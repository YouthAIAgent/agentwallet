"""FastAPI application entry point for AgentWallet Protocol."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import get_settings
from .core.database import close_db
from .core.exceptions import (
    AgentWalletError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
    TierLimitError,
    ValidationError,
)
from .core.logging import setup_logging
from .core.redis_client import close_redis

from .api.routers import (
    agents,
    analytics,
    auth,
    compliance,
    escrow,
    policies,
    transactions,
    wallets,
    webhooks,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)
    yield
    await close_db()
    await close_redis()


app = FastAPI(
    title="AgentWallet Protocol",
    description="AI Agent Wallet Infrastructure on Solana",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /v1
app.include_router(auth.router, prefix="/v1")
app.include_router(wallets.router, prefix="/v1")
app.include_router(agents.router, prefix="/v1")
app.include_router(transactions.router, prefix="/v1")
app.include_router(escrow.router, prefix="/v1")
app.include_router(analytics.router, prefix="/v1")
app.include_router(compliance.router, prefix="/v1")
app.include_router(policies.router, prefix="/v1")
app.include_router(webhooks.router, prefix="/v1")


# Global exception handlers
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"error": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"error": str(exc)})


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"error": str(exc)})


@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content={"error": str(exc)})


@app.exception_handler(AuthorizationError)
async def authz_error_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(status_code=403, content={"error": str(exc)})


@app.exception_handler(TierLimitError)
async def tier_limit_handler(request: Request, exc: TierLimitError):
    return JSONResponse(status_code=402, content={"error": str(exc)})


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError):
    return JSONResponse(
        status_code=429,
        content={"error": str(exc)},
        headers={"Retry-After": str(exc.retry_after)},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
