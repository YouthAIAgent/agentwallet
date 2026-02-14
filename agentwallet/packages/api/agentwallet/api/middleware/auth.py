"""Authentication middleware -- JWT + API key verification."""

import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import get_settings
from ...core.database import get_db
from ...models.api_key import ApiKey
from ...models.organization import Organization

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def hash_api_key(key: str) -> str:
    """Hash an API key using HMAC-SHA256 with the server's JWT secret as the key.

    Using HMAC instead of plain SHA-256 prevents offline brute-force attacks
    if the database is compromised — the attacker would also need the server
    secret to verify candidate keys.
    """
    settings = get_settings()
    return hmac.new(
        settings.jwt_secret_key.encode(),
        key.encode(),
        hashlib.sha256,
    ).hexdigest()


def create_access_token(user_id: uuid.UUID, org_id: uuid.UUID) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {
        "sub": str(user_id),
        "org_id": str(org_id),
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


class AuthContext:
    """Resolved auth context injected into route handlers."""

    def __init__(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        api_key_id: uuid.UUID | None = None,
        agent_id: uuid.UUID | None = None,
        org_tier: str = "free",
        actor_type: str = "user",
    ):
        self.org_id = org_id
        self.user_id = user_id
        self.api_key_id = api_key_id
        self.agent_id = agent_id
        self.org_tier = org_tier
        self.actor_type = actor_type

    @property
    def actor_id(self) -> str:
        return str(self.user_id or self.api_key_id or "unknown")


def _resolve_agent_id(request: Request) -> uuid.UUID | None:
    """Extract optional agent_id from X-Agent-Id header."""
    agent_id_header = request.headers.get("X-Agent-Id")
    if agent_id_header:
        try:
            return uuid.UUID(agent_id_header)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid X-Agent-Id header (must be a valid UUID)")
    return None


async def _verify_agent_belongs_to_org(
    db: AsyncSession, agent_id: uuid.UUID, org_id: uuid.UUID
) -> None:
    """Verify that an agent belongs to the given organization."""
    from ...models.agent import Agent

    agent = await db.get(Agent, agent_id)
    if not agent or agent.org_id != org_id:
        raise HTTPException(status_code=403, detail="Agent does not belong to your organization")


async def get_auth_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """Resolve auth from either JWT bearer token or API key header."""
    settings = get_settings()
    agent_id = _resolve_agent_id(request)

    # Check for API key in header (SDK auth)
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        key_hash = hash_api_key(api_key_header)
        api_key = await db.scalar(select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True)))
        if not api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Update last used
        api_key.last_used_at = datetime.now(timezone.utc)

        org = await db.get(Organization, api_key.org_id)

        # Verify agent belongs to this org if specified
        if agent_id:
            await _verify_agent_belongs_to_org(db, agent_id, api_key.org_id)

        return AuthContext(
            org_id=api_key.org_id,
            api_key_id=api_key.id,
            agent_id=agent_id,
            org_tier=org.tier if org else "free",
            actor_type="api_key",
        )

    # Check for JWT bearer token (dashboard auth)
    if credentials:
        try:
            payload = jwt.decode(
                credentials.credentials,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            user_id = uuid.UUID(payload["sub"])
            org_id = uuid.UUID(payload["org_id"])

            org = await db.get(Organization, org_id)
            if not org or not org.is_active:
                raise HTTPException(status_code=401, detail="Organization inactive")

            # Verify agent belongs to this org if specified
            if agent_id:
                await _verify_agent_belongs_to_org(db, agent_id, org_id)

            return AuthContext(
                org_id=org_id,
                user_id=user_id,
                agent_id=agent_id,
                org_tier=org.tier,
                actor_type="user",
            )
        except (JWTError, KeyError, ValueError):
            raise HTTPException(status_code=401, detail="Invalid token")

    raise HTTPException(status_code=401, detail="Authentication required")
