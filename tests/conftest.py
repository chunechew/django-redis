import sys
from collections.abc import Iterable
from pathlib import Path
from typing import cast

import pytest
from django.conf import settings as django_settings
from xdist.scheduler import LoadScopeScheduling

from django_redis.cache import BaseCache, RedisCache
from tests.settings_wrapper import SettingsWrapper


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
def settings():
    """A Django settings object which restores changes after the testrun"""
    wrapper = SettingsWrapper()
    yield wrapper
    wrapper.finalize()


@pytest.fixture()
def cache(env_name) -> Iterable[BaseCache]:
    wrapper = SettingsWrapper()

    if env_name == "SQLITE":
        # Include `django.contrib.auth` and `django.contrib.contenttypes` for mypy /
        # django-stubs.

        # See:
        # - https://github.com/typeddjango/django-stubs/issues/318
        # - https://github.com/typeddjango/django-stubs/issues/534

        wrapper.__setattr__(
            "INSTALLED_APPS",
            [
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "django.contrib.sessions",
            ],
        )
    else:
       wrapper.__setattr__(
            "INSTALLED_APPS",
            [
                "django.contrib.sessions",
            ],
        )

    if env_name == "SENTINEL":
        wrapper.__setattr__(
            "DJANGO_REDIS_CONNECTION_FACTORY",
            "django_redis.pool.SentinelConnectionFactory",
        )
    elif env_name == "HERD":
        wrapper.__setattr__("CACHE_HERD_TIMEOUT", 2)
    else:
        if hasattr(django_settings, "DJANGO_REDIS_CONNECTION_FACTORY"):
            wrapper.__delattr__("DJANGO_REDIS_CONNECTION_FACTORY")
        if hasattr(django_settings, "CACHE_HERD_TIMEOUT"):
            wrapper.__delattr__("CACHE_HERD_TIMEOUT")

    from django.core.cache import caches
    default_cache = cast("RedisCache", caches[f"default_{env_name}"])

    yield default_cache
    default_cache.clear()

@pytest.fixture()
def env_name(env_name) -> Iterable[str]:
    yield env_name


def pytest_generate_tests(metafunc):
    from os import environ

    from django import setup

    environ["DJANGO_SETTINGS_MODULE"] = "settings.django_config"
    setup()

    if (
        "cache" in metafunc.fixturenames
        or "env_name" in metafunc.fixturenames
        or "session" in metafunc.fixturenames
        or "patch_itersize_setting" in metafunc.fixturenames
    ):
        env_names = [
            "SQLITE",
            "CLUSTER",
            "GZIP",
            "HERD",
            "JSON",
            "LZ4",
            "MSGPACK",
            "SENTINEL",
            "SENTINEL_OPTS",
            "SHARDING",
            "USOCK",
            "ZLIB",
            "ZSTD",
        ]
        metafunc.parametrize("env_name", env_names)

