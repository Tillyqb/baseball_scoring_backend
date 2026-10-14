import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database import Base

# Set TEST_DATABASE_URL (e.g. a mysql+pymysql:// URL) to run against MySQL; defaults to SQLite.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@pytest.fixture()
def engine():
    if TEST_DATABASE_URL:
        url = make_url(TEST_DATABASE_URL)
        admin = create_engine(url.set(database="mysql"), isolation_level="AUTOCOMMIT")
        with admin.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{url.database}`"))
        admin.dispose()
        eng = create_engine(url)
    else:
        eng = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()
