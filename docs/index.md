# Opinionated FastAPI

This package provides some additional tools and a layer of abstraction on top of the excellent FastAPI, with some highly opinionated features.
For most cases, opinionated.fastapi provides only one way of solving a thing - the ORM is SQLAlchemy, the error tracking
platform is Sentry, the ASGI server is Uvicorn. The aim is to provide a "batteries included" solution, with sensible defaults.

A specific objective is to ensure that the package works well in two types of environments - extremely embedded ones where
the entire application should be able to run in a single process (with child processes for the web, worker, scheduling, etc) and
extremely scalable environments like Docker or Kubernetes, where each child process has its own container and/or pod to run in.

## Features

Here are some key features:

* **Settings**: Pydantic-based settings, with sensible defaults and configured via environment variable or command line (a la Django).
* **Error Reporting**: Built-in Sentry support, including integrations
* **Task Queues**: Asynchronous queued tasks via Dramatiq worker processes
* **Scheduled Tasks**: Scheduled tasks via a custom APScheduler implementation
* **ORM Support**: SQLAlchemy 1.4 (using the 2.0 "future" APIs)
* **ORM Migrations**: Pre-configured Alembic environment to manage migrations
* **Command Line Tool**: A management command (fastapi-admin) that provides access to a variety of processes and actions, and is extensible for custom commands
* **ASGI Web Server**: Pre-configured Uvicorn support
* **Web Process Manager**: Gunicorn support for process management in production
* **Deployment**: Docker and Kubernetes build and deployment tools
* **File Structure**: An opinionated file structure to help simplify understanding of complex projects
* **Embedded Friendly**: The ability to run via a single command, that can spawn child processes as needed.

## Guiding Principles

Here are some guiding principles for this project, that I use to help me decide how I'm going to approach any particular feature/enhancement:

* Be extremely opinionated; FastAPI provides the opposite of this, which is great! But for this project, I specifically want to be absolutely opinionated - i.e. pick one way to solve a problem and only implement that one way. If a better option arises, the existing implementation will be replaced (although ideally encapsulated if that's possible). An example would be using Dramatiq, which I prefer over Celery. Rather than support both, the project only supports Dramatiq, but we coul change in future if a compelling reason arises.
* Focus on Code over Configuration; where possible, we avoid configuration files other than pyproject.toml, and try to do most things in code instead
* Adhere to the principles of 12factor app design (see [https://12factor.net/](https://12factor.net/))

## Requirements

Python 3.8 and 3.9 are supported.
Python 3.6 and 3.7 probably work, but we do not actively support it.

## Installation

```commandline
pip install opinionated-fastapi
```

I encourage the use of virtual environments, in particular I recommend using poetry:

```commandline
poetry init
poetry add opinionated-fastapi
```

## Example

I recommend using the [cookiecutter template](https://github.com/opinionated-code/opinionated-fastapi-cookiecutter/) to get a complete filesystem layout.
Alternatively, assuming you already have a virtualenv set up, a minimal example can be set up as follows:

Create a 'my_app' package, and add a module in the package called 'config.py':
```python

from opinionated.fastapi import DefaultSettings


class Development(DefaultSettings):
    APPS = [ "my_app", ]

```

In the 'my_app' package, create a module 'controllers.py':
```python

from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["auth"])


@router.post("/ping")
def ping():
    return {"detail": "pong"}

```

You can run this minimal example with the develop command:
```commandline
fastapi-admin --config=my_app.config --setting=Development develop
```

Alternatively you can use environment varibales:
```commandline
export FASTAPI_CONFIG_MODULE="my_app.config"
export FASTAPI_SETTING=Development
fastapi-admin develop
```

## Related Projects

Related to this project, there is also a [cookiecutter template](https://github.com/opinionated-code/opinionated-fastapi-cookiecutter/)
which provides a standard project design with features like static analysis, tests, GitHub Actions support, etc.
