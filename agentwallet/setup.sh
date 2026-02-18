#!/usr/bin/env bash
# AgentWallet Protocol — One-command setup
# Usage: bash setup.sh

set -e

# ── Colors (ASCII-safe) ──────────────────────────────────────────────────────
BGREEN='\033[1;32m'
GREEN='\033[0;32m'
BCYAN='\033[1;36m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { printf "${BGREEN}[OK]${NC} %s\n" "$1"; }
warn()  { printf "${YELLOW}[!]${NC}  %s\n" "$1"; }
error() { printf "${RED}[ERR]${NC} %s\n" "$1"; exit 1; }
step()  { printf "\n${YELLOW}---- %s ----${NC}\n" "$1"; }

# ── Detect Python (verify it actually runs, not just a Windows stub) ──────────
PYTHON=""
if python3 --version >/dev/null 2>&1; then
  PYTHON=python3
elif python --version >/dev/null 2>&1; then
  PYTHON=python
fi

# ── Hacker Intro (all Unicode via Python with forced UTF-8) ──────────────────
clear

if [ -n "$PYTHON" ]; then
  PYTHONUTF8=1 PYTHONIOENCODING=utf-8 $PYTHON - <<'INTRO_EOF'
import sys, os, random, time

# Force UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

G  = "\033[1;32m"   # bright green
C  = "\033[1;36m"   # bright cyan
DIM = "\033[2m"
W  = "\033[1;37m"
Y  = "\033[1;33m"
R  = "\033[0m"      # reset

try:
    cols = os.get_terminal_size().columns
except Exception:
    cols = 80
cols = min(cols, 100)

# ── Matrix rain ──────────────────────────────────────────────────────────────
chars = "01ABCDEF0123456789#@!$%&*+-=><|"
for _ in range(5):
    line = "".join(random.choice(chars) for _ in range(cols))
    sys.stdout.write(f"{G}{line}{R}\n")
    sys.stdout.flush()
    time.sleep(0.07)
time.sleep(0.2)
print()

# ── Banner: AGENT (bright green) ─────────────────────────────────────────────
agent_art = [
    "    \u2588\u2588\u2588\u2588\u2588\u256d\u2500  \u2588\u2588\u2588\u2588\u2588\u2588\u256d \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u256d\u2588\u2588\u2588\u256d   \u2588\u2588\u256d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u256d",
    "   \u2588\u2588\u256f\u2500\u2500\u2588\u2588\u256d\u2588\u2588\u256f\u2550\u2550\u2550\u2550\u256d \u2588\u2588\u256f\u2550\u2550\u2550\u2550\u256d\u2588\u2588\u2588\u2588\u256d  \u2588\u2588\u256d\u255a\u2550\u2550\u2588\u2588\u256f\u2550\u2550\u256d",
    "   \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u256d\u2588\u2588\u256d  \u2588\u2588\u2588\u256d\u2588\u2588\u2588\u2588\u2588\u256d  \u2588\u2588\u256f\u2588\u2588\u256d \u2588\u2588\u256d   \u2588\u2588\u256d   ",
    "   \u2588\u2588\u256f\u2500\u2500\u2588\u2588\u256d\u2588\u2588\u256d   \u2588\u2588\u256d\u2588\u2588\u256f\u2500\u2500\u256d  \u2588\u2588\u256d\u255a\u2588\u2588\u256d   \u2588\u2588\u256d   ",
    "   \u2588\u2588\u256d  \u2588\u2588\u256d\u255a\u2588\u2588\u2588\u2588\u2588\u2588\u256f\u256d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u256d\u2588\u2588\u256d \u255a\u2588\u2588\u2588\u2588\u256d   \u2588\u2588\u256d   ",
    "   \u255a\u2550\u256d  \u255a\u2550\u256d \u255a\u2550\u2550\u2550\u2550\u2550\u256f \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u256d\u255a\u2550\u256d  \u255a\u2550\u2550\u2550\u256d   \u255a\u2550\u256d   ",
]
for line in agent_art:
    print(f"{G}  {line}{R}")

print()

# ── Banner: WALLET (bright cyan) ─────────────────────────────────────────────
wallet_art = [
    "   \u2588\u2588\u256d    \u2588\u2588\u256d \u2588\u2588\u2588\u2588\u2588\u256d \u2588\u2588\u256d     \u2588\u2588\u256d     \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u256d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u256d",
    "   \u2588\u2588\u256d    \u2588\u2588\u256d\u2588\u2588\u256f\u2500\u2500\u2588\u2588\u256d\u2588\u2588\u256d     \u2588\u2588\u256d     \u2588\u2588\u256f\u2550\u2550\u2550\u2550\u256d\u255a\u2550\u2550\u2588\u2588\u256f\u2500\u2500\u256d",
    "   \u2588\u2588\u256d \u2588\u256d \u2588\u2588\u256d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u256d\u2588\u2588\u256d     \u2588\u2588\u256d     \u2588\u2588\u2588\u2588\u2588\u256d     \u2588\u2588\u256d   ",
    "   \u2588\u2588\u256d\u2588\u2588\u2588\u256d\u2588\u2588\u256d\u2588\u2588\u256f\u2500\u2500\u2588\u2588\u256d\u2588\u2588\u256d     \u2588\u2588\u256d     \u2588\u2588\u256f\u2500\u2500\u256d     \u2588\u2588\u256d   ",
    "   \u255a\u2588\u2588\u2588\u256f\u2588\u2588\u2588\u256f\u2588\u2588\u256d  \u2588\u2588\u256d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u256d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u256d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u256d   \u2588\u2588\u256d   ",
    "    \u255a\u2550\u2550\u256d\u255a\u2550\u2550\u256d \u255a\u2550\u256d  \u255a\u2550\u256d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u256d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u256d\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u256d   \u255a\u2550\u256d   ",
]
for line in wallet_art:
    print(f"{C}  {line}{R}")

print()

# ── Tagline box ───────────────────────────────────────────────────────────────
box_w = 61
line  = "\u2500" * box_w
print(f"{DIM}   \u250c{line}\u2510{R}")
print(f"{DIM}   \u2502{R}  {G}Give your AI agent a wallet.{R}                             {DIM}\u2502{R}")
print(f"{DIM}   \u2502{R}  {DIM}Solana \u00b7 Escrow \u00b7 ACP \u00b7 Swarms \u00b7 v0.4.0 \u00b7 MIT{R}           {DIM}\u2502{R}")
print(f"{DIM}   \u2502{R}  {C}https://agentwallet.fun{R}  \u00b7  {DIM}https://api.agentwallet.fun{R}  {DIM}\u2502{R}")
print(f"{DIM}   \u2514{line}\u2518{R}")
print()
INTRO_EOF

else
  # Python not found — plain ASCII fallback
  printf "\n  === AGENTWALLET PROTOCOL v0.4.0 ===\n"
  printf "  Give your AI agent a wallet.\n"
  printf "  https://agentwallet.fun\n\n"
fi

sleep 0.3

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

command -v curl >/dev/null 2>&1 || warn "curl not found -- health check will be skipped"

# ── Step 2: Create .env ──────────────────────────────────────────────────────
step "Setting up environment"

if [ -f .env ]; then
  warn ".env already exists -- skipping (delete it and re-run to reset)"
else
  cp .env.example .env
  info "Copied .env.example -> .env"

  $PYTHON - <<'PYEOF'
import secrets, sys

jwt_secret = secrets.token_hex(32)

try:
    from cryptography.fernet import Fernet
    fernet_key = Fernet.generate_key().decode()
except ImportError:
    import base64, os
    fernet_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    print("  (cryptography not installed -- used fallback key generator)")

content = open('.env').read()
content = content.replace('change-me-in-production', jwt_secret)
content = content.replace('ENCRYPTION_KEY=', f'ENCRYPTION_KEY={fernet_key}')
open('.env', 'w').write(content)
print(f"  JWT_SECRET_KEY  -> {jwt_secret[:8]}... (auto-generated)")
print(f"  ENCRYPTION_KEY  -> {fernet_key[:8]}... (auto-generated)")
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
      printf "\n"
      info "API is up!"
      break
    fi
  fi
  printf "."
  sleep 2
  ELAPSED=$((ELAPSED + 2))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
  printf "\n"
  warn "API not responding after ${MAX_WAIT}s -- run: docker compose logs api"
fi

# ── Done ─────────────────────────────────────────────────────────────────────
printf "\n${BGREEN}"
printf "   +------------------------------------------------------+\n"
printf "   |           [OK]  Setup Complete!                      |\n"
printf "   +------------------------------------------------------+\n"
printf "   |  API   ->  http://localhost:8000                     |\n"
printf "   |  Docs  ->  http://localhost:8000/docs                |\n"
printf "   +------------------------------------------------------+\n"
printf "   |  make start  -> start services                       |\n"
printf "   |  make stop   -> stop services                        |\n"
printf "   |  make logs   -> view API logs                        |\n"
printf "   |  make test   -> run 110 tests                        |\n"
printf "   +------------------------------------------------------+\n"
printf "${NC}\n"
printf "   Next -> curl http://localhost:8000/health\n"
printf "   Docs -> README.md (Option B) for step-by-step usage\n\n"
