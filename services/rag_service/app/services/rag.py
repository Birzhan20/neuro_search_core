"""RAG pipeline service."""
import os
import uuid
from dataclasses import dataclass

from app.crud import get_messages, get_or_create_session, save_message
from app.infrastructure.qdrant import qdrant_service
from app.services.embeddings import embeddings_service
from app.services.llm import llm_service


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


SYSTEM_PROMPT = """You are a corporate AI assistant.
Answer strictly based on the provided context.
If information is missing, say 'No information found'.

Context:
{context}"""


async def process_query(query: str, session_id: str | None = None) -> RAGResponse:
    """Process user query through RAG pipeline."""
    sid, _ = await get_or_create_session(session_id)
    await save_message(sid, "user", query)

    history_msgs = await get_messages(sid, limit=10)
    history = [(m.role, m.content) for m in history_msgs[:-1]]

    query_vector = await embeddings_service.embed_query(query)
    search_results = await qdrant_service.search(query_vector, limit=3)

    if not search_results:
        answer = "No relevant information found in documents."
        await save_message(sid, "assistant", answer)
        return RAGResponse(answer=answer, sources=[], session_id=str(sid))

    context_parts = []
    sources = []
    for r in search_results:
        context_parts.append(f"Document: {r['source']} (page {r['page']})\n{r['content']}")
        sources.append(Source(
            doc_name=os.path.basename(r["source"]),
            page=r["page"],
            score=r["score"],
        ))

    context = "\n---\n".join(context_parts)
    system_prompt = SYSTEM_PROMPT.format(context=context)

    messages = llm_service.build_messages(system_prompt, history, query)
    answer = await llm_service.generate(messages)

    await save_message(sid, "assistant", answer)

    return RAGResponse(answer=answer, sources=sources, session_id=str(sid))
