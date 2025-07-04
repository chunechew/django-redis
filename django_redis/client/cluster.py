from typing import TYPE_CHECKING, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.core.cache.backends.base import get_key_func
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from redis.cluster import ClusterNode

from django_redis.client.default import DefaultClient

if TYPE_CHECKING:
    from redis import Redis

try:
    from django_redis.pool import ClusterConnectionFactory
except ImportError as err:
    error_message = (
        "`ClusterClient` requires the `redis` package "
        "with Redis Cluster support. "
        "Please install `django-redis[cluster]` or `redis>=6.2.0`."
    )
    raise ImproperlyConfigured(error_message) from err


class ClusterClient(DefaultClient):
    """
    A `django-redis` client compatible with `redis.cluster.RedisCluster`.
    (the base class would instead use the value of the `DJANGO_REDIS_CONNECTION_FACTORY`
    setting, but we don't care about that setting here)

    For non-clustered Redis, `django-redis`'s `ConnectionFactory` does some management
    of connection pools shared between client instances.
    The cluster client in `redis-py` doesn't accept a connection pool from outside,
    they're managed internally. To support that, we won't be caching connection pools
    and passing them into clients, we will instead be caching client instances.

    https://github.com/jazzband/django-redis/issues/606#issuecomment-1505615249
    https://gist.github.com/jonprindiville/f97084ca8f91501c17175a7b7a9578af
    """

    def __init__(self, server, params, backend, **kwargs) -> None:
        self._backend = backend
        self._server = server
        self._params = params
        self._options = params.get("OPTIONS", {})

        self.reverse_key = get_key_func(
            params.get("REVERSE_KEY_FUNCTION")
            or "django_redis.util.default_reverse_key",
        )

        if not self._server:
            self.get_server(self._options)

        if not isinstance(self._server, (list, tuple, set)):
            self._server = self._server.split(",")

        self._clients: list[Optional[Redis]] = [None] * len(self._server)
        self._replica_read_only = self._options.get("REPLICA_READ_ONLY", True)

        serializer_path = self._options.get(
            "SERIALIZER",
            "django_redis.serializers.pickle.PickleSerializer",
        )
        serializer_cls = import_string(serializer_path)

        compressor_path = self._options.get(
            "COMPRESSOR",
            "django_redis.compressors.identity.IdentityCompressor",
        )
        compressor_cls = import_string(compressor_path)

        self._serializer = serializer_cls(options=self._options)
        self._compressor = compressor_cls(options=self._options)

        self.connection_factory = ClusterConnectionFactory(
            options=self._options,
        )

    def get_server(self, options):
        redis_client_kwargs = options.get("REDIS_CLIENT_KWARGS", {})

        if "cluster_nodes" not in redis_client_kwargs:
            error_message = (
                "Missing connections string or 'cluster_nodes' "
                "in REDIS_CLIENT_KWARGS. "
                "Please provide a list of cluster nodes."
            )
            raise ImproperlyConfigured(error_message)

        cluster_nodes = redis_client_kwargs["cluster_nodes"]

        if isinstance(cluster_nodes, (list, tuple)):
            nodes = cluster_nodes
        elif isinstance(cluster_nodes, str):
            nodes = cluster_nodes.split(",")
        elif isinstance(cluster_nodes, ClusterNode):
            nodes = [cluster_nodes]

        self._server = self.parse_url(options, nodes)

        if len(self._server) == 0:
            error_message = (
                "No valid cluster nodes provided in REDIS_CLIENT_KWARGS."
            )
            raise ImproperlyConfigured(error_message)

    def parse_url(self, options, nodes):
        _server = []
        for node in nodes:
            if isinstance(node, ClusterNode):
                host = node.host
                port = node.port
                username = options.get("username", "")
                password = options.get("password", "")
                ssl = options.get("ssl", False)
                protocol = "rediss" if ssl else "redis"
                url_str = f"{host}:{port}"
                if username or password:
                    url_str = f"{username}:{password}@{url_str}"
                url_str = f"{protocol}://{url_str}"
                url = urlparse(url_str)
            elif isinstance(node, str):
                url = urlparse(node)
            else:
                continue
            query_params = parse_qs(url.query)
            if "is_master" in query_params:
                del query_params["is_master"]
            new_query = urlencode(query_params, doseq=True)
            new_url = urlunparse(
                (
                    url.scheme,
                    url.netloc,
                    url.path,
                    url.params,
                    new_query,
                    url.fragment,
                ),
            )
            _server.append(new_url)
        return _server
