from typing import TYPE_CHECKING, Optional

from django.core.cache.backends.base import get_key_func
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

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
