"""Prometheus metrics."""
import time
from functools import wraps
from typing import Callable

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    "rag_requests_total",
    "Total number of RAG requests",
    ["method", "status"],
)

REQUEST_LATENCY = Histogram(
    "rag_request_latency_seconds",
    "Request latency in seconds",
    ["method"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

VECTOR_SEARCH_LATENCY = Histogram(
    "rag_vector_search_seconds",
    "Vector search latency in seconds",
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0],
)

LLM_LATENCY = Histogram(
    "rag_llm_latency_seconds",
    "LLM call latency in seconds",
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

DOCUMENT_PROCESSED = Counter(
    "rag_documents_processed_total",
    "Total number of documents processed",
    ["status"],
)


def track_latency(histogram: Histogram) -> Callable:
    """Decorator to track function latency."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                histogram.observe(time.perf_counter() - start)
        return wrapper
    return decorator


def get_metrics() -> bytes:
    """Generate Prometheus metrics output."""
    return generate_latest()


def get_content_type() -> str:
    """Get Prometheus content type."""
    return CONTENT_TYPE_LATEST
