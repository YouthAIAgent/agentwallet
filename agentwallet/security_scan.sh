#!/usr/bin/env bash
# AgentWallet — one-command security scan
#
# Runs, in a single invocation:
#   1. gitleaks  — secret scan (working tree, git-tracked files)
#   2. bandit    — Python static analysis (api, agx, mcp-server, sdk-python)
#   3. pip-audit — Python dependency audit (audits pyproject.toml deps directly,
#                  so it is immune to whatever junk lives in the global env)
#   4. npm audit — JS dependency vulnerabilities (packages with lockfiles)
#
# Prints a green/red summary and exits non-zero if anything is RED.
#
# Usage:
#   ./security_scan.sh          # full scan
#   ./security_scan.sh quick    # skip the slow gitleaks directory scan
#
# Requires: python, bandit, pip-audit, npm. gitleaks is auto-detected
# (PATH or common install locations); if missing it is skipped with a WARN.

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

MODE="${1:-full}"
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
BOLD=$'\033[1m'
NC=$'\033[0m'

PASS=0
FAIL=0
WARN=0
RESULTS=()

ok()   { RESULTS+=("$GREEN PASS $NC $1"); PASS=$((PASS+1)); }
bad()  { RESULTS+=("$RED FAIL $NC $1");  FAIL=$((FAIL+1)); }
warn() { RESULTS+=("$YELLOW WARN $NC $1"); WARN=$((WARN+1)); }

# --- locate gitleaks ---------------------------------------------------------
find_gitleaks() {
  command -v gitleaks 2>/dev/null && return
  for p in \
    "$HOME/AppData/Local/Temp/gitleaks/gitleaks.exe" \
    "$LOCALAPPDATA/gitleaks/gitleaks.exe" \
    "/usr/local/bin/gitleaks" \
    "$HOME/go/bin/gitleaks"; do
    [ -x "$p" ] && { echo "$p"; return; }
  done
  return 1
}

# --- 1. gitleaks -------------------------------------------------------------
echo "${BOLD}== 1/4 gitleaks — secret scan ==${NC}"
GL="$(find_gitleaks)" || { warn "gitleaks: not found — skipping"; echo "     install: https://github.com/gitleaks/gitleaks/releases"; }
if [ -n "${GL:-}" ]; then
  TREE_REPORT="$LOCALAPPDATA/Temp/gl-scan-$$.json"
  if [ "$MODE" = "full" ]; then
    # full mode: scan the whole working tree (includes gitignored/venv noise, filtered below)
    "$GL" dir . --no-banner --redact -f json -r "$TREE_REPORT" >/dev/null 2>&1
  else
    # quick mode: protect = scan only uncommitted changes (staged + unstaged)
    "$GL" protect --no-banner --redact -f json -r "$TREE_REPORT" >/dev/null 2>&1
  fi
  python - "$TREE_REPORT" "$MODE" <<'PY'
import json, subprocess, sys
d = json.load(open(sys.argv[1]))
tracked = set(subprocess.check_output(["git", "ls-files"], text=True).splitlines())
live = [f for f in d if f["File"] in tracked and "node_modules" not in f["File"] and not f["File"].endswith(".pyc")]
if live:
    print("\n".join(f"  {f['File']}:{f['StartLine']} [{f['RuleID']}]" for f in live))
sys.exit(0 if not live else 1)
PY
  if [ $? -eq 0 ]; then ok "gitleaks — 0 leaks in git-tracked files"
  else bad "gitleaks — leaks found in tracked files (see above)"; fi
fi

# --- 2. bandit ---------------------------------------------------------------
echo ""
echo "${BOLD}== 2/4 bandit — Python static analysis ==${NC}"
BANDIT_JSON="$LOCALAPPDATA/Temp/bandit-scan-$$.json"
# B104 (0.0.0.0 bind) is accepted: the API runs in Docker where binding
# all interfaces is the documented, expected behaviour (see SECURITY_AUDIT.md).
python -m bandit -q --skip B104 -r packages/api/agentwallet packages/agx packages/mcp-server packages/sdk-python -f json -o "$BANDIT_JSON" 2>/dev/null
# bandit exits 1 when issues are found (that's a run, not a crash); only RC >= 2 is an error
BANDIT_RC=$?
if [ "$BANDIT_RC" -ge 2 ]; then
  bad "bandit — run failed (exit $BANDIT_RC)"
else
  python - "$BANDIT_JSON" <<'PY'
import json, sys
from collections import Counter
d = json.load(open(sys.argv[1]))
sev = Counter(r["issue_severity"] for r in d["results"])
med = [r for r in d["results"] if r["issue_severity"] in ("MEDIUM", "HIGH")]
for r in med:
    print(f"  {r['filename'].split('packages')[-1]}:{r['line_number']} [{r['test_id']}] {r['issue_text'][:70]}")
print(f"  issues: {len(d['results'])}  ({', '.join(f'{n} {k}' for k, n in sev.items()) or 'clean'})")
sys.exit(1 if med else 0)
PY
  if [ $? -eq 0 ]; then ok "bandit — no HIGH/MEDIUM issues"
  else bad "bandit — HIGH/MEDIUM issues found (see above)"; fi
fi

# --- 3. pip-audit (audits pyproject deps, not the global env) ----------------
echo ""
echo "${BOLD}== 3/4 pip-audit — Python dependencies (from pyproject.toml) ==${NC}"
REQ_TMP="$LOCALAPPDATA/Temp/aw-reqs-$$.txt"
python - "$REQ_TMP" <<'PY'
import re, sys
text = open("pyproject.toml", encoding="utf-8").read()
# deps live as `dependencies = [ ... ]` inside the [project] table
m = re.search(r"^dependencies\s*=\s*\[(.*?)\]", text, re.S | re.M)
deps = re.findall(r'"([^"]+)"', m.group(1)) if m else []
with open(sys.argv[1], "w") as f:
    for d in deps:
        # strip extras like [cryptography] and inline comments
        d = re.sub(r"\[[^\]]*\]", "", d).split("#")[0].strip()
        if d:
            f.write(d + "\n")
PY
if [ -s "$REQ_TMP" ]; then
  PIP_OUT="$(pip-audit -r "$REQ_TMP" 2>&1)"
  if echo "$PIP_OUT" | grep -qiE "No known vulnerabilities"; then
    ok "pip-audit — no known vulnerabilities in declared deps"
  else
    echo "$PIP_OUT" | grep -iE "vulnerab|PYSEC|GHSA|Fix Versions|^\S+\s+\S+\s+PYSEC" | head -15
    bad "pip-audit — vulnerabilities found in declared deps"
  fi
else
  warn "pip-audit — could not extract dependencies from pyproject.toml"
fi

# --- 4. npm audit ------------------------------------------------------------
echo ""
echo "${BOLD}== 4/4 npm audit — JS dependencies ==${NC}"
NPM_SCANNED=0
for pkg in packages/dashboard packages/sdk-ts packages/video; do
  [ -f "$pkg/package-lock.json" ] || continue
  NPM_SCANNED=1
  OUT="$(cd "$pkg" && npm audit 2>&1)"
  if echo "$OUT" | grep -qE "found 0 vulnerabilities"; then
    ok "npm audit ($pkg) — 0 vulnerabilities"
  else
    SEV=$(echo "$OUT" | grep -oiE "[0-9]+ (low|moderate|high|critical) severity" | sort -u | tr '\n' ', ' | sed 's/, $//')
    if [ -z "$SEV" ]; then
      SEV="found $(echo "$OUT" | grep -oE "found [0-9]+ vulnerabilit" | head -1)"
    fi
    if echo "$SEV" | grep -qiE "moderate|high|critical|found [1-9]"; then
      echo "  $pkg: $SEV"
      bad "npm audit ($pkg) — $SEV"
    else
      echo "  $pkg: $SEV (low only)"
      warn "npm audit ($pkg) — $SEV"
    fi
  fi
done
[ "$NPM_SCANNED" -eq 0 ] && warn "npm audit — no lockfile packages found"

# --- summary -----------------------------------------------------------------
echo ""
echo "${BOLD}========================== SUMMARY ==========================${NC}"
for r in "${RESULTS[@]}"; do echo "  $r"; done
echo "==============================================================="
echo ""
if [ "$FAIL" -gt 0 ]; then
  echo "${RED}${BOLD}RESULT: $FAIL FAIL, $PASS PASS, $WARN WARN — fix the issues above.${NC}"
  exit 1
else
  echo "${GREEN}${BOLD}RESULT: ALL GREEN — $PASS PASS, $WARN WARN. Safe to ship.${NC}"
  exit 0
fi
