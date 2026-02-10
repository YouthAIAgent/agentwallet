"""Auth request/response schemas."""

import uuid

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    org_name: str
    email: EmailStr
    password: str


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
