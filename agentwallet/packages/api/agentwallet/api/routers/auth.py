"""Auth router -- register, login, API key management.

SECURITY NOTE: The /register and /login endpoints MUST have aggressive rate
limiting applied to prevent credential stuffing and brute-force attacks.
The check_rate_limit() dependency from middleware.rate_limit is applied to
these routes below. An in-process fallback rate limiter is now active when
Redis is unavailable.

Account lockout: After MAX_FAILED_LOGINS failures within LOCKOUT_WINDOW_SECONDS,
the account is locked for LOCKOUT_DURATION_SECONDS.
"""

import secrets
import time
import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.logging import get_logger
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
from ..middleware.rate_limit import check_rate_limit
from ..schemas.auth import (
    ApiKeyCreateRequest,
    ApiKeyListItem,
    ApiKeyResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# ── Account lockout (in-process, works without Redis) ─────────────────────
MAX_FAILED_LOGINS = 5
LOCKOUT_WINDOW_SECONDS = 300  # 5 minute window for counting failures
LOCKOUT_DURATION_SECONDS = 900  # 15 minute lockout

# Key: email → list of failure timestamps
_login_failures: dict[str, list[float]] = defaultdict(list)
# Key: email → lockout expiry timestamp
_account_locks: dict[str, float] = {}


def _check_account_lockout(email: str) -> None:
    """Raise 429 if account is locked due to too many failed logins."""
    now = time.monotonic()

    # Check if locked
    lock_until = _account_locks.get(email, 0)
    if lock_until > now:
        remaining = int(lock_until - now)
        raise HTTPException(
            status_code=429,
            detail=f"Account temporarily locked due to too many failed login attempts. "
                   f"Try again in {remaining} seconds.",
            headers={"Retry-After": str(remaining)},
        )
    elif lock_until > 0:
        # Lock expired, clear it
        del _account_locks[email]
        _login_failures.pop(email, None)


def _record_login_failure(email: str) -> None:
    """Record a failed login attempt. Lock account if threshold reached."""
    now = time.monotonic()
    failures = _login_failures[email]

    # Remove old failures outside the window
    cutoff = now - LOCKOUT_WINDOW_SECONDS
    while failures and failures[0] < cutoff:
        failures.pop(0)

    failures.append(now)

    if len(failures) >= MAX_FAILED_LOGINS:
        _account_locks[email] = now + LOCKOUT_DURATION_SECONDS
        logger.warning("account_locked", email=email, failures=len(failures))


def _clear_login_failures(email: str) -> None:
    """Clear failure counter on successful login."""
    _login_failures.pop(email, None)
    _account_locks.pop(email, None)


@router.post("/register", response_model=TokenResponse)
async def register(request: Request, req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new organization and admin user."""
    # Rate limit: stricter limit for auth endpoints to prevent abuse.
    await check_rate_limit(request, org_id="anon:register", tier="free")
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
async def login(request: Request, req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email/password, receive JWT."""
    # Rate limit: stricter limit for auth endpoints to prevent brute-force.
    await check_rate_limit(request, org_id="anon:login", tier="free")

    # Account lockout check
    _check_account_lockout(req.email)

    user = await db.scalar(select(User).where(User.email == req.email))
    if not user or not verify_password(req.password, user.password_hash):
        _record_login_failure(req.email)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    # Successful login — clear any failure counters
    _clear_login_failures(req.email)

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
    result = await db.execute(select(ApiKey).where(ApiKey.org_id == auth.org_id))
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
