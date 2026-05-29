"""T4.2 — FastAPI app skeleton tests (css-async-coder spec, F3 absorbed)."""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


async def test_cors_headers_present():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.options(
            "/api/health",
            headers={
                "Origin": "http://localhost",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert "access-control-allow-origin" in {h.lower() for h in r.headers.keys()}


# F3: CSRF Origin check — mutating request from a foreign origin must be rejected
async def test_mutating_request_with_foreign_origin_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/health", headers={"Origin": "http://evil.com"})
    assert r.status_code == 403
