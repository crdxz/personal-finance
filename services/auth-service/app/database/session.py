from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_database_url

database_url = get_database_url()
connect_args = (
    {"check_same_thread": False}
    if database_url.startswith("sqlite")
    else {"connect_timeout": 10}
)
engine_options = {"connect_args": connect_args, "pool_pre_ping": True}
if not database_url.startswith("sqlite"):
    engine_options["poolclass"] = NullPool
engine = create_engine(database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
