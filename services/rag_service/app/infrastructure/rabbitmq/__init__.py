"""RabbitMQ infrastructure package."""
from app.infrastructure.rabbitmq.consumer import start_consumer

__all__ = ["start_consumer"]
