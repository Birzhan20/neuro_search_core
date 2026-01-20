import sys
import os
import grpc
import json
import pika
import threading
from concurrent import futures
import time

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http import models

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
proto_dir = os.path.join(project_root, 'proto')
sys.path.append(project_root)
sys.path.append(proto_dir)

from proto import rag_service_pb2
from proto import rag_service_pb2_grpc

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
COLLECTION_NAME = "documents"

embeddings_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def init_qdrant_collection():
    client = QdrantClient(host=QDRANT_HOST, port=6333)
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        print(f"Creating collection '{COLLECTION_NAME}'...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE
            )
        )
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists.")


def process_file_task(ch, method, properties, body):
    try:
        data = json.loads(body)
        task_id = data.get("task_id")
        file_path = data.get("file_path")
        print(f"Processing task {task_id}: {file_path}")
        if os.path.exists(file_path):
            loader = PyPDFLoader(file_path)
            pages = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(pages)
            
            print(f"Creating embeddings: {len(splits)} chunks")
            url = f"http://{QDRANT_HOST}:6333"
            Qdrant.from_documents(
                splits,
                embeddings_model,
                url=url,
                prefer_grpc=False,
                collection_name=COLLECTION_NAME
            )
            print(f"Task {task_id} saved to Qdrant")
        else:
            print(f"Error: file not found: {file_path}")

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing task: {e}")

def start_consumer():
    connection = None
    while connection is None:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError:
            print("Waiting for RabbitMQ...")
            time.sleep(5)

    print("Consumer connected to RabbitMQ")
    channel = connection.channel()
    channel.queue_declare(queue='ingestion_queue', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='ingestion_queue', on_message_callback=process_file_task)
    channel.start_consuming()


class RagService(rag_service_pb2_grpc.RagServiceServicer):
    def GetAnswer(self, request, context):
        print(f"Chat request: {request.message}")
        return rag_service_pb2.ChatResponse(
            answer=f"Received message: {request.message}",
            sources=[]
        )

def serve():
    init_qdrant_collection()
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rag_service_pb2_grpc.add_RagServiceServicer_to_server(RagService(), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    consumer_thread = threading.Thread(target=start_consumer, daemon=True)
    consumer_thread.start()
    
    serve()
