# mcp_server/server.py
from __future__ import annotations

import os

from fastmcp import FastMCP

from models import init_db
from .tool_loader import register_dynamic_tools


DB_URL = os.getenv("APP_DB_URL", "sqlite:///app.db")

mcp = FastMCP(name="Dynamic DB/API Tool Server")


def init():
    init_db(DB_URL)
    register_dynamic_tools(mcp, db_url=DB_URL)
    print("✅ Dynamic tools registered from DB.")


if __name__ == "__main__":
    init()
    mcp.run(transport="http", host="127.0.0.1", port=8000)
