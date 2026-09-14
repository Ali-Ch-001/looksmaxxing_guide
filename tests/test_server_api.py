"""Integration tests for FastAPI REST Endpoints & Web UI."""

import pytest
import httpx
from src.server import app


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "looksmaxxing.guide-engine"


@pytest.mark.asyncio
async def test_html_ui_endpoint():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "looksmaxxing<span class=\"text-emerald-400\">.guide</span>" in resp.text
        assert "Deterministic Posological AST Engine" in resp.text


@pytest.mark.asyncio
async def test_api_generate_valid_langgraph():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/generate", json={"topic": "oral minoxidil", "use_langgraph": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["engine"] == "LangGraph StateGraph"
        assert data["audit_passed"] is True
        assert data["citations_count"] > 0
        assert data["markdown"] is not None
        assert data["json_ld"] is not None


@pytest.mark.asyncio
async def test_api_generate_banned_practice():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/generate", json={"topic": "bone smashing jawline", "use_langgraph": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_category"] == "banned"
        assert data["is_crisis_routed"] is True
        assert data["audit_passed"] is False
        assert "bone smashing" in data["rejection_reason"].lower()


@pytest.mark.asyncio
async def test_api_verify_dosage():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Safe dose
        r_safe = await client.post("/api/v1/verify-dosage", json={"text": "Take 1.25 mg oral minoxidil daily"})
        assert r_safe.status_code == 200
        assert r_safe.json()["passed"] is True

        # Overdose
        r_over = await client.post("/api/v1/verify-dosage", json={"text": "Take 10 mg oral minoxidil daily"})
        assert r_over.status_code == 200
        assert r_over.json()["passed"] is False
        assert len(r_over.json()["violations"]) > 0


@pytest.mark.asyncio
async def test_api_genetic_eval():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/genetic-eval", json={"population_size": 15, "generations": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert data["generations_run"] == 2
        assert data["escape_rate"] == 0.0
        assert data["resilience_score"] == 1.0
