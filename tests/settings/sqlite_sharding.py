CACHES = {
    "default_sharding": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": ["redis://127.0.0.1:6379?db=9", "redis://127.0.0.1:6379?db=10"],
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.ShardClient"},
    },
    "doesnotexist_sharding": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": ["redis://127.0.0.1:56379?db=9", "redis://127.0.0.1:56379?db=10"],
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.ShardClient"},
    },
    "sample_sharding": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379?db=9,redis://127.0.0.1:6379?db=9",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.ShardClient"},
    },
    "with_prefix_sharding": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379?db=9",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.ShardClient"},
        "KEY_PREFIX": "test-prefix",
    },
}
