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
        self.grpc_port = settings.QDRANT_GRPC_PORT
        self.prefer_grpc = settings.QDRANT_PREFER_GRPC
        self.collection = settings.QDRANT_COLLECTION

    def get_client(self) -> AsyncQdrantClient:
        """Create new client instance."""
        return AsyncQdrantClient(
            host=self.host,
            port=self.port,
            grpc_port=self.grpc_port,
            prefer_grpc=self.prefer_grpc,
        )

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

                await client.create_payload_index(
                    collection_name=self.collection,
                    field_name="content",
                    field_schema=models.TextIndexParams(
                        type="text",
                        tokenizer=models.TokenizerType.MULTILINGUAL,
                        min_token_len=2,
                        max_token_len=20,
                        lowercase=True,
                    ), # index for text search
                )
        finally:
            await client.close()

    async def search(self, query_vector: list[float], limit: int = 10) -> list[dict]:
        """Search similar documents."""
        client = self.get_client()
        try:
            result = await client.query_points(
                collection_name=self.collection,
                query=query_vector,
                limit=limit,
                with_payload=True,
            )
            results = []
            for p in result.points:
                payload = p.payload or {}
                meta = payload.get("metadata", {})
                results.append({
                    "id": p.id,
                    "source": meta.get("source", payload.get("source", "unknown")),
                    "page": meta.get("page", payload.get("page", 0)),
                    "content": payload.get("page_content", ""),
                    "score": p.score or 0.0,
                })
            return results
        finally:
            await client.close()

    async def search_bm25(self, query: str, limit: int) -> list[dict]:
        """Search documents using BM25 text search."""
        client = self.get_client()
        try:
            result, _ = await client.scroll(
                collection_name=self.collection,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="content",
                            match=models.MatchText(text=query)
                        )
                    ]
                ),
                limit=limit,
                with_payload=True,
            )
            results = []
            for p in result:
                payload = p.payload or {}
                meta = payload.get("metadata", {})
                results.append({
                    "id": p.id,
                    "source": meta.get("source", payload.get("source", "unknown")),
                    "page": meta.get("page", payload.get("page", 0)),
                    "content": payload.get("page_content", ""),
                    "score": 0.0,  # Scroll doesn't return score
                })
            return results
        finally:
            await client.close()


    @property
    def url(self) -> str:
        """Get HTTP URL for Qdrant."""
        return f"http://{self.host}:{self.port}"


qdrant_service = QdrantService()
