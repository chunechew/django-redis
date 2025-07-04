DJANGO_REDIS_CONNECTION_FACTORY = "django_redis.pool.SentinelConnectionFactory"

SENTINELS = [("127.0.0.1", 26379)]

CACHES = {
    "default_SENTINEL": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": ["redis://default_service?db=7"],
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SENTINELS": SENTINELS,
        },
    },
    "doesnotexist_SENTINEL": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://missing_service?db=7",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SENTINELS": SENTINELS,
        },
    },
    "sample_SENTINEL": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://default_service?db=7",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.SentinelClient",
            "SENTINELS": SENTINELS,
        },
    },
    "with_prefix_SENTINEL": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://default_service?db=7",
        "KEY_PREFIX": "test-prefix",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SENTINELS": SENTINELS,
        },
    },
}
