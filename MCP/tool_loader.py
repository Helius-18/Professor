# mcp_server/dynamic_tool_loader.py
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from fastmcp import FastMCP

from models import Tool, Connection, get_session
from tool_executor import DBExecutor, APIExecutor


def _parse_content(tool: Tool) -> Dict[str, Any]:
    if not tool.content:
        return {}
    try:
        return json.loads(tool.content)
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in Tool.content for tool '{tool.tool_name}'")


def register_dynamic_tools(mcp: FastMCP, db_url: str = "sqlite:///app.db") -> None:
    """
    Load all Tool rows from DB and register them as FastMCP tools.
    """

    session = get_session(db_url)
    tools: List[Tool] = session.query(Tool).join(Connection).all()

    for tool in tools:
        spec = _parse_content(tool)
        description = spec.get("description", f"Dynamically generated tool {tool.tool_name}")
        params_spec: Dict[str, Dict[str, Any]] = spec.get("params", {})

        connection: Connection = tool.connection

        if tool.tool_type == "DB":
            _register_db_tool(mcp, tool, connection, spec, description, params_spec)
        elif tool.tool_type == "API":
            _register_api_tool(mcp, tool, connection, spec, description, params_spec)
        else:
            # Ignore unknown tool types
            continue

    session.close()


def _build_param_signature(params_spec: Dict[str, Dict[str, Any]]):
    """
    Build a typed function signature dynamically.
    To keep it simple, we'll map everything to str | int | float based on `type` field.
    """
    from inspect import Signature, Parameter

    parameters = []
    for name, meta in params_spec.items():
        typ = meta.get("type", "string")
        if typ == "integer":
            annotation = int
        elif typ == "number":
            annotation = float
        elif typ == "boolean":
            annotation = bool
        else:
            annotation = str

        # Optional vs required can be extended here
        param = Parameter(
            name=name,
            kind=Parameter.POSITIONAL_OR_KEYWORD,
            annotation=annotation,
            default=Parameter.empty,
        )
        parameters.append(param)

    return Signature(parameters)


def _register_db_tool(
    mcp: FastMCP,
    tool_row: Tool,
    conn: Connection,
    spec: Dict[str, Any],
    description: str,
    params_spec: Dict[str, Dict[str, Any]],
) -> None:
    sql = spec.get("sql")
    if not sql:
        raise ValueError(f"DB tool '{tool_row.tool_name}' is missing 'sql' in content")

    executor = DBExecutor(conn)
    signature = _build_param_signature(params_spec)

    # We’ll construct a closure that uses **kwargs; FastMCP uses annotations for schema.
    def _impl(**kwargs):
        return executor.run(sql, kwargs)

    _impl.__name__ = tool_row.tool_name
    _impl.__doc__ = description
    _impl.__signature__ = signature  # type: ignore[attr-defined]

    mcp.tool(name=tool_row.tool_name, description=description)(_impl)


def _register_api_tool(
    mcp: FastMCP,
    tool_row: Tool,
    conn: Connection,
    spec: Dict[str, Any],
    description: str,
    params_spec: Dict[str, Dict[str, Any]],
) -> None:
    relative_endpoint = spec.get("relative_endpoint")  # may be None
    method = spec.get("method") or conn.request_type or "GET"
    payload_template = spec.get("payload")

    executor = APIExecutor(conn)
    signature = _build_param_signature(params_spec)

    def _impl(**kwargs):
        return executor.run(relative_endpoint, method, payload_template, kwargs)

    _impl.__name__ = tool_row.tool_name
    _impl.__doc__ = description
    _impl.__signature__ = signature  # type: ignore[attr-defined]

    mcp.tool(name=tool_row.tool_name, description=description)(_impl)
