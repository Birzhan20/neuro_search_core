"""Document processing service."""
import asyncio
import os

import docx
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.core.metrics import DOCUMENT_PROCESSED
from app.infrastructure.qdrant import qdrant_service
from app.services.embeddings import embeddings_service

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def load_document(file_path: str) -> list[Document]:
    """Load document by file extension."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return PyPDFLoader(file_path).load()

    if ext == ".docx":
        doc = docx.Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
        return [Document(page_content=text, metadata={"source": file_path})]

    if ext == ".txt":
        return TextLoader(file_path, encoding="utf-8").load()

    raise ValueError(f"Unsupported format: {ext}")


def split_documents(documents: list[Document]) -> list[Document]:
    """Split documents into chunks."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    return splitter.split_documents(documents)


def upload_to_qdrant(chunks: list[Document]) -> None:
    """Upload document chunks to Qdrant."""
    Qdrant.from_documents(
        chunks,
        embeddings_service.model,
        url=qdrant_service.url,
        prefer_grpc=False,
        collection_name=settings.QDRANT_COLLECTION,
    )


async def process_document(file_path: str) -> None:
    """Process document: load, split, embed, and store."""
    if not os.path.exists(file_path):
        DOCUMENT_PROCESSED.labels(status="not_found").inc()
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        DOCUMENT_PROCESSED.labels(status="unsupported").inc()
        raise ValueError(f"Unsupported format: {ext}")

    loop = asyncio.get_running_loop()

    def process() -> None:
        documents = load_document(file_path)
        chunks = split_documents(documents)
        upload_to_qdrant(chunks)

    try:
        await loop.run_in_executor(None, process)
        DOCUMENT_PROCESSED.labels(status="success").inc()
    except Exception:
        DOCUMENT_PROCESSED.labels(status="error").inc()
        raise

