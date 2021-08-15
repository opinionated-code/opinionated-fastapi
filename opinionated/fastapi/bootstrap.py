"""
bootstrap

The setup() function sets up the FastAPI environment and loads configuration values, etc.
It only executes once - if run a second time, it will just return without doing anything.

We have a bunch of things we do for any of our processes, whether it be a webserver, CLI, dramatiq worker, etc.
The most important thing we do is instantiate the correct settings object based on environment variables.
Then we set up the ORM, the task broker, and so on.
"""
import importlib
import logging
import logging.config
import os
import sys
from types import ModuleType
from typing import List, Optional, Protocol, cast

from fastapi import APIRouter, FastAPI

from .config import init_config, settings
from .default_settings import DEFAULT_LOGGING
from .sentry import init_sentry, setup_sentry_middleware
from .tasks import init_broker

logger = logging.getLogger(__name__)


initialized = False


def load_modules(
    apps: List[str], mod_name: Optional[str] = None, mods: Optional[List[str]] = None
) -> List[ModuleType]:
    """Generic function to load modules from apps and dedicated config paths"""
    res: List[ModuleType] = []
    for app in apps:
        full_path = f"{app}.{mod_name}" if mod_name is not None else app
        try:
            logger.debug("Importing: %s", full_path)
            res.append(importlib.import_module(full_path))
        except ImportError as exc:
            # Ignore missing modules in apps; it just means the app doesn't use it
            # fixme eventually replace this debug with more targeted warnings (or pass)
            logger.debug("ImportError loading %s: %r", full_path, exc)
    if mods is not None:
        for mod in mods:
            logger.debug("Importing: %s", mod)
            # No protection; if there's an error, crash and burn and let the user know
            res.append(importlib.import_module(mod))

    return res


def load_apps() -> None:
    # Load the package for each app, allowing the app to do some initialization if it needs to
    load_modules(settings.APPS)


def load_models() -> None:
    logger.info("Loading database models")
    # Find the models and load them.
    load_modules(settings.APPS, "models", settings.MODELS)


def load_tasks() -> None:
    logger.info("Loading async task modules")
    # Find the models and load them.
    load_modules(settings.APPS, "tasks", settings.TASKS)


def load_commands() -> None:
    """During bootstrap, load all command modules specified in the settings, or autodiscover them"""

    logger.info("Loading command modules")

    # Find the models and load them.
    load_modules(settings.APPS, "commands", settings.COMMANDS)


class ControllerModule(Protocol):
    router: Optional[APIRouter]


def load_controllers() -> List[APIRouter]:
    logger.info("Loading API endpoint controller modules")
    routers: List[APIRouter] = []
    # Find the modules and load them.
    controllers = load_modules(settings.APPS, "controllers", settings.CONTROLLERS)
    for controller in controllers:
        router: Optional[APIRouter] = getattr(
            cast(ControllerModule, controller), "router", None
        )
        if router is not None:
            routers.append(router)

    # Return the routers, for when we need to add them to the FastAPI app.
    return routers


def setup():
    """Set up the FastAPI environment"""

    global initialized

    if sys.version_info[0] != 3 or sys.version_info[1] not in {8, 9, 10}:
        logger.warning(
            "Python version %s is not supported by opinionated.fastapi, and may not work correctly.",
            ".".join(str(x) for x in sys.version_info[0:2]),
        )

    os.environ.setdefault(
        "FASTAPI_CONFIG_MODULE", "opinionated.fastapi.default_settings"
    )
    os.environ.setdefault("FASTAPI_SETTINGS", "DefaultSettings")

    if initialized:
        logger.debug("Call to setup() after we were already initialized.")
        return
    # Set up some basic default logging until we've loaded our settings
    logging.config.dictConfig(
        {
            **DEFAULT_LOGGING,
        }
    )
    logger.debug("Running opinionated.fastapi.bootstrap:setup()")
    # Do this early, so we don't accidentally recurse and re-enter ourself
    initialized = True

    # initialize settings
    # - find the right Settings object using environment variables and import and instantiate it
    init_config()

    logging.config.dictConfig({**DEFAULT_LOGGING, **settings.LOGGING})

    # Ordering is significant; sentry must initialize *before* db and dramatiq but *after* config
    # initialize sentry
    # - init the SDK
    init_sentry()

    # Make sure the database is initialized by importing the db
    from .db import Engine as Engine

    if Engine is None:
        raise RuntimeError("Failed to initialize database engine.")

    # - find and import all model modules to ensure models are loaded into the sqlalchemy and alembic lists
    load_models()

    # initialize dramatiq tasks
    # - init the global broker
    init_broker()
    # - find and import all tasks modules to ensure tasks are loaded into the actors list
    load_tasks()

    # find and import any command modules
    load_commands()

    # We don't use them here, but load the controllers, which makes sure they're ready and without obvious errors
    load_controllers()


class OpinionatedFastAPI(FastAPI):
    def __init__(self, *args, **kwargs):
        setup()

        kwargs.setdefault("openapi_url", f"{settings.BASE_URL_PREFIX}/openapi.json")
        kwargs.setdefault("title", settings.SERVER_TITLE)
        kwargs.setdefault("debug", settings.DEBUG)

        super().__init__(*args, **kwargs)

        # Add the sentry ASGI middleware
        setup_sentry_middleware(self)

        api_router = APIRouter()
        for router in load_controllers():
            api_router.include_router(router)
        self.include_router(api_router, prefix=settings.BASE_URL_PREFIX)
