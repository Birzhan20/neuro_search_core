"""Reranking service using CrossEncoder from Sentence Transformers."""

import torch
from sentence_transformers import CrossEncoder


class RerankerService:
    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        # device="cuda" если есть GPU, иначе "cpu"
        device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model = CrossEncoder(
            model_name,
            device=device,
            trust_remote_code=True,
            automodel_args={"torch_dtype": torch.float16} if device == "cuda" else {}, # for better performance on GPU
        )

    def rerank(self, query: str, documents: list[dict], top_k: int = 3) -> list[dict]:
        """Rerank documents based on their relevance to the query using CrossEncoder."""
        if not documents:
            return []

        pairs = []
        for doc in documents:
            doc_content = doc.get("content", "")
            pairs.append([query, doc_content])

        scores = self.model.predict(pairs)

        for i, doc in enumerate(documents):
            doc["rerank_score"] = float(scores[i])

        sorted_docs = sorted(documents, key=lambda x: x["rerank_score"], reverse=True)

        return sorted_docs[:top_k]

reranker_service = RerankerService()
