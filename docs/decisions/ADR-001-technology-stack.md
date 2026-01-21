# 1. Technology Stack

**Date:** 2026-01-21
**Status:** Accepted

## Decision

### 1. Language: Python 3.11+ (RAG Service)
*   **Role:** Core logic, ML integration.
*   **Libs:** `grpcio-tools`, `langchain`, `qdrant-client`, `aio-pika`.

### 2. Language: Go 1.22+ (API Gateway)
*   **Role:** High-performance entry point.
*   **Libs:** `gin`, `grpc`, `amqp`.

### 3. Protocol: gRPC
*   **Why:** Low latency communication between Gateway and RAG service. Strict schema (Protobuf).

### 4. Vector DB: Qdrant
*   **Why:** High performance Rust engine, excellent Python client, advanced filtering.

### 5. Deployment: Docker Compose
*   **Why:** Reproducible local development environment.

## Context
Moved from REST-only architecture to gRPC for internal service communication to improve latency and type safety.