"""Database connection utilities and `Connection` model.

This module provides SQLAlchemy engine/session/Base and the
`Connection` model requested (connection type, servername, username,
password, endpoint, request type, payload, response).
"""
from __future__ import annotations

import enum
import os
from typing import Generator

from sqlalchemy import (
	JSON,
	Column,
	Integer,
	String,
	Text,
	create_engine,
	Enum as SQLEnum,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from db_manager import Base
# Read DB URL from env; fallback to a sensible local Postgres URL
DATABASE_URL = os.getenv(
	"DATABASE_URL",
	"postgresql+psycopg2://postgres:Ajay123@localhost:5432/professor",
)

# Create engine with recommended SQLAlchemy 2.0 settings
engine = create_engine(DATABASE_URL, future=True, echo=False, pool_pre_ping=True)

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)



class ConnectionType(enum.Enum):
	DB = "DB"
	API = "API"


class RequestType(enum.Enum):
	POST = "POST"
	GET = "GET"
	PUT = "PUT"
	DELETE = "DELETE"


class Connection(Base):
	__tablename__ = "connections"

	id = Column(Integer, primary_key=True, index=True)
	connection_type = Column(
		SQLEnum(ConnectionType, name="connection_type_enum", native_enum=False), nullable=False
	)
	servername = Column(String(255), nullable=True)
	username = Column(String(255), nullable=True)
	password = Column(String(255), nullable=True)
	auth_url = Column(String(2048), nullable=True)

	request_type = Column(
		SQLEnum(RequestType, name="request_type_enum", native_enum=False), nullable=True
	)
	payload = Column(JSON, nullable=True)

	def __repr__(self) -> str:  # pragma: no cover - simple helper
		return (
			f"<Connection id={self.id} type={self.connection_type} server={self.servername}"
			f" auth_url={self.auth_url} request={self.request_type}>"
		)


def get_db() -> Generator[Session, None, None]:
	"""Yield a database session and ensure it's closed.

	Use within dependency injection or try/finally blocks.
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


__all__ = [
	"engine",
	"SessionLocal",
	"Base",
	"get_db",
	"init_db",
	"DATABASE_URL",
	"Connection",
	"ConnectionType",
	"RequestType",
]
