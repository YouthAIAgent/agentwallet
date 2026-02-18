#!/usr/bin/env bash
# AgentWallet Protocol — One-command setup for new contributors
# Usage: bash setup.sh

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

info()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }
step()    { echo -e "\n${YELLOW}──── $1 ────${NC}"; }

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   AgentWallet Protocol — Setup       ║"
echo "║   Give your AI agent a wallet        ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── Step 1: Check prerequisites ────────────────────────────────────────────────
step "Checking prerequisites"

command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1 \
  || error "Python 3.10+ not found. Install from https://python.org"

PYTHON=$(command -v python3 2>/dev/null || command -v python)
PY_VER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python $PY_VER found"

command -v docker >/dev/null 2>&1 \
  || error "Docker not found. Install Docker Desktop from https://www.docker.com/products/docker-desktop"

docker info >/dev/null 2>&1 \
  || error "Docker is not running. Please start Docker Desktop and try again."

info "Docker is running"

command -v curl >/dev/null 2>&1 || warn "curl not found — health check will be skipped"

# ── Step 2: Create .env ─────────────────────────────────────────────────────────
step "Setting up environment"

if [ -f .env ]; then
  warn ".env already exists — skipping (delete it and re-run to reset)"
else
  cp .env.example .env
  info "Copied .env.example → .env"

  # Auto-generate secrets
  $PYTHON - <<'PYEOF'
import sys

# Generate JWT secret
import secrets
jwt_secret = secrets.token_hex(32)

# Generate Fernet key
try:
    from cryptography.fernet import Fernet
    fernet_key = Fernet.generate_key().decode()
except ImportError:
    import base64, os
    fernet_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    print("  (cryptography not installed — used fallback key generator)")

content = open('.env').read()
content = content.replace('change-me-in-production', jwt_secret)
content = content.replace('ENCRYPTION_KEY=', f'ENCRYPTION_KEY={fernet_key}')
open('.env', 'w').write(content)
print(f"  JWT_SECRET_KEY  → {jwt_secret[:8]}... (auto-generated)")
print(f"  ENCRYPTION_KEY  → {fernet_key[:8]}... (auto-generated)")
PYEOF
  info "Secrets auto-generated"
fi

# ── Step 3: Start services ──────────────────────────────────────────────────────
step "Starting services (API + PostgreSQL + Redis)"

# Only start core services — skip dashboard (requires Node build)
docker compose up -d postgres redis api 2>&1 | tail -5

info "Containers started"

# ── Step 4: Wait for API ────────────────────────────────────────────────────────
step "Waiting for API to be ready"

MAX_WAIT=60
ELAPSED=0
printf "  Waiting"
while [ $ELAPSED -lt $MAX_WAIT ]; do
  if command -v curl >/dev/null 2>&1; then
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || true)
    if [ "$STATUS" = "200" ]; then
      echo ""
      info "API is up!"
      break
    fi
  fi
  printf "."
  sleep 2
  ELAPSED=$((ELAPSED + 2))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
  echo ""
  warn "API not responding after ${MAX_WAIT}s — check logs with: docker compose logs api"
fi

# ── Step 5: Show result ─────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║              Setup Complete!                 ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  API:   http://localhost:8000                ║"
echo "║  Docs:  http://localhost:8000/docs           ║"
echo "║  Health:http://localhost:8000/health         ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  Quick commands:                             ║"
echo "║    make start   → start all services         ║"
echo "║    make stop    → stop all services          ║"
echo "║    make logs    → view API logs              ║"
echo "║    make test    → run 110 tests              ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  Next: curl http://localhost:8000/health"
echo "  See README.md → Option B for step-by-step API usage"
echo ""
