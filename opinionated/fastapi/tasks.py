import logging
import os
from typing import List, Optional

import dramatiq
from dramatiq import Broker, Middleware, set_broker
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.brokers.redis import RedisBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.middleware import (
    AgeLimit,
    Prometheus,
    Retries,
    ShutdownNotifications,
    TimeLimit,
)

# from dramatiq.results import Results


logger = logging.getLogger(__name__)


def create_broker(
    broker_type: str, url: Optional[str], middleware: List[Middleware]
) -> Broker:
    if broker_type == "stub":
        return StubBroker(middleware=middleware)
    if url is None:
        raise RuntimeError("Must set WORKER_BROKER_URL")
    if broker_type == "redis":
        return RedisBroker(url=url, middleware=middleware)
    elif broker_type == "rabbitmq":
        return RabbitmqBroker(url=url, middleware=middleware)


def init_broker(reload=False):
    # Import locally to avoid circular imports
    from .config import settings

    logger.info("Loading async task broker")
    middleware = [
        # max time waiting in queue (one day)
        AgeLimit(max_age=3600000),
        Retries(max_retries=10, min_backoff=15000, max_backoff=604800000),
        ShutdownNotifications(notify_shutdown=True),
        # max task execution time (10min)
        TimeLimit(time_limit=600000, interval=1000),
        # fixme: dramatiq uses env vars for prometheus; maybe write our own using settings?
        Prometheus(),
        # fixme: i doubt we'll use results; anything that requires a result should prob be
        #  run using fastapi async BackgroundTask, but keep it here to keep our options open
        # Results(),
    ]

    set_broker(
        create_broker(
            settings.WORKER_BROKER_TYPE, settings.WORKER_BROKER_URL, middleware
        )
    )


def setup_dramatiq():
    """Called by dramatiq worker. Do NOT run this function from anywhere else"""

    os.environ.setdefault("FASTAPI_CONFIG_MODULE", "server.config")
    os.environ.setdefault("FASTAPI_SETTINGS", "Development")

    from .bootstrap import setup

    # The main thing this module needs to do is load the tasks modules - setup() will achieve
    # that, so that's all we really need to do.
    setup()

    from dramatiq import get_broker

    broker = get_broker()
    actors = broker.get_declared_actors()
    logger.info("Dramatiq worker loaded: %d actors registered.", len(actors))
    for actor in actors:
        actor_obj = broker.get_actor(actor)
        logger.debug(
            " - Actor registered: [%s] %s", actor_obj.queue_name, actor_obj.actor_name
        )
