# Enterprise AI API Gateway

A high-performance, strictly architected API Gateway for dynamic routing across multiple AI Providers (OpenAI, Gemini, Groq, Ollama).

## Features
- **Strict Clean Architecture**: Decoupled Domain from Frameworks.
- **Provider Adapters**: Easy integration with multiple AI vendors.
- **Resilience**: Integrated Redis Token Bucket rate limiting, Retry Manager, and Circuit Breaker.
- **Observability**: Prometheus metrics, Structlog Request Context.

## Stack
- Python 3.12
- FastAPI
- PostgreSQL + asyncpg
- Redis
- httpx

## Deployment
```bash
cd deploy
docker-compose up -d
```
