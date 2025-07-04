import copy
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
def ignore_exceptions_cache(settings, env_name: str) -> RedisCache:
    caches_setting = copy.deepcopy(settings.CACHES)
    key_name = f"doesnotexist_{env_name}"
    caches_setting[key_name]["OPTIONS"]["IGNORE_EXCEPTIONS"] = True
    caches_setting[key_name]["OPTIONS"]["LOG_IGNORED_EXCEPTIONS"] = True
    settings.CACHES = caches_setting
    settings.DJANGO_REDIS_IGNORE_EXCEPTIONS = True
    settings.DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True
    return cast("RedisCache", caches[key_name])


def test_get_django_omit_exceptions_many_returns_default_arg(
    ignore_exceptions_cache: RedisCache,
):
    assert ignore_exceptions_cache._ignore_exceptions is True
    assert ignore_exceptions_cache.get_many(["key1", "key2", "key3"]) == {}


def test_get_django_omit_exceptions(
    caplog: LogCaptureFixture,
    ignore_exceptions_cache: RedisCache,
    env_name: str,
):
    assert ignore_exceptions_cache._ignore_exceptions is True
    assert ignore_exceptions_cache._log_ignored_exceptions is True

    assert ignore_exceptions_cache.get("key") is None
    default_key = f"default_{env_name}"
    assert ignore_exceptions_cache.get("key", default_key) == default_key
    assert ignore_exceptions_cache.get("key", default=default_key) == default_key

    assert len(caplog.records) == 3
    assert all(
        record.levelname == "ERROR" and record.msg == "Exception ignored"
        for record in caplog.records
    )


def test_get_django_omit_exceptions_priority_1(settings, env_name: str):
    caches_setting = copy.deepcopy(settings.CACHES)
    key_name = f"doesnotexist_{env_name}"
    caches_setting[key_name]["OPTIONS"]["IGNORE_EXCEPTIONS"] = True
    settings.CACHES = caches_setting
    settings.DJANGO_REDIS_IGNORE_EXCEPTIONS = False
    cache = cast("RedisCache", caches[key_name])
    assert cache._ignore_exceptions is True
    assert cache.get("key") is None


def test_get_django_omit_exceptions_priority_2(settings, env_name: str):
    caches_setting = copy.deepcopy(settings.CACHES)
    key_name = f"doesnotexist_{env_name}"
    caches_setting[key_name]["OPTIONS"]["IGNORE_EXCEPTIONS"] = False
    settings.CACHES = caches_setting
    settings.DJANGO_REDIS_IGNORE_EXCEPTIONS = True
    cache = cast("RedisCache", caches[key_name])
    assert cache._ignore_exceptions is False
    with pytest.raises(RedisConnectionError):
        cache.get("key")


@pytest.fixture
def key_prefix_cache(
        cache: RedisCache,
        settings,
        env_name: str,
    ) -> Iterable[RedisCache]:
    caches_setting = copy.deepcopy(settings.CACHES)
    caches_setting[f"default_{env_name}"]["KEY_PREFIX"] = "*"
    settings.CACHES = caches_setting
    yield cache


@pytest.fixture
def with_prefix_cache(env_name: str) -> Iterable[RedisCache]:
    with_prefix = cast("RedisCache", caches[f"with_prefix_{env_name}"])
    yield with_prefix
    with_prefix.clear()


class TestDjangoRedisCacheEscapePrefix:
    def test_delete_pattern(
        self,
        key_prefix_cache: RedisCache,
        with_prefix_cache: RedisCache,
    ):
        key_prefix_cache.set("a", "1")
        with_prefix_cache.set("b", "2")
        key_prefix_cache.delete_pattern("*")
        assert key_prefix_cache.has_key("a") is False
        assert with_prefix_cache.get("b") == "2"

    def test_iter_keys(
        self,
        key_prefix_cache: RedisCache,
        with_prefix_cache: RedisCache,
    ):
        if isinstance(key_prefix_cache.client, ShardClient):
            pytest.skip("ShardClient doesn't support iter_keys")

        key_prefix_cache.set("a", "1")
        with_prefix_cache.set("b", "2")
        assert list(key_prefix_cache.iter_keys("*")) == ["a"]

    def test_keys(self, key_prefix_cache: RedisCache, with_prefix_cache: RedisCache):
        key_prefix_cache.set("a", "1")
        with_prefix_cache.set("b", "2")
        keys = key_prefix_cache.keys("*")
        assert "a" in keys
        assert "b" not in keys


def test_custom_key_function(cache: RedisCache, settings, env_name: str):
    caches_setting = copy.deepcopy(settings.CACHES)
    default_key = f"default_{env_name}"
    caches_setting[default_key]["KEY_FUNCTION"] = "test_cache_options.make_key"
    caches_setting[default_key]["REVERSE_KEY_FUNCTION"] = (
        "test_cache_options.reverse_key"
    )
    settings.CACHES = caches_setting

    if isinstance(cache.client, ShardClient):
        pytest.skip("ShardClient doesn't support get_client")

    for key in ["foo-aa", "foo-ab", "foo-bb", "foo-bc"]:
        cache.set(key, "foo")

    res = cache.delete_pattern("*foo-a*")
    assert bool(res) is True

    keys = cache.keys("foo*")
    assert set(keys) == {"foo-bb", "foo-bc"}
    # ensure our custom function was actually called
    assert {k.decode() for k in cache.client.get_client(write=False).keys("*")} == (
        {"#1#foo-bc", "#1#foo-bb"}
    )
