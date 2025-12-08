# dynamic_tools.py
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List
from inspect import Signature, Parameter

from models import get_session, Tool, Connection 
from tool_executor import DBExecutor, APIExecutor 


def _parse_content(tool: Tool) -> Dict[str, Any]:
    """
    Parse the JSON spec stored in Tool.content.
    """
    if not tool.content:
        return {}
    try:
        return json.loads(tool.content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in Tool.content for tool '{tool.tool_name}': {exc}"
        ) from exc


def _build_param_signature(params_spec: Dict[str, Dict[str, Any]]) -> Signature:
    """
    Build a dynamic function signature from the 'params' spec in the JSON content.

    Each param entry looks like:
    {
      "param_name": {
         "type": "string" | "integer" | "number" | "boolean",
         "description": "..."
      }
    }
    """
    parameters: List[Parameter] = []

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

        param = Parameter(
            name=name,
            kind=Parameter.POSITIONAL_OR_KEYWORD,
            annotation=annotation,
            default=Parameter.empty,  # required
        )
        parameters.append(param)

    return Signature(parameters)


def _create_db_tool_callable(
    tool_row: Tool,
    conn: Connection,
    spec: Dict[str, Any],
    description: str,
    params_spec: Dict[str, Dict[str, Any]],
) -> Callable:
    """
    Create a callable for a DB tool using DBExecutor.
    """
    sql = spec.get("sql")
    if not sql:
        raise ValueError(f"DB tool '{tool_row.tool_name}' is missing 'sql' in content")

    executor = DBExecutor(conn)
    signature = _build_param_signature(params_spec)

    def _impl(**kwargs):
        """
        Execute the SQL query using the provided parameters and return rows as list[dict].
        """
        return executor.run(sql, kwargs)

    _impl.__name__ = tool_row.tool_name
    _impl.__doc__ = description
    _impl.__signature__ = signature  # type: ignore[attr-defined]

    return _impl


def _create_api_tool_callable(
    tool_row: Tool,
    conn: Connection,
    spec: Dict[str, Any],
    description: str,
    params_spec: Dict[str, Dict[str, Any]],
) -> Callable:
    """
    Create a callable for an API tool using APIExecutor.
    """
    relative_endpoint = spec.get("relative_endpoint")  # may be None
    method = spec.get("method") or conn.request_type or "GET"
    payload_template = spec.get("payload")

    executor = APIExecutor(conn)
    signature = _build_param_signature(params_spec)

    def _impl(**kwargs):
        """
        Execute the API call and return the JSON/text result.
        """
        return executor.run(relative_endpoint, method, payload_template, kwargs)

    _impl.__name__ = tool_row.tool_name
    _impl.__doc__ = description
    _impl.__signature__ = signature  # type: ignore[attr-defined]

    return _impl


def load_dynamic_tools(db_url: str = "sqlite:///app.db") -> List[Callable]:
    """
    Load all `Tool` rows from the DB and return a list of Python callables
    that can be passed to LangGraph.
    """
    session = get_session(db_url)
    tools: List[Tool] = session.query(Tool).join(Connection).all()

    tool_funcs: List[Callable] = []

    for tool in tools:
        spec = _parse_content(tool)
        description = spec.get("description", f"Dynamically generated tool {tool.tool_name}")
        params_spec: Dict[str, Dict[str, Any]] = spec.get("params", {})

        conn: Connection = tool.connection

        if tool.tool_type == "DB":
            func = _create_db_tool_callable(tool, conn, spec, description, params_spec)
            tool_funcs.append(func)
        elif tool.tool_type == "API":
            func = _create_api_tool_callable(tool, conn, spec, description, params_spec)
            tool_funcs.append(func)
        else:
            # Unknown tool type, skip
            continue

    session.close()
    return tool_funcs
