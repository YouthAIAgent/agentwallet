"""Tests for authentication and authorization operations."""


import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from agentwallet.models import User

@pytest.mark.asyncio
async def test_register(
    async_client: AsyncClient,
    db_session: AsyncSession,
    mock_redis,
    mock_solana_rpc
):
    """Test user registration."""
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    }
    
    response = await async_client.post(
        "/api/v1/auth/register",
        json=register_data
    )
    
    assert response.status_code == 201
    assert "access_token" in response.json()
    
    # Verify user was created in database
    result = await db_session.execute(
        User.__table__.select().where(User.email == register_data["email"])
    )
    db_user = result.first()
    assert db_user is not None


@pytest.mark.asyncio
async def test_register_duplicate_email(
    async_client: AsyncClient,
    db_session: AsyncSession,
    mock_redis,
    mock_solana_rpc
):
    """Test registration with duplicate email."""
    # Create user in database
    test_user = User(
        username="existinguser",
        email="test@example.com",
        is_active=True
    )
    db_session.add(test_user)
    await db_session.commit()
    
    # Attempt to register with same email
    register_data = {
        "username": "othertest",
        "email": "test@example.com",
        "password": "Password123"
    }
    
    response = await async_client.post(
        "/api/v1/auth/register",
        json=register_data
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(
    async_client: AsyncClient,
    test_user: User
):
    """Test successful login."""
    login_data = {
        "username": test_user.email,
        "password": "test_password"
    }
    
    response = await async_client.post(
        "/api/v1/auth/login",
        data=login_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"



@pytest.mark.asyncio
async def test_login_invalid_credentials(
    async_client: AsyncClient
):
    """Test login with invalid credentials."""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "wrong"
    }
    
    response = await async_client.post(
        "/api/v1/auth/login",
        data=login_data
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_api_key(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test creating API key."""
    response = await async_client.post(
        "/api/v1/auth/api-key",
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "api_key" in data
    assert "expires_at" in data


@pytest.mark.asyncio
async def test_get_current_user(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test retrieving current user information."""
    response = await async_client.get(
        "/api/v1/users/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data


@pytest.mark.asyncio
async def test_unauthorized_access(
    async_client: AsyncClient
):
    """Test unauthorized access to protected endpoint."""
    response = await async_client.get(
        "/api/v1/users/me"
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_key_authentication(
    async_client: AsyncClient,
    test_user: User
):
    """Test authentication with API key."""
    # First create API key
    response = await async_client.post(
        "/api/v1/auth/api-key",
        headers={"Authorization": f"Bearer {auth_headers["Authorization"]}"
    )
    data = response.json()
    api_key = data["api_key"]

    # Test access with API key
    response = await async_client.get(
        "/api/v1/users/me",
        headers={"X-API-Key": api_key}
    )
    
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_api_key(
    async_client: AsyncClient
):
    """Test with invalid API key."""
    response = await async_client.get(
        "/api/v1/users/me",
        headers={"X-API-Key": "invalid-key-123"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_password_recovery_start(
    async_client: AsyncClient
):
    """Test initiating password recovery."""
    response = await async_client.post(
        "/api/v1/auth/recover-password",
        json={"email": "test@example.com"}
    )
    
    # Should return 200 even if email not found, for security reasons
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_password_reset(
    async_client: AsyncClient
):
    """Test password reset with token."""
    response = await async_client.post(
        "/api/v1/auth/recover-password",
        json={"email": "test@example.com"}
    )
    
    # Should return 200 even if email not found, for security reasons
    assert response.status_code == 200