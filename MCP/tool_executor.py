# mcp_server/executors.py
from __future__ import annotations

import json
from typing import Any, Dict, List

import httpx
from sqlalchemy import create_engine, text

from models import Connection


class DBExecutor:
    """Executes DB tools based on Connection + tool spec."""

    def __init__(self, connection: Connection):
        if not connection.server_name:
            raise ValueError("DB connection.server_name must be a SQLAlchemy URL.")
        self.connection = connection
        self.engine = create_engine(connection.server_name, future=True)

    def run(self, sql: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute parameterized SQL and return list of dict rows."""
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params)
            rows = [dict(row._mapping) for row in result]
        return rows


class APIExecutor:
    """Executes API tools based on Connection + tool spec."""

    def __init__(self, connection: Connection):
        if not connection.endpoint:
            raise ValueError("API connection.endpoint must be set")
        self.connection = connection
        self.base_url = connection.endpoint.rstrip("/")

    def run(
        self,
        relative_endpoint: str | None,
        method: str,
        payload_template: Dict[str, Any] | None,
        args: Dict[str, Any],
    ) -> Any:
        """
        - relative_endpoint: may contain {placeholders}
        - method: GET/POST/PUT/DELETE
        - payload_template: dict with placeholders to be formatted from args
        - args: actual tool arguments
        """
        url = self.base_url
        if relative_endpoint:
            url = f"{self.base_url}/{relative_endpoint.lstrip('/')}"

        # Format placeholders in URL
        url = url.format(**args)

        # Build payload from template
        data = None
        json_body = None
        if payload_template:
            # Deep-format simple dict using args as context
            template_str = json.dumps(payload_template)
            formatted_str = template_str.format(**args)
            json_body = json.loads(formatted_str)

        method = method.upper() if method else "GET"

        with httpx.Client(timeout=30.0) as client:
            resp = client.request(method, url, json=json_body, data=data)
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                return resp.text
