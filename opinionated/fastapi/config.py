"""
config

Utilities for managing FastAPI settings module(s)
"""

import importlib
import logging
import os
from typing import Any, Optional, Type, cast

from .default_settings import DefaultSettings

logger = logging.getLogger(__name__)


class NotReadyError(Exception):
    pass


class SettingsProxy(object):
    """
    When you do 'from config import settings', we need to either have already initialized the value in this module,
    or we need to use a proxy like this one. The proxy allows us to late-load the settings object in init_config().
    We could technically get away with directly assigning settings, but there would be other problems that would create.
    This solution retains the most flexibility.
    """

    _proxy_obj: Optional[DefaultSettings] = None

    def loaded(self) -> bool:
        return object.__getattribute__(self, "_proxy_obj") is not None

    def set_proxy_object(self, obj: Optional[DefaultSettings]) -> None:
        object.__setattr__(self, "_proxy_obj", obj)

    def __delattr__(self, *args) -> None:
        raise RuntimeError("FastAPI settings object is read-only")

    def __setattr__(self, *args) -> None:
        raise RuntimeError("FastAPI settings object is read-only")

    def __getattr__(self, name: str) -> Any:
        """Return attributes from the proxy object if there is one, otherwise raise an error"""

        proxy = object.__getattribute__(self, "_proxy_obj")
        if proxy is not None:
            return getattr(proxy, name)
        else:
            raise NotReadyError(
                "The settings object has not been initialized yet, "
                "did you try to access it before running bootstrap.setup()?"
            )

    def __nonzero__(self):
        return bool(object.__getattribute__(self, "_proxy_obj"))

    def __str__(self):
        if self._proxy_obj is not None:
            return str(object.__getattribute__(self, "_proxy_obj"))
        else:
            return "SettingsProxy (uninitialized)"

    def __repr__(self):
        if self._proxy_obj is not None:
            return repr(object.__getattribute__(self, "_proxy_obj"))
        else:
            return "SettingsProxy (uninitialized)"


# Some typing acrobatics for the sake of mypy
settings_proxy = SettingsProxy()
settings: DefaultSettings = cast(DefaultSettings, settings_proxy)


def init_config() -> None:
    global settings, settings_proxy

    if settings_proxy.loaded():
        logger.debug("Running init_config() after already initialized.")
        # We're already loaded
        return

    config_module = os.environ.get("FASTAPI_CONFIG_MODULE", None)
    setting_name = os.environ.get("FASTAPI_SETTINGS", None)

    if config_module is None:
        raise RuntimeError(
            "The environment variable 'FASTAPI_CONFIG_MODULE' must be set"
        )
    if setting_name is None:
        raise RuntimeError("The environment variable 'FASTAPI_SETTINGS' must be set")

    logger.debug(
        "Initializing configuration for opinionated.fastapi with %s:%s",
        config_module,
        setting_name,
    )

    # Load the config module, if we can.
    try:
        cfg = importlib.import_module(config_module)
    except Exception as exc:
        # fixme get more specific with the error but need to learn more about pydantic behaviour...
        logger.error("Got error in loading config module")
        raise

    # Find the settings class, if we can.
    try:
        settings_cls = cast(Type[DefaultSettings], getattr(cfg, setting_name))
    except AttributeError:
        raise RuntimeError(
            f"Could not find setting '{setting_name}' in '{config_module}'"
        )

    logger.debug("Setting up new settings class '%r' as SettingsProxy.", settings_cls)
    # fixme think about whether we set settings up as a injectable dependency as well ?
    # Instantiate the settings object
    settings_proxy.set_proxy_object(settings_cls())
