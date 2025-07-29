import sqlite3
import requests
import json
from datetime import datetime, timedelta
from langchain_core.tools import Tool

def get_fresh_token(auth_url, auth_method, auth_payload, auth_headers):
    if auth_method.upper() == "POST":
        resp = requests.post(auth_url, data=json.loads(auth_payload or "{}"), headers=json.loads(auth_headers or "{}"))
    else:
        resp = requests.get(auth_url, params=json.loads(auth_payload or "{}"), headers=json.loads(auth_headers or "{}"))
    
    data = resp.json()
    # Assume OAuth2-like response
    token = data.get("access_token")
    expires_in = data.get("expires_in", 3600)
    expiry = datetime.utcnow() + timedelta(seconds=expires_in)
    return token, expiry

def load_tools_from_db(db_path="tools.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, name, description, endpoint, method, params_schema,
                  auth_type, auth_value, auth_url, auth_method, auth_payload,
                  auth_headers, token_expires_at
           FROM tools WHERE enabled=1"""
    )
    rows = cursor.fetchall()
    conn.close()

    tools = []
    for (tool_id, name, desc, endpoint, method, params_schema,
         auth_type, auth_value, auth_url, auth_method, auth_payload,
         auth_headers, token_expires_at) in rows:

        def make_func(endpoint=endpoint, method=method, auth_type=auth_type,
                      auth_value=auth_value, auth_url=auth_url, auth_method=auth_method,
                      auth_payload=auth_payload, auth_headers=auth_headers, tool_id=tool_id):

            def func(**kwargs):
                headers = {}

                # --- Handle Authentication ---
                token = auth_value
                if auth_type in ("bearer_refresh", "oauth2"):
                    expiry = datetime.fromisoformat(token_expires_at) if token_expires_at else datetime.utcnow() - timedelta(seconds=1)
                    if datetime.utcnow() >= expiry:
                        new_token, new_expiry = get_fresh_token(auth_url, auth_method, auth_payload, auth_headers)
                        token = new_token
                        # Update DB with new token + expiry
                        conn = sqlite3.connect("tools.db")
                        cur = conn.cursor()
                        cur.execute("UPDATE tools SET auth_value=?, token_expires_at=? WHERE id=?",
                                    (new_token, new_expiry.isoformat(), tool_id))
                        conn.commit()
                        conn.close()
                if auth_type == "bearer" and token:
                    headers["Authorization"] = f"Bearer {token}"
                elif auth_type == "apikey" and token:
                    headers["x-api-key"] = token

                # --- Make actual request ---
                url = endpoint.format(**kwargs)
                if method.upper() == "GET":
                    resp = requests.get(url, headers=headers, params=kwargs)
                elif method.upper() == "POST":
                    resp = requests.post(url, headers=headers, json=kwargs)
                else:
                    return f"Unsupported method {method}"

                try:
                    return resp.json()
                except Exception:
                    return resp.text

            return func

        tools.append(Tool(name=name, func=make_func(), description=desc))

    return tools
