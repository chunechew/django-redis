CACHES = {
    "default_lz4": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": ["redis://127.0.0.1:6379?db=5", "redis://127.0.0.1:6379?db=5"],
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.lz4.Lz4Compressor",
        },
    },
    "doesnotexist_lz4": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:56379?db=5",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.lz4.Lz4Compressor",
        },
    },
    "sample_lz4": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379?db=5,redis://127.0.0.1:6379?db=5",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.lz4.Lz4Compressor",
        },
    },
    "with_prefix_lz4": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379?db=5",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "COMPRESSOR": "django_redis.compressors.lz4.Lz4Compressor",
        },
        "KEY_PREFIX": "test-prefix",
    },
}
