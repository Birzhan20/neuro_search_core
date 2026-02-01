"""RAG pipeline service with Jinja2 templates."""
import asyncio
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.core.metrics import LLM_LATENCY, REQUEST_COUNT, REQUEST_LATENCY, VECTOR_SEARCH_LATENCY
from app.crud import get_messages, get_or_create_session, save_message
from app.infrastructure.qdrant import qdrant_service
from app.services.embeddings import embeddings_service
from app.services.llm import llm_service
from app.services.reranker import reranker_service

logger = logging.getLogger(__name__)


TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)


@dataclass
class Source:
    """Document source reference."""

    doc_name: str
    page: int
    score: float


@dataclass
class RAGResponse:
    """RAG pipeline response."""

    answer: str
    sources: list[Source]
    session_id: str


def render_system_prompt(context: str) -> str:
    """Render system prompt from Jinja2 template."""
    template = jinja_env.get_template("system_prompt.j2")
    return template.render(context=context)


def reciprocal_rank_fusion(vector_results, bm25_results, k=60, limit=3):
    scores = {}

    for rank, res in enumerate(vector_results, start=1):
        doc_id = res['id']
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
        scores[doc_id + "_data"] = res

    for rank, res in enumerate(bm25_results, start=1):
        doc_id = res['id']
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
        if doc_id + "_data" not in scores:
            scores[doc_id + "_data"] = res

    sorted_ids = sorted([key for key in scores if not key.endswith("_data")],
                        key=lambda x: scores[x], reverse=True)

    return [scores[doc_id + "_data"] for doc_id in sorted_ids[:limit]]


async def process_query(query: str, session_id: str | None = None) -> RAGResponse:
    """Process user query through RAG pipeline."""
    start_time = time.perf_counter()

    try:
        sid, _ = await get_or_create_session(session_id)
        await save_message(sid, "user", query)

        history_msgs = await get_messages(sid, limit=10)
        history = [(m.role, m.content) for m in history_msgs[:-1]]

        vector_start = time.perf_counter()
        query_vector = await embeddings_service.embed_text(query)
        vector_task = qdrant_service.search(query_vector, limit=25)
        bm25_task = qdrant_service.search_bm25(query, limit=25)
        vector_results, bm25_results = await asyncio.gather(vector_task, bm25_task)
        initial_candidates = reciprocal_rank_fusion(vector_results, bm25_results, limit=25)
        search_results = await asyncio.get_running_loop().run_in_executor(
            None,
            reranker_service.rerank,
            query,
            initial_candidates,
            3
        )
        VECTOR_SEARCH_LATENCY.observe(time.perf_counter() - vector_start)

        if not search_results:
            answer = "No relevant information found in documents."
            await save_message(sid, "assistant", answer)
            REQUEST_COUNT.labels(method="chat", status="no_results").inc()
            logger.info(f"No results for query: {query[:50]}...")
            return RAGResponse(answer=answer, sources=[], session_id=str(sid))

        context_parts = []
        sources = []
        for r in search_results:
            context_parts.append(f"Document: {r['source']} (page {r['page']})\n{r['content']}")
            sources.append(Source(
                doc_name=os.path.basename(r.get("source", "unknown")),
                page=r.get("page", 0),
                score=r.get("rerank_score", 0.0),
            ))

        context = "\n---\n".join(context_parts)
        system_prompt = render_system_prompt(context)

        messages = llm_service.build_messages(system_prompt, history, query)

        llm_start = time.perf_counter()
        answer = await llm_service.generate(messages)
        LLM_LATENCY.observe(time.perf_counter() - llm_start)

        await save_message(sid, "assistant", answer)

        REQUEST_COUNT.labels(method="chat", status="success").inc()
        logger.info(f"Query processed in {time.perf_counter() - start_time:.2f}s")
        return RAGResponse(answer=answer, sources=sources, session_id=str(sid))

    except Exception as e:
        REQUEST_COUNT.labels(method="chat", status="error").inc()
        logger.error(f"RAG pipeline error: {e}")
        raise

    finally:
        REQUEST_LATENCY.labels(method="chat").observe(time.perf_counter() - start_time)
