from tests.settings.sqlite import CACHES as SQLITE_CACHES
from tests.settings.sqlite_cluster import CACHES as CLUSTER_CACHES
from tests.settings.sqlite_gzip import CACHES as GZIP_CACHES
from tests.settings.sqlite_herd import CACHES as HERD_CACHES
from tests.settings.sqlite_json import CACHES as JSON_CACHES
from tests.settings.sqlite_lz4 import CACHES as LZ4_CACHES
from tests.settings.sqlite_msgpack import CACHES as MSGPACK_CACHES
from tests.settings.sqlite_sentinel import CACHES as SENTINEL_CACHES
from tests.settings.sqlite_sentinel_opts import CACHES as SENTINEL_OPTS_CACHES
from tests.settings.sqlite_sharding import CACHES as SHARDING_CACHES
from tests.settings.sqlite_usock import CACHES as USOCK_CACHES
from tests.settings.sqlite_zlib import CACHES as ZLIB_CACHES
from tests.settings.sqlite_zstd import CACHES as ZSTD_CACHES

SECRET_KEY = "django_tests_secret_key"

CACHES = {}
CACHES.update(SQLITE_CACHES)
CACHES.update(CLUSTER_CACHES)
CACHES.update(GZIP_CACHES)
CACHES.update(HERD_CACHES)
CACHES.update(JSON_CACHES)
CACHES.update(LZ4_CACHES)
CACHES.update(MSGPACK_CACHES)
CACHES.update(SENTINEL_CACHES)
CACHES.update(SENTINEL_OPTS_CACHES)
CACHES.update(SHARDING_CACHES)
CACHES.update(USOCK_CACHES)
CACHES.update(ZLIB_CACHES)
CACHES.update(ZSTD_CACHES)

USE_TZ = False
