"""Qdrant infrastructure package."""
from app.infrastructure.qdrant.client import QdrantService, qdrant_service

__all__ = ["QdrantService", "qdrant_service"]
