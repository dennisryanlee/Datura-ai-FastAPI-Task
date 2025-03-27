import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

API_KEY = settings.API_KEY

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_unauthenticated_dividends():
    """Test dividends endpoint without authentication"""
    response = client.get("/api/v1/tao_dividends")
    assert response.status_code == 401  # Unauthorized

def test_authenticated_dividends():
    """Test dividends endpoint with authentication"""
    response = client.get(
        "/api/v1/tao_dividends",
        headers={"X-API-Key": API_KEY}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "dividends" in data
    assert "stake" in data
    assert "balance" in data
    assert "netuid" in data
    assert "hotkey" in data
    assert "cached" in data
    assert data["cached"] is False  # First request should not be cached

def test_trade_parameter():
    """Test dividends endpoint with trade parameter"""
    response = client.get(
        "/api/v1/tao_dividends?trade=true",
        headers={"X-API-Key": API_KEY}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "task_id" in data
    assert data["stake_tx_triggered"] is True
    
    # Check task status
    task_id = data["task_id"]
    task_response = client.get(
        f"/api/v1/tasks/{task_id}",
        headers={"X-API-Key": API_KEY}
    )
    
    assert task_response.status_code == 200
    task_data = task_response.json()
    assert "status" in task_data
    # Task might be in various states, so just check it has a status
