from __future__ import annotations

from typing import Any, Dict, Optional, Literal

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from models import get_engine, get_session, Tool, Connection

import httpx

app = FastAPI()


class ExecuteRequest(BaseModel):
    params: Optional[Dict[str, Any]] = None
    payload: Optional[Any] = None
    override_method: Optional[str] = None
    headers: Optional[Dict[str, str]] = None



class ConnectionCreate(BaseModel):
    connection_type: Literal["DB", "API"]
    server_name: Optional[str] = None
    user_name: Optional[str] = None
    password: Optional[str] = None
    endpoint: Optional[str] = None
    request_type: Optional[Literal["GET", "POST", "PUT", "DELETE"]]
    payload: Optional[Any] = None


class ToolCreate(BaseModel):
    tool_name: str
    tool_type: Literal["DB", "API"]
    connection_id: int
    content: Optional[str] = None


def resolve_db_url(connection: Connection) -> str:
    # If server_name is set, treat it as a SQLAlchemy DB URL. Otherwise default to app.db
    return connection.server_name or "sqlite:///app.db"


@app.get("/tools")
def list_tools():
    session = get_session()
    try:
        tools = session.query(Tool).all()
        return [
            {
                "id": t.id,
                "tool_name": t.tool_name,
                "tool_type": t.tool_type,
                "connection_id": t.connection_id,
                "content": t.content,
            }
            for t in tools
        ]
    finally:
        session.close()



@app.post("/connections", status_code=201)
def create_connection(conn: ConnectionCreate):
    session = get_session()
    try:
        connection = Connection(
            connection_type=conn.connection_type,
            server_name=conn.server_name,
            user_name=conn.user_name,
            password=conn.password,
            endpoint=conn.endpoint,
            request_type=conn.request_type,
            payload=conn.payload,
        )
        session.add(connection)
        session.commit()
        session.refresh(connection)
        return {
            "id": connection.id,
            "connection_type": connection.connection_type,
            "server_name": connection.server_name,
            "endpoint": connection.endpoint,
        }
    finally:
        session.close()


@app.get("/connections")
def get_connections():
    session = get_session()
    try:
        conns = session.query(Connection).all()
        return [
            {
                "id": c.id,
                "connection_type": c.connection_type,
                "server_name": c.server_name,
                "endpoint": c.endpoint,
            }
            for c in conns
        ]
    finally:
        session.close()


@app.post("/tools", status_code=201)
def create_tool(tool: ToolCreate):
    session = get_session()
    try:
        # ensure connection exists
        conn = session.get(Connection, tool.connection_id)
        if not conn:
            raise HTTPException(status_code=404, detail="Connection not found")

        t = Tool(
            tool_name=tool.tool_name,
            tool_type=tool.tool_type,
            connection_id=tool.connection_id,
            content=tool.content,
        )
        session.add(t)
        session.commit()
        session.refresh(t)
        return {
            "id": t.id,
            "tool_name": t.tool_name,
            "tool_type": t.tool_type,
            "connection_id": t.connection_id,
        }
    finally:
        session.close()


@app.get("/mcp/tools")
def mcp_tools(request: Request):
    """Expose tools in a simple MCP-friendly format so an agent can register them dynamically.

    Each tool includes an `execute_url` that points back to this server's `/tools/{id}/execute`.
    """
    session = get_session()
    try:
        tools = session.query(Tool).all()
        base = str(request.base_url).rstrip("/")
        result = []
        for t in tools:
            execute_url = f"{base}/tools/{t.id}/execute"
            result.append(
                {
                    "id": t.id,
                    "name": t.tool_name,
                    "type": t.tool_type,
                    "execute_url": execute_url,
                    "method": "POST",
                    "description": (t.content or "")[:200],
                }
            )
        return result
    finally:
        session.close()


@app.get("/tools/{tool_id}")
def get_tool(tool_id: int):
    session = get_session()
    try:
        tool = session.get(Tool, tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")
        return {
            "id": tool.id,
            "tool_name": tool.tool_name,
            "tool_type": tool.tool_type,
            "connection_id": tool.connection_id,
            "content": tool.content,
        }
    finally:
        session.close()


@app.post("/tools/{tool_id}/execute")
def execute_tool(tool_id: int, req: ExecuteRequest):
    session = get_session()
    try:
        tool = session.get(Tool, tool_id)
        if not tool:
            raise HTTPException(status_code=404, detail="Tool not found")

        connection = tool.connection
        if not connection:
            raise HTTPException(status_code=500, detail="Connection for tool missing")

        if tool.tool_type == "DB":
            db_url = resolve_db_url(connection)
            engine = create_engine(db_url, future=True)
            sql = (tool.content or "").strip()
            if not sql:
                raise HTTPException(status_code=400, detail="No SQL content for DB tool")

            try:
                with engine.connect() as conn:
                    # Use SQLAlchemy text and params mapping for basic parameterization
                    result = conn.execute(text(sql), req.params or {})
                    # If the statement returns rows, fetch them
                    try:
                        rows = result.mappings().all()
                        return {"status": "ok", "rows": [dict(r) for r in rows]}
                    except Exception:
                        # No rows (e.g., UPDATE/INSERT)
                        return {"status": "ok", "rowcount": result.rowcount}
            except SQLAlchemyError as e:
                raise HTTPException(status_code=500, detail=f"DB error: {e}")

        elif tool.tool_type == "API":
            method = (req.override_method or connection.request_type or "GET").upper()
            base = (connection.endpoint or "").rstrip("/")
            path = (tool.content or "").lstrip("/")
            if base and path:
                url = f"{base}/{path}"
            else:
                url = base or path

            if not url:
                raise HTTPException(status_code=400, detail="No URL to call for API tool")

            try:
                # Use httpx for HTTP calls
                with httpx.Client(timeout=30.0) as client:
                    req_kwargs = {}
                    if req.headers:
                        req_kwargs["headers"] = req.headers
                    # prefer explicit request payload then connection payload
                    body = req.payload if req.payload is not None else connection.payload
                    if body is not None:
                        req_kwargs["json"] = body

                    resp = client.request(method, url, **req_kwargs)
                    # attempt to parse JSON, fallback to text
                    try:
                        content = resp.json()
                    except Exception:
                        content = resp.text

                    return {"status_code": resp.status_code, "content": content}
            except httpx.HTTPError as e:
                raise HTTPException(status_code=500, detail=f"HTTP error: {e}")

        else:
            raise HTTPException(status_code=400, detail="Unknown tool_type")
    finally:
        session.close()


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
