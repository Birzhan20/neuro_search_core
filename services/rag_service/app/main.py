import sys
import os
import grpc
from concurrent import futures
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
proto_dir = os.path.join(project_root, 'proto')
sys.path.append(project_root)
sys.path.append(proto_dir)

from proto import rag_service_pb2
from proto import rag_service_pb2_grpc

class RagService(rag_service_pb2_grpc.RagServiceServicer):
    def GetAnswer(self, request, context):
        print(f"go: {request.message}")
        print(f"history count: {len(request.history)}")

        mock_answer = f"success: '{request.message}'."
        
        response = rag_service_pb2.ChatResponse(
            answer=mock_answer,
            sources=[
                rag_service_pb2.Source(doc_name="manual.pdf", page=1, score=0.99),
                rag_service_pb2.Source(doc_name="compliance.docx", page=12, score=0.85)
            ]
        )
        return response

def serve():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rag_service_pb2_grpc.add_RagServiceServicer_to_server(RagService(), server)
    server.add_insecure_port('[::]:' + port)
    
    print(f"started on port {port}")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()