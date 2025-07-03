from django.core.exceptions import ImproperlyConfigured

from django_redis.client.default import DefaultClient

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

    def __init__(self, server, params, backend) -> None:
        super().__init__(server, params, backend)
        self.connection_factory = ClusterConnectionFactory(
            options=self._options,
        )
