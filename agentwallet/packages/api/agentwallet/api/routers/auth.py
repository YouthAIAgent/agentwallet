"""Auth router -- register, login, API key management."""

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...models.api_key import ApiKey
from ...models.organization import Organization
from ...models.user import User
from ..middleware.auth import (
    AuthContext,
    create_access_token,
    get_auth_context,
    hash_api_key,
    hash_password,
    verify_password,
)
from ..schemas.auth import (
    ApiKeyCreateRequest,
    ApiKeyListItem,
    ApiKeyResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new organization and admin user."""
    existing = await db.scalar(select(User).where(User.email == req.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    org = Organization(name=req.org_name, email=req.email)
    db.add(org)
    await db.flush()

    user = User(
        org_id=org.id,
        email=req.email,
        password_hash=hash_password(req.password),
        role="admin",
    )
    db.add(user)
    await db.flush()

    token = create_access_token(user.id, org.id)
    return TokenResponse(access_token=token, org_id=org.id)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email/password, receive JWT."""
    user = await db.scalar(select(User).where(User.email == req.email))
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    token = create_access_token(user.id, user.org_id)
    return TokenResponse(access_token=token, org_id=user.org_id)


@router.post("/api-keys", response_model=ApiKeyResponse)
async def create_api_key(
    req: ApiKeyCreateRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key for SDK access."""
    raw_key = f"aw_live_{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key(raw_key)
    prefix = raw_key[:15] + "..."

    api_key = ApiKey(
        org_id=auth.org_id,
        key_hash=key_hash,
        key_prefix=prefix,
        name=req.name,
        permissions=req.permissions,
    )
    db.add(api_key)
    await db.flush()

    return ApiKeyResponse(
        id=api_key.id,
        key=raw_key,
        key_prefix=prefix,
        name=req.name,
        permissions=req.permissions,
        created_at=api_key.created_at.isoformat(),
    )


@router.get("/api-keys", response_model=list[ApiKeyListItem])
async def list_api_keys(
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for the organization."""
    result = await db.execute(
        select(ApiKey).where(ApiKey.org_id == auth.org_id)
    )
    keys = result.scalars().all()
    return [
        ApiKeyListItem(
            id=k.id,
            key_prefix=k.key_prefix,
            name=k.name,
            permissions=k.permissions,
            is_active=k.is_active,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            created_at=k.created_at.isoformat(),
        )
        for k in keys
    ]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: uuid.UUID,
    auth: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""
    key = await db.get(ApiKey, key_id)
    if not key or key.org_id != auth.org_id:
        raise HTTPException(status_code=404, detail="API key not found")
    key.is_active = False
    return {"status": "revoked"}
