import sys
from collections.abc import Iterable
from pathlib import Path
from typing import cast

import pytest
from django.utils.connection import ConnectionProxy
from xdist.scheduler import LoadScopeScheduling

from django_redis.cache import BaseCache, RedisCache
from tests.settings_wrapper import CacheHandler, SettingsWrapper


class FixtureScheduling(LoadScopeScheduling):
    """Split by [] value. This is very hackish and might blow up any time!"""

    def _split_scope(self, nodeid):
        if "[sqlite" in nodeid:
            return nodeid.rsplit("[")[-1].replace("]", "")
        return None


def pytest_xdist_make_scheduler(log, config):
    return FixtureScheduling(config, log)


def pytest_configure(config):
    sys.path.insert(0, str(Path(__file__).absolute().parent))


@pytest.fixture()
def base(env_name):
    from os import environ

    from django import setup

    environ["DJANGO_SETTINGS_MODULE"] = (
        "settings.django_config"
        if env_name != "sqlite"
        else "settings.django_config_sqlite"
    )

    setup()

    # from tests.settings_wrapper import CacheHandler

    default_name = f"default_{env_name}"

    wrapper = SettingsWrapper()
    wrapper.__setattr__("SESSION_CACHE_ALIAS", default_name)

    if env_name == "herd":
        wrapper.__setattr__("CACHE_HERD_TIMEOUT", 2)
    else:
        wrapper.__delattr__("CACHE_HERD_TIMEOUT")

    # wrapper.finalize()
    # wrapper = SettingsWrapper()

    # from django.core.cache import caches
    from django.core import cache

    # cache.caches = None
    # cache.caches = CacheHandler()

    default_cache = ConnectionProxy(cache.caches, default_name)
    # default_cache = cast("RedisCache", caches[default_name])
    cache.cache = default_cache

    yield wrapper, cache.caches, default_cache
    # default_cache.clear()
    # default_cache.close()


@pytest.fixture()
def settings(base):
    """A Django settings object which restores changes after the testrun"""
    yield base[0]
    base[0].finalize()


@pytest.fixture()
def caches(base) -> Iterable[CacheHandler]:
    yield base[1]


@pytest.fixture()
def cache(base) -> Iterable[BaseCache]:
    yield base[2]
    base[2].clear()


@pytest.fixture()
def suffix(env_name) -> Iterable[str]:
    yield f"_{env_name}"


def pytest_generate_tests(metafunc):
    # import sys

    # sys.setrecursionlimit(100)

    # from os import environ

    # from django import setup

    # environ["DJANGO_SETTINGS_MODULE"] = "settings.django_config"

    # setup()

    if "base" in metafunc.fixturenames or "suffix" in metafunc.fixturenames:
        # Mark
        env_names = [
            "sqlite",
            # "cluster",
            "gzip",
            "herd",
            "json",
            "lz4",
            "msgpack",
            "sentinel",
            "sentinel_opts",
            "sharding",
            "usock",
            "zlib",
            "zstd",
        ]
        metafunc.parametrize("env_name", env_names)
