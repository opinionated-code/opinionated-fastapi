import importlib
import logging
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import declared_attr, registry, sessionmaker

from opinionated.fastapi.config import settings

logger = logging.getLogger(__name__)


args = {
    # fixme: add more database options
}
if settings.DATABASE_URL.startswith("sqlite://"):
    # Special setting for sqlite only
    args["check_same_thread"] = False

engine: Engine = create_engine(
    settings.DATABASE_URL,
    future=True,
    connect_args=args,
)
Session: sessionmaker = sessionmaker(bind=engine, autoflush=False, future=True)

Registry = registry()


class BaseModel(metaclass=DeclarativeMeta):
    """Base abstract model we use to create all other models"""

    __abstract__ = True
    __name__: str
    id: Any

    # Generate table name automatically using the __name__ (lower case)
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    registry = Registry
    metadata = Registry.metadata
