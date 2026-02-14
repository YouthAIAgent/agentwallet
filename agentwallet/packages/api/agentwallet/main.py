"""FastAPI application entry point for AgentWallet Protocol."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .api.routers import (
    agents,
    analytics,
    auth,
    compliance,
    erc8004,
    escrow,
    marketplace,
    pda_wallets,
    policies,
    tokens,
    transactions,
    wallets,
    webhooks,
    x402,
)
from .core.config import get_settings
from .core.database import close_db
from .core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    ERC8004Error,
    EscrowStateError,
    EVMTransactionError,
    IdempotencyConflictError,
    InsufficientBalanceError,
    NotFoundError,
    PolicyDeniedError,
    RateLimitError,
    TierLimitError,
    TransactionFailedError,
    ValidationError,
)
from .core.logging import setup_logging
from .core.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level, settings.log_format)
    yield
    await close_db()
    await close_redis()


_settings = get_settings()
_is_prod = _settings.environment == "production"

app = FastAPI(
    title="AgentWallet Protocol",
    description="AI Agent Wallet Infrastructure on Solana",
    version="0.3.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if _is_prod:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "worker-src 'self' blob:"
            )
        return response


app.add_middleware(SecurityHeadersMiddleware)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.api_cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# Register routers under /v1
app.include_router(auth.router, prefix="/v1")
app.include_router(wallets.router, prefix="/v1")
app.include_router(agents.router, prefix="/v1")
app.include_router(transactions.router, prefix="/v1")
app.include_router(tokens.router, prefix="/v1")
app.include_router(escrow.router, prefix="/v1")
app.include_router(analytics.router, prefix="/v1")
app.include_router(compliance.router, prefix="/v1")
app.include_router(policies.router, prefix="/v1")
app.include_router(webhooks.router, prefix="/v1")
app.include_router(erc8004.router, prefix="/v1")
app.include_router(x402.router, prefix="/v1")
app.include_router(marketplace.router, prefix="/v1")
app.include_router(pda_wallets.router, prefix="/v1")


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


@app.exception_handler(ERC8004Error)
async def erc8004_error_handler(request: Request, exc: ERC8004Error):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(EVMTransactionError)
async def evm_tx_error_handler(request: Request, exc: EVMTransactionError):
    return JSONResponse(status_code=502, content={"error": str(exc)})


@app.exception_handler(TransactionFailedError)
async def tx_failed_handler(request: Request, exc: TransactionFailedError):
    return JSONResponse(status_code=502, content={"error": str(exc)})


@app.exception_handler(InsufficientBalanceError)
async def insufficient_balance_handler(request: Request, exc: InsufficientBalanceError):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(PolicyDeniedError)
async def policy_denied_handler(request: Request, exc: PolicyDeniedError):
    return JSONResponse(status_code=403, content={"error": str(exc)})


@app.exception_handler(IdempotencyConflictError)
async def idempotency_conflict_handler(request: Request, exc: IdempotencyConflictError):
    return JSONResponse(status_code=409, content={"error": str(exc)})


@app.exception_handler(EscrowStateError)
async def escrow_state_handler(request: Request, exc: EscrowStateError):
    return JSONResponse(status_code=409, content={"error": str(exc)})


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.3.0"}
