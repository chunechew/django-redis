CACHES = {
    "default_HERD": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": ["redis://127.0.0.1:6379?db=3"],
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.HerdClient"},
    },
    "doesnotexist_HERD": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:56379?db=3",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.HerdClient"},
    },
    "sample_HERD": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379?db=3,redis://127.0.0.1:6379?db=3",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.HerdClient"},
    },
    "with_prefix_HERD": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379?db=3",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.HerdClient"},
        "KEY_PREFIX": "test-prefix",
    },
}
