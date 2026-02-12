"""Tests for authentication and authorization."""

import pytest


@pytest.mark.asyncio
async def test_register(unauthed_client):
    """Test user registration."""
    resp = await unauthed_client.post("/v1/auth/register", json={
        "org_name": "Auth Test Org",
        "email": "authtest@example.com",
        "password": "securepass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "org_id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(unauthed_client):
    """Test registration with duplicate email fails."""
    payload = {
        "org_name": "Dup Org",
        "email": "duptest@example.com",
        "password": "securepass123",
    }
    resp = await unauthed_client.post("/v1/auth/register", json=payload)
    assert resp.status_code == 200

    resp = await unauthed_client.post("/v1/auth/register", json={
        "org_name": "Dup Org 2",
        "email": "duptest@example.com",
        "password": "otherpass123",
    })
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login(unauthed_client):
    """Test login flow."""
    # Register first
    await unauthed_client.post("/v1/auth/register", json={
        "org_name": "Login Test Org",
        "email": "logintest@example.com",
        "password": "testpass123",
    })

    # Login
    resp = await unauthed_client.post("/v1/auth/login", json={
        "email": "logintest@example.com",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(unauthed_client):
    """Test login with wrong password."""
    resp = await unauthed_client.post("/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpass",
    })
    assert resp.status_code in (401, 404)


@pytest.mark.asyncio
async def test_unauthenticated_access(unauthed_client):
    """Test that protected endpoints require auth."""
    resp = await unauthed_client.get("/v1/agents")
    assert resp.status_code == 401
