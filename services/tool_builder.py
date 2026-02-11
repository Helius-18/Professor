"""Dynamic tool builder that constructs agno-compatible tools from DB records.

This module queries the `connections` and `tools` tables and builds callable
tools that the agno Agent can use. It supports both API and DB connection types.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Callable, List, Optional

import requests
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, text as sql_text

from models.connections import Connection, ConnectionType, RequestType, SessionLocal
from models.tools import Tool, ToolType
from typing import Generator

logger = logging.getLogger(__name__)


class ToolBuilder:
    """Dynamically build agno-compatible tools from database records."""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize with optional DB session (creates one if not provided)."""
        self.db = db_session or SessionLocal()
        self._tools: List[Callable] = []

    def build_api_tool(self, tool: Tool, connection: Connection) -> Optional[Callable]:
        """Build an HTTP-based tool from an API connection.

        Returns a callable that makes HTTP requests using the stored endpoint,
        request type, and payload template from the connection.
        """
        if not connection.auth_url and not tool.api_endpoint:
            logger.warning(f"Tool {tool.name} has no endpoint; skipping.")
            return None

        auth_url = connection.auth_url
        api_endpoint = tool.api_endpoint
        method = (connection.request_type.value if connection.request_type else "GET").upper()


        access_token = None
        if auth_url:
            try:
                if method in ("POST"):
                    auth_resp = requests.post(auth_url, json=connection.payload, timeout=30)
                else:
                    auth_resp = requests.get(auth_url, params=connection.payload, timeout=30)
                auth_resp.raise_for_status()
                auth_data = auth_resp.json()
                try:
                    access_token = auth_data.get("access_token",auth_data)
                except Exception as exc:
                    access_token = auth_data
            except Exception as exc:
                logger.error(f"Authentication failed for tool {tool.name}: {exc}")
                return None

        def api_tool_fn(
            input_data: Optional[dict] = None,
            **kwargs: Any,
        ) -> dict:
            """Execute an API call based on the tool's connection config.

            Args:
                input_data: Optional dict to merge with the stored payload template.
                **kwargs: Additional arguments.

            Returns:
                Response as dict (parsed JSON or text).
            """
            payload = tool.content or {}
            if input_data:
                payload = {**payload, **input_data}

            # Build headers with Bearer token if available
            headers = {}
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"

            try:
                api_method = tool.api_method.value if tool.api_method else "GET"
                if api_method in ("POST", "PUT"):
                    resp = requests.request(
                        api_method,
                        api_endpoint,
                        json=payload,
                        headers=headers,
                        timeout=30,
                    )
                elif api_method == "DELETE":
                    resp = requests.delete(api_endpoint, headers=headers, timeout=30)
                else:  # GET
                    resp = requests.get(api_endpoint, params=payload, headers=headers, timeout=30)

                resp.raise_for_status()
                return {"status": "success", "data": resp.json() if resp.text else None}

            except Exception as exc:
                logger.error(f"Tool {tool.name} failed: {exc}")
                return {"status": "error", "message": str(exc)}

        # Attach metadata
        api_tool_fn.__name__ = tool.name
        api_tool_fn.__doc__ = (
            f"API tool for {tool.name}. "
            f"Endpoint: {api_endpoint} | Method: {method} | Content: {tool.content or 'N/A'}"
        )

        return api_tool_fn

    def build_db_tool(self, tool: Tool, connection: Connection) -> Optional[Callable]:
        """Build a database query tool from a DB connection.

        Note: For security, actual DB tool execution should be sandboxed and
        carefully controlled. This is a placeholder showing the pattern.
        """
        if not connection.servername:
            logger.warning(f"Tool {tool.name} has no servername; skipping.")
            return None

        content = tool.content or "SELECT 1;"
        user = connection.username
        password = connection.password
        server = connection.servername
        DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{server}:5432/professor"
        engine = create_engine(DATABASE_URL, future=True, echo=False, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        def get_db() -> Generator[Session, None, None]:
            """Yield a database session and ensure it's closed.

            Use within dependency injection or try/finally blocks.
            """
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()
    
        def db_tool_fn(query: Optional[str] = None, **kwargs: Any) -> dict:
            """Execute a database query (with caution!).

            Args:
                query: Optional SQL query to override the stored content.
                **kwargs: Additional arguments.

            Returns:
                Query result as dict with status and data.
            """
            exec_query = query or content
            logger.info(f"DB Tool {tool.name} executing: {exec_query}")
            
            # Get the session from the generator (next() unpacks it)
            db = next(get_db())
            try:
                # Wrap raw SQL string in text() for SQLAlchemy 2.0
                result = db.execute(sql_text(exec_query))
                try:
                    rows = [dict(row._mapping) for row in result]
                except Exception:
                    # Non-SELECT queries won't have rows to map
                    rows = {"rowcount": result.rowcount}
                
                return {"status": "success", "data": rows}
            except Exception as exc:
                logger.error(f"DB Tool {tool.name} failed: {exc}")
                return {"status": "error", "message": str(exc)}
            finally:
                db.close()

        db_tool_fn.__name__ = tool.name
        db_tool_fn.__doc__ = (
            f"Database tool for {tool.name}. "
            f"Server: {connection.servername} | Default query: {content[:100]}"
        )

        return db_tool_fn

    def load_tools_from_db(self) -> List[Callable]:
        """Query DB and build all registered tools.

        Returns:
            List of callable tool functions ready for agno Agent.
        """
        try:
            tools_records = self.db.query(Tool).all()
            logger.info(f"Found {len(tools_records)} tools in database.")

            for tool_record in tools_records:
                connection = self.db.query(Connection).filter_by(id=tool_record.connection_id).first()
                if not connection:
                    logger.warning(f"Tool {tool_record.name} has no connection; skipping.")
                    continue

                tool_fn = None
                if tool_record.tool_type == ToolType.API:
                    tool_fn = self.build_api_tool(tool_record, connection)
                elif tool_record.tool_type == ToolType.DB:
                    tool_fn = self.build_db_tool(tool_record, connection)

                if tool_fn:
                    self._tools.append(tool_fn)
                    logger.info(f"Loaded tool: {tool_record.name} (type={tool_record.tool_type})")

        except Exception as exc:
            logger.error(f"Error loading tools from DB: {exc}")

        return self._tools

    def get_tools(self) -> List[Callable]:
        """Return the currently loaded tools."""
        return self._tools

    def close(self) -> None:
        """Close the DB session."""
        if self.db:
            self.db.close()

    def __enter__(self) -> ToolBuilder:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()


def create_tools_for_agent(db_session: Optional[Session] = None) -> List[Callable]:
    """Convenience function to build and return tools for the agno Agent.

    Usage:
        tools = create_tools_for_agent()
        agent = Agent(tools=tools, ...)
    """
    with ToolBuilder(db_session) as builder:
        return builder.load_tools_from_db()


__all__ = ["ToolBuilder", "create_tools_for_agent"]
