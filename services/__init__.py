"""Services package for Professor project.

This file makes `services` an importable package so scripts like
`python -m services.agent` or `python services\agent.py` can import
submodules using absolute imports (`from services import ...`).
"""

__all__ = ["agent", "tool_builder"]
