
"""Database connection utilities for SQLAlchemy + PostgreSQL.

Uses the `DATABASE_URL` environment variable. Example:
postgresql+psycopg2://user:password@host:port/dbname
"""
from __future__ import annotations

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Read DB URL from env; fallback to a sensible local Postgres URL
DATABASE_URL = os.getenv(
	"DATABASE_URL",
	"postgresql+psycopg2://postgres:Ajay123@localhost:5432/professor",
)

# Create engine with recommended SQLAlchemy 2.0 settings
engine = create_engine(DATABASE_URL, future=True, echo=False, pool_pre_ping=True)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
	"""Yield a database session and ensure it's closed.

	Use within dependency injection or try/finally blocks:

		with next(get_db()) as db:
			...
	"""
	db = SessionLocal()
	try:
		yield db
	finally:
		db.close()


def init_db() -> None:
	"""Create database tables from models (useful for quick local setup).

	For production migrations, prefer Alembic instead of this function.
	"""
	Base.metadata.create_all(bind=engine)


__all__ = ["engine", "SessionLocal", "Base", "get_db", "init_db", "DATABASE_URL"]
