"""Qdrant vector database client."""
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from app.core.config import settings


class QdrantService:
    """Async Qdrant client wrapper."""

    def __init__(self) -> None:
        """Initialize Qdrant client."""
        self.host = settings.QDRANT_HOST
        self.port = settings.QDRANT_PORT
        self.collection = settings.QDRANT_COLLECTION

    def get_client(self) -> AsyncQdrantClient:
        """Create new client instance."""
        return AsyncQdrantClient(host=self.host, port=self.port)

    async def init_collection(self) -> None:
        """Create collection if not exists."""
        client = self.get_client()
        try:
            collections = await client.get_collections()
            exists = any(c.name == self.collection for c in collections.collections)
            if not exists:
                await client.create_collection(
                    collection_name=self.collection,
                    vectors_config=models.VectorParams(
                        size=384,
                        distance=models.Distance.COSINE,
                    ),
                )
        finally:
            await client.close()

    async def search(self, query_vector: list[float], limit: int = 3) -> list[dict]:
        """Search similar documents."""
        client = self.get_client()
        try:
            result = await client.query_points(
                collection_name=self.collection,
                query=query_vector,
                limit=limit,
                with_payload=True,
            )
            return [
                {
                    "source": p.payload.get("source", "unknown") if p.payload else "unknown",
                    "page": p.payload.get("page", 0) if p.payload else 0,
                    "content": p.payload.get("page_content", "") if p.payload else "",
                    "score": p.score or 0.0,
                }
                for p in result.points
            ]
        finally:
            await client.close()

    @property
    def url(self) -> str:
        """Get HTTP URL for Qdrant."""
        return f"http://{self.host}:{self.port}"


qdrant_service = QdrantService()
