"""Tools model for database ORM."""
from __future__ import annotations

import enum

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from models.connections import Base
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

class ToolType(enum.Enum):
    API = "API"
    DB = "DB"

class ApiMethod(enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tool_type = Column(
        SQLEnum(ToolType, name="tool_type_enum", native_enum=False), nullable=False
    )
    api_endpoint = Column(String(2048), nullable=True)
    api_method = Column(SQLEnum(ApiMethod), nullable=False, default=ApiMethod.GET)
    connection_id = Column(Integer, ForeignKey("connections.id"), nullable=False)
    content = Column(Text, nullable=True)

    # Relationship to Connection model
    connection = relationship("Connection", backref="tools")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Tool id={self.id} name={self.name} type={self.tool_type} "
            f"connection_id={self.connection_id}>"
        )


__all__ = ["Tool", "ToolType"]
