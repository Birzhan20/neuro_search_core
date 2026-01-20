"""RAG Service entry point."""
import asyncio
import logging
import sys
from pathlib import Path

import grpc

sys.path.insert(0, str(Path(__file__).parent))

from core.config import settings
from core.database import db
from grpc_api import RagServiceHandler
from infrastructure.qdrant import qdrant_service
from infrastructure.rabbitmq import start_consumer
from proto import rag_service_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def serve() -> None:
    """Start gRPC server and RabbitMQ consumer."""
    logger.info("Connecting to PostgreSQL...")
    await db.create_tables()
    logger.info("Database ready")

    logger.info("Initializing Qdrant...")
    await qdrant_service.init_collection()
    logger.info("Qdrant ready")

    server = grpc.aio.server()
    rag_service_pb2_grpc.add_RagServiceServicer_to_server(RagServiceHandler(), server)
    server.add_insecure_port(settings.GRPC_PORT)
    logger.info("gRPC server started on %s", settings.GRPC_PORT)

    await server.start()

    try:
        await asyncio.gather(
            server.wait_for_termination(),
            start_consumer(),
        )
    except asyncio.CancelledError:
        await server.stop(0)
    finally:
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        pass
