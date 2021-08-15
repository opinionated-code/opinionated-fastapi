"""
commands

Library functions to handle the "manage.py" fastapi commands.
"""
import importlib
import logging
import subprocess
import sys
from functools import partial
from typing import List, Protocol, cast

import typer
from fastapi import FastAPI

from .config import settings

logger = logging.getLogger(__name__)
cli = typer.Typer()


try:
    # Ordering matters; run import and setup() before running cli()
    from opinionated.fastapi.bootstrap import setup

    setup()
except ImportError as exc:
    print(
        f"We can't import the modules we need. Did you forget to activate the virtualenv?\n{exc}",
        file=sys.stderr,
        flush=True,
    )
    sys.exit(1)


@cli.command()
def develop(
    hostname: str = typer.Option(settings.SERVER_HOST),
    port: int = typer.Option(settings.SERVER_PORT),
    reload: bool = typer.Option(settings.SERVER_RELOAD),
):
    try:
        from uvicorn.main import run

        # FIXME: possibly add reload-dirs option to set which dirs to watch for reloading
        # FIXME: add logging config for uvicorn
        run(
            f"{settings.APP_MODULE}:app",
            proxy_headers=settings.SERVER_PROXY_HEADERS,
            host=hostname,
            port=port,
            reload=reload,
            log_level="info",
        )
    except ImportError:
        typer.echo("Failed to run server - uvicorn is not installed.", err=True)
        raise typer.Exit(1)


class FastApiAppProtocol(Protocol):
    app: FastAPI


@cli.command()
def runserver():
    try:
        from gunicorn.app.base import BaseApplication
    except ImportError:
        typer.echo("Failed to run server - gunicorn is not installed.", err=True)
        raise typer.Exit(1)

    try:
        from uvicorn.workers import UvicornWorker
    except ImportError:
        typer.echo("Failed to run server - uvicorn is not installed.", err=True)
        raise typer.Exit(1)

    try:
        # If no app module set, use the default one
        app = cast(FastApiAppProtocol, importlib.import_module(settings.APP_MODULE)).app

        class FastApiApp(BaseApplication):
            def init(self, parser, opts, args):
                pass

            def load_config(self):
                # fixme: set some sane defaults and provide some command line arguments here
                self.cfg.set("worker_class", "uvicorn.workers.UvicornWorker")

            def load(self):
                return app

        FastApiApp().run()
    except ImportError:
        typer.echo(
            f"Failed to run server - could not find app '{settings.APP_MODULE}'",
            err=True,
        )
        raise typer.Exit(1)


@cli.command()
def runworker(
    hostname: str = typer.Option(settings.SERVER_HOST),
    processes: int = typer.Option(settings.WORKER_PROCESSES),
    reload: bool = typer.Option(settings.WORKER_RELOAD),
):
    # Only consume 'default' queue normally, because we don't want to get scheduler events
    queues = settings.WORKER_QUEUES
    # Note; we don't need to load all the modules that have dramatiq actors in them.
    # Insteead, the opinionated.fastapi.dramatiq_setup module will ensure setuo() is run,
    #  which will load all .tasks modules as part of that process.
    cmd = [
        "dramatiq",
        "opinionated.fastapi.tasks:setup_dramatiq",
        "--path",
        ".",
        "--processes",
        str(processes),
        "-Q",
        *queues,
    ]
    if reload:
        cmd += ["--watch", "."]

    # fixme: do we need to double check that environ variables are passed through?
    ret = subprocess.call(cmd)
    if ret != 0:
        raise typer.Exit(ret)


@cli.command()
def runscheduler():
    from .scheduler import run_scheduler

    # fixme: make an option on runworker to add --scheduler, and run this as an extra thread/process.
    run_scheduler()


@cli.command()
def checktypes():
    from mypy import api

    # Run mypy
    stdout, stderr, res = api.run([])

    typer.echo(stdout)
    typer.echo(stderr, err=True)
    if res != 0:
        raise typer.Exit(res)


@cli.command("format")
def cmd_format(args: List[str]):
    # Run black
    cmd = ["black", *args]

    ret = subprocess.call(cmd)
    if ret != 0:
        raise typer.Exit(ret)


@cli.command()
def test():
    # Run pytest
    pass


@cli.command()
def audit():
    # Check for security issues in packages
    pass


@cli.command()
def update():
    # fixme run poetry and check for newer versions of packages, update as much as we can
    # fixme include "--major" option for updating even for new major versions
    # fixme include "--dryrun" option for just checking without actually updating
    pass


@cli.command()
def generate():
    # Scaffold - subcommand with multiple child commands:
    #  - model
    #  - schema
    #  - service
    #  - task
    #  - endpoint
    #  - query
    #  - mutation
    #  - command
    pass


@cli.command()
def shell():
    # Load everything, import models etc, and start a python REPL shell
    # fixme: make sure everything (models, etc) is imported when the shell loads
    try:
        from bpython import embed as shell
    except ImportError:
        try:
            from IPython import start_ipython

            shell = partial(start_ipython, argv=[])
        except ImportError:
            from code import interact as shell

    shell()


@cli.command()
def dbshell():
    # Start the appropriate database CLI shell for the db type we're using, if its installed.
    pass


@cli.command()
def backups():
    # Subcommand (backups create, backups list, backups restore, backups remove)
    pass
