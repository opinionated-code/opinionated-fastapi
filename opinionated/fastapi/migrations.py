import logging
import os
from pathlib import Path

from alembic.script import write_hooks

logger = logging.getLogger(__name__)


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    from alembic import context

    from .config import settings
    from .db import Registry

    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=Registry.metadata,
        literal_binds=True,
        # dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    from alembic import context

    from .db import Registry, engine

    def process_revision_directives(context, revision, directives):
        if context.config.cmd_opts.autogenerate:
            script = directives[0]
            if script.upgrade_ops.is_empty():
                print("No changes to database, not creating any new migration")
                directives[:] = []

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Registry.metadata,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


def load_alembic():
    # Order matters - these must be run BEFORE setup()
    os.environ.setdefault("FASTAPI_CONFIG_MODULE", "server.config")
    os.environ.setdefault("FASTAPI_SETTINGS", "Development")
    from .bootstrap import setup

    setup()


def run_alembic_migrations():
    from alembic import context

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


@write_hooks.register("black")
def code_format(filename, options):
    from black import Mode, Report, WriteBack, reformat_one

    report = Report()
    # Note: this bypasses black config, which is maybe not ideal. Possibly we should just subprocess.call() black...
    reformat_one(
        src=Path(filename),
        write_back=WriteBack.YES,
        fast=False,
        mode=Mode(),
        report=report,
    )
    logger.info(str(report))
