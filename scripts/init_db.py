"""Initialize the database by creating tables from SQLAlchemy models.

Run this once from the project root:
    python scripts/init_db.py
"""
import sys
from pathlib import Path

# Ensure project root is importable
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.connections import init_db, engine
# import models to ensure they're registered with Base
from models.tools import Tool  # noqa: F401

if __name__ == "__main__":
    print("Creating database tables...")
    try:
        init_db()
        print("✓ Database tables created successfully!")
        print(f"Connected to: {engine.url}")
    except Exception as exc:
        print(f"✗ Error creating tables: {exc}")
        sys.exit(1)
