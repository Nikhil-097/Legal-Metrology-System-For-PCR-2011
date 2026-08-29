import io
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_rules_summary_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/rules/summary")
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    assert data["total_rules"] == 35  # Rule 1 to 34 including 32-A[cite: 1]


@pytest.mark.asyncio
async def test_calculate_min_font_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(
            "/api/v1/rules/calculate-min-font",
            params={"pdp_area_cm2": 150.0, "net_quantity": 500.0, "unit": "g"}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["required_min_font_height_mm"] == 4.0


@pytest.mark.asyncio
async def test_auth_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            data={"username": "officer@doca.gov.in", "password": "password123"}
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "LEGAL_OFFICER"


@pytest.mark.asyncio
async def test_analytics_dashboard_stats():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/analytics/dashboard-stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_scans" in data
    assert "compliance_rate_percentage" in data