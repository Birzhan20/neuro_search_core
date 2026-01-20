"""Core package."""
from app.core.config import settings
from app.core.database import db

__all__ = ["db", "settings"]
