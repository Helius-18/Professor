from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Connection(Base):
    """
    `connections` table

    Columns:
    - id: primary key
    - connection_type: 'DB' or 'API' (not null)
    - server_name: nullable
    - user_name: nullable
    - password: nullable
    - endpoint: nullable (URL as string)
    - request_type: nullable, one of 'GET', 'POST', 'PUT', 'DELETE'
    - payload: nullable, request body/payload
    """

    __tablename__ = "connections"

    id: Mapped[int] = mapped_column("connection_id", Integer, primary_key=True, autoincrement=True)

    connection_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    server_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    endpoint: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    request_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    payload: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tools: Mapped[list["Tool"]] = relationship(
        back_populates="connection",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Only 'DB' or 'API' allowed for connection_type
        CheckConstraint(
            "connection_type IN ('DB', 'API')",
            name="ck_connections_connection_type",
        ),
        # If request_type is not null, it must be one of the allowed HTTP verbs
        CheckConstraint(
            "request_type IS NULL OR request_type IN ('GET', 'POST', 'PUT', 'DELETE')",
            name="ck_connections_request_type",
        ),
    )


class Tool(Base):
    """
    `tools` table

    Columns:
    - id: primary key
    - tool_name: string (not null)
    - tool_type: 'DB' or 'API' (not null)
    - connection_id: foreign key to connections.connection_id
    - content: string (nullable)
    """

    __tablename__ = "tools"

    id: Mapped[int] = mapped_column("tool_id", Integer, primary_key=True, autoincrement=True)

    tool_name: Mapped[str] = mapped_column(String(255), nullable=False)

    tool_type: Mapped[str] = mapped_column(String(10), nullable=False)

    connection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("connections.connection_id", ondelete="CASCADE"),
        nullable=False,
    )

    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    connection: Mapped[Connection] = relationship(back_populates="tools")

    __table_args__ = (
        CheckConstraint(
            "tool_type IN ('DB', 'API')",
            name="ck_tools_tool_type",
        ),
    )


def get_engine(db_url: str = "sqlite:///app.db"):
    """
    Create and return a SQLAlchemy engine pointing to the SQLite database.
    """
    return create_engine(db_url, echo=False, future=True)


def init_db(db_url: str = "sqlite:///app.db") -> None:
    """
    Initialize the database and create all tables.
    """
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)


def get_session(db_url: str = "sqlite:///app.db") -> Session:
    """
    Convenience helper to get a new Session.
    """
    engine = get_engine(db_url)
    return Session(engine)


if __name__ == "__main__":
    # Create tables when run as a script
    init_db()
    print("Database initialized and tables created.")


