# 1. Technology Stack Selection

Date: 2026-01-20
Status: Accepted

## Context
We need to develop a high-performance RAG (Retrieval-Augmented Generation) platform.
The system must handle asynchronous document ingestion (PDF parsing) and provide low-latency semantic search.

## Decision
We chose the following technology stack:

### 1. Core Language: Python (3.11+)
* **Why:** Unrivaled ecosystem for AI/ML (LangChain, Pydantic, HuggingFace).
* **Framework:** **FastAPI**. It supports asynchronous operations natively, which is critical for I/O bound tasks (calling LLM APIs).

### 2. Vector Database: Qdrant
* **Why:**
    * Written in Rust (extremely high performance).
    * Native support for metadata filtering (essential for RBAC in RAG).
    * Production-ready (unlike ChromaDB which is often used for prototypes).

### 3. Orchestration: Docker & Docker Compose
* **Why:** Ensures reproducible environments. The entire stack (App + DBs) can be launched with a single command.

### 4. API Gateway (Optional Future Step): Go
* **Why:** If RPS increases, we will introduce a Go proxy for rate limiting and connection pooling.

## Consequences
* **Positive:** Rapid development cycle due to Python's ecosystem. High retrieval speed due to Qdrant.
* **Negative:** Python's GIL limits CPU-bound performance, so we offload heavy parsing tasks to background workers (Celery/Task Queue).