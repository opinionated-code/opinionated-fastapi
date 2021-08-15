"""A package built on top of FastAPI to provide some highly opinionated features.

This package provides some additional tools and a layer of abstraction on top of
FastAPI, with some highly opinionated features.

For most cases, opinionated.fastapi provides only one way of solving a thing -
the ORM is SQLAlchemy, the error tracking platform is Sentry, the ASGI server
is Uvicorn. The aim is to provide a "batteries included" solution.

This software is licensed under the [MIT License](license.md).

Copyright (c) 2021 Daniel Sloan, Lucid Horizons Pty Ltd

::: opinionated.fastapi.app
    selection:
      filters:

"""

from .bootstrap import OpinionatedFastAPI, setup
from .config import settings
from .default_settings import DefaultSettings

__all__ = ["setup", "OpinionatedFastAPI", "DefaultSettings", "settings"]
