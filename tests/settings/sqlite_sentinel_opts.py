SENTINELS = [("127.0.0.1", 26379)]

conn_factory = "django_redis.pool.SentinelConnectionFactory"

CACHES = {
    "default_SENTINEL_OPTS": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": ["redis://default_service?db=8"],
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SENTINELS": SENTINELS,
            "CONNECTION_FACTORY": conn_factory,
        },
    },
    "doesnotexist": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://missing_service?db=8",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SENTINELS": SENTINELS,
            "CONNECTION_FACTORY": conn_factory,
        },
    },
    "sample_SENTINEL_OPTS": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://default_service?db=8",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.SentinelClient",
            "SENTINELS": SENTINELS,
            "CONNECTION_FACTORY": conn_factory,
        },
    },
    "with_prefix_SENTINEL_OPTS": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://default_service?db=8",
        "KEY_PREFIX": "test-prefix",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SENTINELS": SENTINELS,
            "CONNECTION_FACTORY": conn_factory,
        },
    },
}
