import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)


def init_sentry():
    """Initialize sentry on application startup"""
    from .config import settings

    if settings.SENTRY_DSN is not None and len(settings.SENTRY_DSN) > 0:
        logger.info("Initializing Sentry")

        import sentry_sdk
        from sentry_dramatiq import DramatiqIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            release=settings.SENTRY_RELEASE,
            sample_rate=settings.SENTRY_SAMPLE_RATE,
            send_default_pii=settings.SENTRY_SEND_PII,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[
                # fixme write an integration for fastapi to add any other useful data to our events
                #  (in particular, set transaction name based on route endpoint, add instrumentation, etc)
                SqlalchemyIntegration(),
                DramatiqIntegration(),
            ],
        )


def setup_sentry_middleware(app: FastAPI) -> FastAPI:
    """Add sentry middleware to FastAPI application"""

    from .config import settings

    if settings.SENTRY_DSN is not None and len(settings.SENTRY_DSN) > 0:
        logger.debug("Loading Sentry ASGI Middleware")
        from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

        app.add_middleware(SentryAsgiMiddleware)

    return app
