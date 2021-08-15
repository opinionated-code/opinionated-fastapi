from typing import Any, Dict, List, Literal, Optional, TypedDict

from pydantic import AnyUrl, BaseSettings, HttpUrl, validator

DEFAULT_LOGGING: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "detailed": {
            "class": "logging.Formatter",
            "format": "%(asctime)s %(name)-35s %(levelname)-8s %(processName)-10s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "detailed",
        },
    },
    "loggers": {
        "alembic": {
            "level": "INFO",
        },
        "sqlalchemy": {
            "level": "WARN",
        },
        "opinionated": {
            "level": "DEBUG",
            "propagate": True,
        },
    },
    "root": {
        "handlers": [
            "console",
        ],
        "level": "DEBUG",
    },
}


class DefaultSettings(BaseSettings):
    """Default settings for FastAPI application"""

    # Redefine for a custom app initialization - most of the time should not be required, unless you want to add
    #  some custom ASGI middleware or something.
    APP_MODULE = "opinionated.fastapi.app"

    # Watch for changes and reload
    SERVER_RELOAD = True

    # Serve on hostname and port
    SERVER_HOST = "127.0.0.1"
    SERVER_PORT = 5000

    # Show remote IP etc using Forwarded-for headers, etc (this means you trust the proxy server)
    SERVER_PROXY_HEADERS = False

    # Sentry - if None or an empty string, disable sentry integration completely.
    SENTRY_DSN: Optional[HttpUrl] = None

    @validator("SENTRY_DSN", pre=True)
    def sentry_dsn_can_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is None or len(v) == 0:
            return None
        return v

    SENTRY_ENVIRONMENT = "development"
    SENTRY_RELEASE: Optional[str] = None
    SENTRY_SAMPLE_RATE = 1.0
    SENTRY_SEND_PII = False
    SENTRY_TRACES_SAMPLE_RATE = 1.0

    # Database URL - can be sqlite://, postgres://, postgis://, or mysql://
    DATABASE_URL = "sqlite:///./db.sqlite"

    # Watch for changes and reload worker
    WORKER_RELOAD = True
    WORKER_PROCESSES = 2
    WORKER_QUEUES: List[str] = ["default"]
    WORKER_BROKER_TYPE: Literal["redis", "stub", "rabbitmq"] = "stub"
    WORKER_BROKER_URL: Optional[AnyUrl] = None

    @validator("WORKER_BROKER_URL")
    def url_must_be_set_for_non_stub(
        cls, v: Optional[str], values: Dict[str, Any], **kwargs
    ) -> Optional[str]:
        if values["WORKER_BROKER_TYPE"] in {"redis", "rabbitmq"} and (
            v is None or len(v) == 0
        ):
            raise ValueError(
                "WORKER_BROKER_URL must be set for redis or rabbitmq brokers"
            )
        return v

    BASE_URL_PREFIX: str = ""
    SERVER_TITLE: str = "FastAPI Server"
    DEBUG: bool = False

    # The apps we are loading (apps being just a python package,
    #  that contains some or all of .tasks, .models, .commands, .controllers)
    APPS: List[str] = []
    # In addition we can specify specific tasks, models, commands, and controllers modules, with or without apps
    MODELS: List[str] = []
    TASKS: List[str] = []
    COMMANDS: List[str] = []
    CONTROLLERS: List[str] = []

    LOGGING: Dict[str, Any] = {}

    class Config:
        case_sensitive = True
        env_prefix = "FASTAPI_"
