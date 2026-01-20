"""Embeddings service using HuggingFace."""
import asyncio

from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings


class EmbeddingsService:
    """Service for text embeddings."""

    def __init__(self) -> None:
        """Initialize embeddings model."""
        self.model = HuggingFaceEmbeddings(model_name=settings.EMBEDDINGS_MODEL)

    async def embed_query(self, text: str) -> list[float]:
        """Get embedding vector for query text."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.model.embed_query, text)

    def embed_query_sync(self, text: str) -> list[float]:
        """Synchronous version for use in executors."""
        return self.model.embed_query(text)


embeddings_service = EmbeddingsService()
