"""Expose the FastAPI app at the package level.

This lets ``uvicorn api:app`` work in addition to ``uvicorn app.main:app`` and
``uvicorn api.index:app``, so the server starts regardless of which common
invocation is used.
"""

from app.main import app

__all__ = ["app"]
