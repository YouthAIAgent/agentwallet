"""Auth request/response schemas."""

import re
import uuid

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    org_name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    org_id: uuid.UUID


class ApiKeyCreateRequest(BaseModel):
    name: str
    permissions: dict = {}


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    key: str  # Only returned on creation
    key_prefix: str
    name: str
    permissions: dict
    created_at: str


class ApiKeyListItem(BaseModel):
    id: uuid.UUID
    key_prefix: str
    name: str
    permissions: dict
    is_active: bool
    last_used_at: str | None
    created_at: str
