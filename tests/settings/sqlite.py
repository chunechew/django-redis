CACHES = {
    "default_sqlite": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": ["redis://127.0.0.1:6379?db=1", "redis://127.0.0.1:6379?db=1"],
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
    "doesnotexist_sqlite": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:56379?db=1",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
    "sample_sqlite": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379?db=1,redis://127.0.0.1:6379?db=1",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    },
    "with_prefix_sqlite": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379?db=1",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "test-prefix",
    },
}
