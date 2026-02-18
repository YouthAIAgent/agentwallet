#!/usr/bin/env bash
# AgentWallet Protocol — One-command setup
# Usage: bash setup.sh

set -e

# ── Colors ───────────────────────────────────────────────────────────────────
BGREEN='\033[1;32m'
GREEN='\033[0;32m'
BCYAN='\033[1;36m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
WHITE='\033[1;37m'
DIM='\033[2m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${BGREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
step()  { echo -e "\n${YELLOW}──── $1 ────${NC}"; }

# ── Detect Python ────────────────────────────────────────────────────────────
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "")

# ── Hacker Intro ─────────────────────────────────────────────────────────────
clear

# Matrix rain animation
if [ -n "$PYTHON" ]; then
  $PYTHON - <<'MATRIX_EOF'
import random, time, sys, os
try:
    cols = os.get_terminal_size().columns
except Exception:
    cols = 80
cols = min(cols, 100)
chars = "01アイウエオカキクケコABCDEF0123456789▓▒░"
for _ in range(5):
    line = "".join(random.choice(chars) for _ in range(cols))
    sys.stdout.write(f"\033[0;32m{line}\033[0m\n")
    sys.stdout.flush()
    time.sleep(0.07)
time.sleep(0.2)
MATRIX_EOF
fi

# ── Banner: AGENT (bright green) ─────────────────────────────────────────────
echo -e "${BGREEN}"
echo "    █████╗  ██████╗ ███████╗███╗   ██╗████████╗"
echo "   ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝"
echo "   ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   "
echo "   ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   "
echo "   ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   "
echo "   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   "

# ── Banner: WALLET (bright cyan) ─────────────────────────────────────────────
echo -e "${BCYAN}"
echo "   ██╗    ██╗ █████╗ ██╗     ██╗     ███████╗████████╗"
echo "   ██║    ██║██╔══██╗██║     ██║     ██╔════╝╚══██╔══╝"
echo "   ██║ █╗ ██║███████║██║     ██║     █████╗     ██║   "
echo "   ██║███╗██║██╔══██║██║     ██║     ██╔══╝     ██║   "
echo "   ╚███╔███╔╝██║  ██║███████╗███████╗███████╗   ██║   "
echo "    ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝   ╚═╝   "
echo -e "${NC}"

# ── Tagline box ───────────────────────────────────────────────────────────────
echo -e "   ${DIM}┌─────────────────────────────────────────────────────────┐${NC}"
echo -e "   ${DIM}│${NC}  ${BGREEN}Give your AI agent a wallet.${NC}                            ${DIM}│${NC}"
echo -e "   ${DIM}│${NC}  ${DIM}Solana · Escrow · ACP · Swarms · v0.4.0 · MIT License${NC}  ${DIM}│${NC}"
echo -e "   ${DIM}│${NC}  ${CYAN}https://agentwallet.fun${NC}  ${DIM}·  https://api.agentwallet.fun${NC}  ${DIM}│${NC}"
echo -e "   ${DIM}└─────────────────────────────────────────────────────────┘${NC}"
echo ""
sleep 0.4

# ── Step 1: Check prerequisites ──────────────────────────────────────────────
step "Checking prerequisites"

[ -n "$PYTHON" ] \
  || error "Python 3.10+ not found. Install from https://python.org"

PY_VER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python $PY_VER found"

command -v docker >/dev/null 2>&1 \
  || error "Docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop"

docker info >/dev/null 2>&1 \
  || error "Docker is not running. Start Docker Desktop and try again."

info "Docker is running"

command -v curl >/dev/null 2>&1 || warn "curl not found — health check will be skipped"

# ── Step 2: Create .env ──────────────────────────────────────────────────────
step "Setting up environment"

if [ -f .env ]; then
  warn ".env already exists — skipping (delete it and re-run to reset)"
else
  cp .env.example .env
  info "Copied .env.example → .env"

  $PYTHON - <<'PYEOF'
import secrets, sys

jwt_secret = secrets.token_hex(32)

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

# ── Step 3: Start services ───────────────────────────────────────────────────
step "Starting services (API + PostgreSQL + Redis)"

docker compose up -d postgres redis api 2>&1 | tail -5

info "Containers started"

# ── Step 4: Wait for API ─────────────────────────────────────────────────────
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
  warn "API not responding after ${MAX_WAIT}s — run: docker compose logs api"
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BGREEN}"
echo "   ╔══════════════════════════════════════════════════════╗"
echo "   ║             ✓  Setup Complete!                       ║"
echo "   ╠══════════════════════════════════════════════════════╣"
echo -e "   ║  ${BCYAN}API   ${BGREEN}→  http://localhost:8000                       ║"
echo -e "   ║  ${BCYAN}Docs  ${BGREEN}→  http://localhost:8000/docs                  ║"
echo "   ╠══════════════════════════════════════════════════════╣"
echo -e "   ║  ${YELLOW}make start${BGREEN}  → start services                         ║"
echo -e "   ║  ${YELLOW}make stop${BGREEN}   → stop services                          ║"
echo -e "   ║  ${YELLOW}make logs${BGREEN}   → view API logs                          ║"
echo -e "   ║  ${YELLOW}make test${BGREEN}   → run 110 tests                          ║"
echo "   ╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo "   Next → curl http://localhost:8000/health"
echo "   Docs → README.md (Option B) for step-by-step usage"
echo ""
