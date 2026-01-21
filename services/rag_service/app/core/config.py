"""Application configuration."""
import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings from environment variables."""

    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "qdrant")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION: str = "documents"

    DB_HOST: str = os.getenv("DB_HOST", "postgres")
    DB_USER: str = os.getenv("POSTGRES_USER", "user")
    DB_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    DB_NAME: str = os.getenv("POSTGRES_DB", "neurosearch")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDINGS_MODEL: str = "all-MiniLM-L6-v2"

    GRPC_PORT: str = "[::]:50051"

    CHUNK_SIZE_TOKENS: int = 256
    CHUNK_OVERLAP_TOKENS: int = 100
    TIKTOKEN_ENCODING: str = "cl100k_base"

    @property
    def database_url(self) -> str:
        """Build PostgreSQL connection string."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:5432/{self.DB_NAME}"


settings = Settings()
