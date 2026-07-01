# Project Explanation & Interview Guide

This document is designed to help you prepare for technical interviews regarding the **Enterprise AI API Gateway**.

## 1. Architectural Pattern: Clean Architecture
**Question**: Why use Clean Architecture instead of standard MVC?
**Answer**: By decoupling the Domain layer from the Infrastructure layer (e.g., SQLAlchemy), we ensure that core business rules remain unaffected by database technology changes. It makes unit testing trivial because entities and use-cases don't require an active database connection. 

## 2. Design Patterns
**Adapter Pattern**: The `AIGatewayProvider` interface allows us to normalize requests and responses. Adding a new provider only involves creating a new class (e.g., `AnthropicAdapter`) without modifying the core `ProxyEngine`.

**Circuit Breaker Pattern**: To protect the system from cascading failures, the `CircuitBreaker` class tracks upstream failures. If an AI provider like OpenAI goes down, the circuit opens, failing fast rather than hanging threads waiting for timeouts.

**Repository Pattern**: Used for all database accesses (`IUserRepository`, etc.). It abstracts the data layer, allowing us to swap Postgres for MongoDB later if required.

## 3. Resilience and Concurrency
**Rate Limiting**: Implemented a Redis-based Token Bucket. By using a Lua script/pipeline approach, we ensure atomic operations in a highly concurrent environment.
**Retry Logic**: Exponential backoff is used to handle transient network blips to AI providers gracefully.

## 4. Observability
**Structlog**: We inject a unique `Trace ID` into every log across the request lifecycle. This is critical for distributed tracing in microservices.
**Prometheus**: Exposed `/admin/metrics` to track latency and error rates in real-time.

## Scalability Considerations
- **Statelessness**: The FastAPI nodes are completely stateless (sessions stored in JWT, limits in Redis), meaning they can scale horizontally infinitely behind an ingress load balancer.
- **AsyncIO**: We use `httpx` and `asyncpg` to avoid blocking OS threads, allowing a single node to handle thousands of concurrent I/O heavy connections (vital since AI APIs are notoriously slow).
