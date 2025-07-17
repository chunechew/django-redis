from collections.abc import Iterable
from typing import cast

import pytest
from django.core.cache import caches
from pytest import LogCaptureFixture
from redis.exceptions import ConnectionError as RedisConnectionError

from django_redis.cache import RedisCache
from django_redis.client import ShardClient


def make_key(key: str, prefix: str, version: str) -> str:
    return f"{prefix}#{version}#{key}"


def reverse_key(key: str) -> str:
    return key.split("#", 2)[2]


@pytest.fixture
def ignore_exceptions_cache(cache, settings) -> RedisCache:
    caches_setting = settings.CACHES
    if "doesnotexist" not in caches_setting:
        return cache
    caches_setting["doesnotexist"]["OPTIONS"]["IGNORE_EXCEPTIONS"] = True
    caches_setting["doesnotexist"]["OPTIONS"]["LOG_IGNORED_EXCEPTIONS"] = True
    settings.CACHES = caches_setting
    settings.DJANGO_REDIS_IGNORE_EXCEPTIONS = True
    settings.DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True
    return cast("RedisCache", caches["doesnotexist"])

# ClusterClient can't the four tests with invalid connection below
# because it requires a valid node connection.

def test_get_django_omit_exceptions_many_returns_default_arg(
    ignore_exceptions_cache: RedisCache,
):
    try:
        from django_redis.client import ClusterClient

        if isinstance(ignore_exceptions_cache.client, ClusterClient):
            pytest.skip("ClusterClient doesn't support doesnotexist cache")
    except ImportError:
        pass
    assert ignore_exceptions_cache._ignore_exceptions is True
    assert ignore_exceptions_cache.get_many(["key1", "key2", "key3"]) == {}


def test_get_django_omit_exceptions(
    caplog: LogCaptureFixture,
    ignore_exceptions_cache: RedisCache,
):
    try:
        from django_redis.client import ClusterClient

        if isinstance(ignore_exceptions_cache.client, ClusterClient):
            pytest.skip("ClusterClient doesn't support doesnotexist cache")
    except ImportError:
        pass
    assert ignore_exceptions_cache._ignore_exceptions is True
    assert ignore_exceptions_cache._log_ignored_exceptions is True

    assert ignore_exceptions_cache.get("key") is None
    assert ignore_exceptions_cache.get("key", "default") == "default"
    assert ignore_exceptions_cache.get("key", default="default") == "default"

    assert len(caplog.records) == 3
    assert all(
        record.levelname == "ERROR" and record.msg == "Exception ignored"
        for record in caplog.records
    )


def test_get_django_omit_exceptions_priority_1(cache, settings):
    try:
        from django_redis.client import ClusterClient

        if isinstance(cache.client, ClusterClient):
            pytest.skip("ClusterClient doesn't support doesnotexist cache")
    except ImportError:
        pass
    caches_setting = settings.CACHES
    caches_setting["doesnotexist"]["OPTIONS"]["IGNORE_EXCEPTIONS"] = True
    settings.CACHES = caches_setting
    settings.DJANGO_REDIS_IGNORE_EXCEPTIONS = False
    _cache = cast("RedisCache", caches["doesnotexist"])
    assert _cache._ignore_exceptions is True
    assert _cache.get("key") is None


def test_get_django_omit_exceptions_priority_2(cache, settings):
    try:
        from django_redis.client import ClusterClient

        if isinstance(cache.client, ClusterClient):
            pytest.skip("ClusterClient doesn't support doesnotexist cache")
    except ImportError:
        pass
    caches_setting = settings.CACHES
    caches_setting["doesnotexist"]["OPTIONS"]["IGNORE_EXCEPTIONS"] = False
    settings.CACHES = caches_setting
    settings.DJANGO_REDIS_IGNORE_EXCEPTIONS = True
    _cache = cast("RedisCache", caches["doesnotexist"])
    assert _cache._ignore_exceptions is False
    with pytest.raises(RedisConnectionError):
        _cache.get("key")


@pytest.fixture
def key_prefix_cache(cache: RedisCache, settings) -> Iterable[RedisCache]:
    caches_setting = settings.CACHES
    caches_setting["default"]["KEY_PREFIX"] = "*"
    settings.CACHES = caches_setting
    yield cache


@pytest.fixture
def with_prefix_cache() -> Iterable[RedisCache]:
    with_prefix = cast("RedisCache", caches["with_prefix"])
    yield with_prefix
    with_prefix.clear()


class TestDjangoRedisCacheEscapePrefix:
    def test_delete_pattern(
        self,
        key_prefix_cache: RedisCache,
        with_prefix_cache: RedisCache,
    ):
        key_prefix_cache.set("{same_slot}_a", "1")
        with_prefix_cache.set("{same_slot}_b", "2")
        key_prefix_cache.delete_pattern("{same_slot}_*")
        assert key_prefix_cache.has_key("{same_slot}_a") is False
        assert with_prefix_cache.get("{same_slot}_b") == "2"

    def test_iter_keys(
        self,
        key_prefix_cache: RedisCache,
        with_prefix_cache: RedisCache,
    ):
        if isinstance(key_prefix_cache.client, ShardClient):
            pytest.skip("ShardClient doesn't support iter_keys")

        key_prefix_cache.set("{same_slot}_a", "1")
        with_prefix_cache.set("{same_slot}_b", "2")
        assert list(key_prefix_cache.iter_keys("{same_slot}_*")) == ["{same_slot}_a"]

    def test_keys(self, key_prefix_cache: RedisCache, with_prefix_cache: RedisCache):
        key_prefix_cache.set("{same_slot}_a", "1")
        with_prefix_cache.set("{same_slot}_b", "2")
        keys = key_prefix_cache.keys("{same_slot}_*")
        assert "{same_slot}_a" in keys
        assert "{same_slot}_b" not in keys


def test_custom_key_function(cache: RedisCache, settings):
    caches_setting = settings.CACHES
    caches_setting["default"]["KEY_FUNCTION"] = "test_cache_options.make_key"
    caches_setting["default"]["REVERSE_KEY_FUNCTION"] = "test_cache_options.reverse_key"
    settings.CACHES = caches_setting

    if isinstance(cache.client, ShardClient):
        pytest.skip("ShardClient doesn't support get_client")

    for key in [
        "{same_slot}_foo-aa",
        "{same_slot}_foo-ab",
        "{same_slot}_foo-bb",
        "{same_slot}_foo-bc",
    ]:
        cache.set(key, "foo")

    res = cache.delete_pattern("*{same_slot}_foo-a*")
    assert bool(res) is True

    keys = cache.keys("{same_slot}_foo*")
    assert set(keys) == {"{same_slot}_foo-bb", "{same_slot}_foo-bc"}

    # ensure our custom function was actually called
    prefix = cache.key_prefix
    version = cache.version
    scan_pattern = f"{prefix}#{version}#*"
    expected_keys = {
        f"{prefix}#{version}#{{same_slot}}_foo-bb",
        f"{prefix}#{version}#{{same_slot}}_foo-bc",
    }

    try:
        from django_redis.client import ClusterClient

        if isinstance(cache.client, ClusterClient):
            raw_keys = {k.decode() for k in cache.client.get_raw_keys(scan_pattern)}
            assert raw_keys == expected_keys
        else:
            raw_keys = {
                k.decode() for k in cache.client.get_client(write=False).keys(scan_pattern)
            }
            assert raw_keys == expected_keys
    except ImportError:
        raw_keys = {
            k.decode() for k in cache.client.get_client(write=False).keys(scan_pattern)
        }
        assert raw_keys == expected_keys
