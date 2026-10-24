import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.server import get_application
from app.application.services import gateway_service
from app.core.config import settings
from app.infrastructure.cache.memory_store import memory_store

CHAT = {"model": "test-model", "messages": [{"role": "user", "content": "hi"}]}


def make_upstream(calls: list, fail_hosts: dict | None = None):
    """Fake AI providers. fail_hosts maps hostname -> status code to return."""
    fail_hosts = fail_hosts or {}

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        status = fail_hosts.get(request.url.host)
        if status:
            return httpx.Response(status, json={"error": "boom"})
        return httpx.Response(200, json={"id": "chatcmpl-1", "host": request.url.host,
                                         "choices": [{"message": {"role": "assistant", "content": "hello"}}]})

    return httpx.MockTransport(handler)


@pytest.fixture
def make_client(db_file, monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEYS", "groq-key-1,groq-key-2")
    monkeypatch.setattr(settings, "OPENAI_API_KEYS", "openai-key")
    memory_store.clear()
    gateway_service._breakers.clear()
    gateway_service._limiter._local_buckets.clear()
    clients = []

    def factory(calls=None, fail_hosts=None):
        client = TestClient(get_application())
        client.__enter__()
        client.app.state.http_client = httpx.AsyncClient(transport=make_upstream(calls if calls is not None else [], fail_hosts))
        clients.append(client)
        return client

    yield factory
    for c in clients:
        c.__exit__(None, None, None)


def login(client, email, password):
    r = client.post("/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def user_headers(client, email="user@example.com"):
    r = client.post("/v1/auth/register", json={"email": email, "password": "password-123"})
    assert r.status_code == 200, r.text
    return login(client, email, "password-123")


def test_health(make_client):
    client = make_client()
    assert client.get("/health/live").json() == {"status": "alive"}
    assert client.get("/health/ready").json() == {"status": "ready"}


def test_frontend_is_served(make_client):
    r = make_client().get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"] and "AI Gateway" in r.text


def test_register_login_and_bad_credentials(make_client):
    client = make_client()
    user_headers(client)
    assert client.post("/v1/auth/register", json={"email": "USER@example.com", "password": "password-123"}).status_code == 400
    r = client.post("/v1/auth/login", json={"email": "user@example.com", "password": "wrong-password"})
    assert r.status_code == 401


def test_register_cannot_choose_a_role(make_client):
    client = make_client()
    r = client.post("/v1/auth/register", json={"email": "sneaky@example.com", "password": "password-123",
                                               "role_id": "00000000-0000-0000-0000-000000000000"})
    assert r.status_code == 200
    headers = login(client, "sneaky@example.com", "password-123")
    assert client.get("/v1/admin/providers/", headers=headers).status_code == 403


def test_admin_endpoints_require_admin(make_client):
    client = make_client()
    assert client.get("/v1/admin/providers/").status_code == 401
    assert client.get("/v1/admin/providers/", headers=user_headers(client)).status_code == 403

    admin = login(client, "admin@example.com", "admin-password-1")
    r = client.get("/v1/admin/providers/", headers=admin)
    assert r.status_code == 200
    assert {p["name"] for p in r.json()} == {"openai", "groq", "gemini", "ollama"}


def test_admin_can_add_and_disable_provider(make_client):
    client = make_client()
    admin = login(client, "admin@example.com", "admin-password-1")
    r = client.post("/v1/admin/providers/", headers=admin,
                    json={"name": "Custom", "base_url": "https://custom.example/v1/chat/completions", "priority": 5})
    assert r.status_code == 200 and r.json()["name"] == "custom"
    r = client.patch(f"/v1/admin/providers/{r.json()['id']}", headers=admin, json={"is_active": False})
    assert r.json()["is_active"] is False
    r = client.post("/v1/admin/providers/", headers=admin, json={"name": "x", "base_url": "not a url"})
    assert r.status_code == 422


def test_chat_requires_auth(make_client):
    client = make_client()
    assert client.post("/v1/gateway/chat/completions", json=CHAT).status_code == 401


def test_chat_routes_to_requested_provider_with_key_rotation_and_cache(make_client):
    calls = []
    client = make_client(calls)
    headers = user_headers(client)

    r = client.post("/v1/gateway/chat/completions", headers=headers, json={**CHAT, "provider": "groq"})
    assert r.status_code == 200
    assert r.headers["X-Gateway-Provider"] == "groq" and r.headers["X-Gateway-Cache"] == "MISS"
    assert r.json()["host"] == "api.groq.com"
    assert calls[0].headers["authorization"] == "Bearer groq-key-1"
    assert "provider" not in calls[0].read().decode()

    r = client.post("/v1/gateway/chat/completions", headers=headers, json={**CHAT, "provider": "groq"})
    assert r.headers["X-Gateway-Cache"] == "HIT"
    assert len(calls) == 1

    # A different prompt misses the cache and the next groq key is used.
    client.post("/v1/gateway/chat/completions", headers=headers,
                json={**CHAT, "provider": "groq", "messages": [{"role": "user", "content": "other"}]})
    assert calls[1].headers["authorization"] == "Bearer groq-key-2"


def test_unknown_or_unkeyed_provider(make_client):
    client = make_client()
    headers = user_headers(client)
    r = client.post("/v1/gateway/chat/completions", headers=headers, json={**CHAT, "provider": "nope"})
    assert r.status_code == 404
    r = client.post("/v1/gateway/chat/completions", headers=headers, json={**CHAT, "provider": "gemini"})
    assert r.status_code == 503 and "No API key" in r.json()["detail"]


def test_fails_over_to_next_provider_on_server_error(make_client):
    calls = []
    client = make_client(calls, fail_hosts={"api.groq.com": 500})  # groq has top priority
    headers = user_headers(client)
    r = client.post("/v1/gateway/chat/completions", headers=headers, json=CHAT)
    assert r.status_code == 200
    assert r.headers["X-Gateway-Provider"] == "openai"
    hosts = [c.url.host for c in calls]
    assert hosts.count("api.groq.com") == settings.GATEWAY_MAX_RETRIES and hosts[-1] == "api.openai.com"


def test_client_errors_are_not_retried_or_failed_over(make_client):
    calls = []
    client = make_client(calls, fail_hosts={"api.groq.com": 400})
    headers = user_headers(client)
    r = client.post("/v1/gateway/chat/completions", headers=headers, json=CHAT)
    assert r.status_code == 400
    assert len(calls) == 1


def test_circuit_breaker_opens_after_repeated_failures(make_client):
    calls = []
    client = make_client(calls, fail_hosts={"api.groq.com": 500, "api.openai.com": 500})
    headers = user_headers(client)
    for i in range(5):
        r = client.post("/v1/gateway/chat/completions", headers=headers,
                        json={**CHAT, "provider": "groq", "messages": [{"role": "user", "content": str(i)}]})
        assert r.status_code == 500
    before = len(calls)
    r = client.post("/v1/gateway/chat/completions", headers=headers, json={**CHAT, "provider": "groq"})
    assert r.status_code == 503 and "Circuit Breaker" in r.json()["detail"]
    assert len(calls) == before


def test_rate_limit_returns_429(make_client, monkeypatch):
    monkeypatch.setattr(gateway_service._limiter, "capacity", 2)
    monkeypatch.setattr(gateway_service._limiter, "refill_rate", 0.0001)
    client = make_client()
    headers = user_headers(client)
    codes = [client.post("/v1/gateway/chat/completions", headers=headers,
                         json={**CHAT, "provider": "groq", "temperature": i / 10}).status_code for i in range(3)]
    assert codes == [200, 200, 429]


def test_streaming_is_rejected(make_client):
    client = make_client()
    headers = user_headers(client)
    r = client.post("/v1/gateway/chat/completions", headers=headers, json={**CHAT, "provider": "groq", "stream": True})
    assert r.status_code == 400
