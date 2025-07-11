from redis.cluster import ClusterNode

SECRET_KEY = "django_tests_secret_key"

conn_client = "django_redis.client.ClusterClient"
conn_factory = "django_redis.pool.ClusterConnectionFactory"
conn_client_class = "redis.cluster.RedisCluster"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        # "LOCATION": "redis://127.0.0.1:6380",
        "OPTIONS": {
            "CLIENT_CLASS": conn_client,
            "CONNECTION_FACTORY": conn_factory,
            "REDIS_CLIENT_CLASS": conn_client_class,
            "REDIS_CLIENT_KWARGS": {
                "cluster_nodes": [
                    ClusterNode(host="127.0.0.1", port=6380),
                    ClusterNode(host="127.0.0.1", port=6381),
                    ClusterNode(host="127.0.0.1", port=6382),
                ],
            },
        },
    },
    # "doesnotexist": {
    #     "BACKEND": "django_redis.cache.RedisCache",
    #     # "LOCATION": "redis://missing_service:6380",
    #     "OPTIONS": {
    #         "CLIENT_CLASS": conn_client,
    #         "CONNECTION_FACTORY": conn_factory,
    #         "REDIS_CLIENT_CLASS": conn_client_class,
    #         "REDIS_CLIENT_KWARGS": {
    #             "cluster_nodes": [
    #                 ClusterNode(host="127.0.0.1", port=56380),
    #                 ClusterNode(host="127.0.0.1", port=56381),
    #                 ClusterNode(host="127.0.0.1", port=56382),
    #             ],
    #         },
    #     },
    # },
    "sample": {
        "BACKEND": "django_redis.cache.RedisCache",
        # "LOCATION": "redis://127.0.0.1:6380",
        "OPTIONS": {
            "CLIENT_CLASS": conn_client,
            "CONNECTION_FACTORY": conn_factory,
            "REDIS_CLIENT_CLASS": conn_client_class,
            "REDIS_CLIENT_KWARGS": {
                "cluster_nodes": [
                    ClusterNode(host="127.0.0.1", port=6380),
                    ClusterNode(host="127.0.0.1", port=6381),
                    ClusterNode(host="127.0.0.1", port=6382),
                ],
            },
        },
    },
    "with_prefix": {
        "BACKEND": "django_redis.cache.RedisCache",
        # "LOCATION": "redis://127.0.0.1:6380",
        "KEY_PREFIX": "test-prefix",
        "OPTIONS": {
            "CLIENT_CLASS": conn_client,
            "CONNECTION_FACTORY": conn_factory,
            "REDIS_CLIENT_CLASS": conn_client_class,
            "REDIS_CLIENT_KWARGS": {
                "cluster_nodes": [
                    ClusterNode(host="127.0.0.1", port=6380),
                    ClusterNode(host="127.0.0.1", port=6381),
                    ClusterNode(host="127.0.0.1", port=6382),
                ],
            },
        },
    },
}

INSTALLED_APPS = ["django.contrib.sessions"]

USE_TZ = False
