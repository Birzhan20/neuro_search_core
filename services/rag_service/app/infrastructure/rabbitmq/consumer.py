"""RabbitMQ consumer for file ingestion."""
import asyncio
import json
import logging

from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage

from app.core.config import settings
from app.services.document_processor import process_document

logger = logging.getLogger(__name__)


async def process_task(message: AbstractIncomingMessage) -> None:
    """Process single ingestion task."""
    async with message.process():
        try:
            data = json.loads(message.body.decode())
            task_id = data.get("task_id", "unknown")
            file_path = data.get("file_path", "")

            logger.info("Processing task %s: %s", task_id, file_path)
            await process_document(file_path)
            logger.info("Task %s completed", task_id)

        except Exception as e:
            logger.exception("Error processing task: %s", e)


async def start_consumer() -> None:
    """Connect to RabbitMQ and consume messages."""
    retries = 5
    connection = None

    while retries > 0:
        try:
            connection = await connect_robust(settings.RABBITMQ_URL)
            logger.info("Connected to RabbitMQ")
            break
        except Exception:
            logger.warning("Waiting for RabbitMQ...")
            await asyncio.sleep(5)
            retries -= 1

    if not connection:
        logger.error("Could not connect to RabbitMQ")
        return

    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue("ingestion_queue", durable=True)
        await channel.set_qos(prefetch_count=1)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await process_task(message)
