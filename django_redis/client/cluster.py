from collections.abc import Iterable, Iterator
from typing import TYPE_CHECKING, Any, Optional

from django.core.cache.backends.base import get_key_func
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from django_redis.client.default import DefaultClient, _main_exceptions
from django_redis.exceptions import ConnectionInterrupted

if TYPE_CHECKING:
    from redis import Redis
    from redis.typing import KeyT

try:
    from redis.cluster import RedisCluster  # noqa: TC002

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

    def iter_keys(
        self,
        search: str,
        itersize: Optional[int] = None,
        client=None,
        version: Optional[int] = None,
    ) -> Iterator[str]:
        """
        Cluster-aware implementation of `iter_keys`.
        It runs `SCAN` on all primary nodes and yields keys that match the pattern.
        """
        if client is None:
            client = self.get_client(write=False)

        pattern = self.make_pattern(search, version=version)

        try:
            # client.get_primaries() is available in redis-py 4.4.0+
            # client.get_nodes("primary") or client.masters() in older versions.
            try:
                primary_nodes = client.get_primaries()
            except AttributeError:
                primary_nodes = client.get_nodes("primary")


            for node in primary_nodes:
                # Run scan_iter on each node.
                # This ensures we only scan keys from the specified node.
                node_keys_iter = client.scan_iter(
                    match=pattern, count=itersize, target_nodes=[node],
                )
                for key in node_keys_iter:
                    yield self.reverse_key(key.decode())
        except _main_exceptions as e:
            raise ConnectionInterrupted(connection=client) from e

    def keys(
        self,
        search: str,
        version: Optional[int] = None,
        client=None,
    ) -> list[Any]:
        """
        Cluster-aware `keys` implementation.
        This is a convenience wrapper around `iter_keys`.
        """
        return list(self.iter_keys(search, version=version, client=client))

    def delete_pattern(
        self,
        pattern: str,
        version: Optional[int] = None,
        prefix: Optional[str] = None,
        client=None,
        itersize: Optional[int] = None,
    ) -> int:
        """
        Cluster-aware implementation to delete keys matching a pattern.
        It scans all primary nodes for keys and then deletes them.
        """
        if client is None:
            client = self.get_client(write=True)

        full_pattern = self.make_pattern(pattern, version=version, prefix=prefix)
        count = 0

        try:
            # 1. Scan all primary nodes for keys matching the pattern.
            keys_to_delete = []

            try:
                primary_nodes = client.get_primaries()
            except AttributeError:
                primary_nodes = client.get_nodes("primary")

            for node in primary_nodes:
                # client.scan_iter returns raw keys (bytes).
                node_keys_iter = client.scan_iter(
                    match=full_pattern, count=itersize, target_nodes=[node]
                )
                keys_to_delete.extend(node_keys_iter)

            # 2. Remove the found keys.
            if keys_to_delete:
                # RedisCluster.delete supports deleting keys across multiple nodes.
                count = client.delete(*keys_to_delete)

            return count
        except _main_exceptions as e:
            raise ConnectionInterrupted(connection=client) from e

    def delete(
        self,
        key: "KeyT",
        version: Optional[int] = None,
        prefix: Optional[str] = None,
        client=None,
    ) -> int:
        """
        Deletes a single key. The parent implementation is sufficient as
        `redis-py`'s cluster client handles routing for single-key operations.
        This override is here for clarity and to ensure the correct client is used.
        """
        if client is None:
            client = self.get_client(write=True)

        return super().delete(key, version=version, prefix=prefix, client=client)

    def delete_many(
        self,
        keys: Iterable["KeyT"],
        version: Optional[int] = None,
        client=None,
    ) -> int:
        """
        Deletes multiple keys. The parent implementation works correctly
        because the underlying `RedisCluster.delete(*keys)` command is
        cluster-aware and can handle keys across different nodes.
        """
        if client is None:
            client = self.get_client(write=True)

        return super().delete_many(keys, version=version, client=client)

    def clear(self, client=None) -> None:
        """
        Flush all cache keys from all primary nodes in the cluster.
        """
        if client is None:
            client = self.get_client(write=True)

        try:
            # Run `flushdb` on all primary nodes.
            client.flushdb(target_nodes="primaries")
        except _main_exceptions as e:
            raise ConnectionInterrupted(connection=client) from e

    def get_raw_keys(
        self,
        pattern: str = "*",
        itersize: Optional[int] = None,
        client=None,
    ) -> Iterator[bytes]:
        """
        A helper method for tests.
        Scans all primary nodes for raw keys (bytes) matching a pattern.
        This does NOT apply the reverse_key function.
        """
        if client is None:
            client = self.get_client(write=False)

        try:
            try:
                primary_nodes = client.get_primaries()
            except AttributeError:
                primary_nodes = client.get_nodes("primary")

            for node in primary_nodes:
                node_keys_iter = client.scan_iter(
                    match=pattern, count=itersize, target_nodes=[node]
                )
                yield from node_keys_iter
        except _main_exceptions as e:
            raise ConnectionInterrupted(connection=client) from e
