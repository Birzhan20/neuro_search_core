"""gRPC service handler."""
import logging

import grpc

from app.services.rag import process_query
from proto import rag_service_pb2, rag_service_pb2_grpc


logger = logging.getLogger(__name__)


class RagServiceHandler(rag_service_pb2_grpc.RagServiceServicer):
    """gRPC handler for RAG service."""

    async def GetAnswer(
        self,
        request: rag_service_pb2.ChatRequest,
        context: grpc.aio.ServicerContext,
    ) -> rag_service_pb2.ChatResponse:
        """Handle chat request."""
        query = request.message
        session_id = request.session_id if request.session_id else None

        logger.info("Query: %s", query)

        try:
            result = await process_query(query, session_id)

            sources = [
                rag_service_pb2.Source(
                    doc_name=s.doc_name,
                    page=s.page,
                    score=s.score,
                )
                for s in result.sources
            ]

            return rag_service_pb2.ChatResponse(
                answer=result.answer,
                sources=sources,
                session_id=result.session_id,
            )

        except Exception as e:
            logger.exception("RAG error: %s", e)
            return rag_service_pb2.ChatResponse(
                answer="Error processing request.",
                sources=[],
                session_id=session_id or "",
            )
