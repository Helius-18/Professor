## Database Models with SQLite and SQLAlchemy

This module defines two tables using SQLAlchemy ORM on top of a SQLite database:

- **connections**
- **tools**

### Requirements

Install dependencies (preferably in a virtual environment):

```bash
pip install -r requirements.txt
```

### Running the model definition and creating the database

By default, the database will be created as a file named `app.db` in the same directory.

To create the tables, run:

```bash
python models.py
```

This will create `app.db` (if it does not exist) and create the `connections` and `tools` tables with the specified constraints.

## Fast MCP server (dynamic tools)

This repository includes a minimal FastAPI-based MCP server that dynamically loads tools from the SQLite database and exposes endpoints to list and execute them.

Quick start:

1. Install dependencies (prefer a virtual environment):

```powershell
pip install -r requirements.txt
```

2. Create sample data (this creates `app.db` and adds example tools):

```powershell
python create_sample_db.py
```

3. Run the server:

```powershell
uvicorn server:app --reload
```

4. Try the endpoints (default host:port 127.0.0.1:8000):

- List tools: GET http://127.0.0.1:8000/tools
- Execute a tool: POST http://127.0.0.1:8000/tools/1/execute  (JSON body optional)

Notes and assumptions:

- `Tool.tool_type` is either `DB` or `API`.
- For DB tools: `Connection.server_name` is treated as the SQLAlchemy DB URL (e.g. `sqlite:///app.db`); `Tool.content` contains SQL.
- For API tools: `Connection.endpoint` is the base URL and `Tool.content` is a path appended to it; the request type comes from `Connection.request_type` unless the execute request provides `override_method`.

If you want further features (authentication, sandboxing of SQL, templating, more robust parameter handling), I can add them next.



