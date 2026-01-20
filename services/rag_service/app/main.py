"""RAG Service entry point."""
import asyncio
import logging
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread

import grpc

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.database import db
from app.core.metrics import get_content_type, get_metrics
from app.grpc_api import RagServiceHandler
from app.infrastructure.qdrant import qdrant_service
from app.infrastructure.rabbitmq import start_consumer
from proto import rag_service_pb2_grpc

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

METRICS_PORT = 9090


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics."""

    def do_GET(self):
        """Handle GET /metrics."""
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", get_content_type())
            self.end_headers()
            self.wfile.write(get_metrics())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress HTTP logs."""
        pass


def start_metrics_server():
    """Start metrics HTTP server in background."""
    server = HTTPServer(("0.0.0.0", METRICS_PORT), MetricsHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Metrics server started on port %d", METRICS_PORT)


async def serve() -> None:
    """Start gRPC server and RabbitMQ consumer."""
    start_metrics_server()

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
