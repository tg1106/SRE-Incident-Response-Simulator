#!/usr/bin/env bash
set -uo pipefail

DOCKER_BUILD_TIMEOUT=600
if [ -t 1 ]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
else
  RED='' GREEN='' YELLOW='' BOLD='' NC=''
fi

PING_URL="${1:-}"
REPO_DIR="${2:-.}"

if [ -z "$PING_URL" ]; then printf "Usage: %s <ping_url> [repo_dir]\n" "$0"; exit 1; fi
if ! REPO_DIR="$(cd "$REPO_DIR" 2>/dev/null && pwd)"; then printf "Error: directory not found\n"; exit 1; fi

PING_URL="${PING_URL%/}"
PASS=0

log()  { printf "[%s] %b\n" "$(date -u +%H:%M:%S)" "$*"; }
pass() { log "${GREEN}PASSED${NC} -- $1"; PASS=$((PASS + 1)); }
fail() { log "${RED}FAILED${NC} -- $1"; }
hint() { printf "  ${YELLOW}Hint:${NC} %b\n" "$1"; }
stop_at() { printf "\n${RED}${BOLD}Stopped at %s.${NC}\n" "$1"; exit 1; }

printf "\n${BOLD}========================================${NC}\n"
printf "${BOLD}  OpenEnv Submission Validator${NC}\n"
printf "${BOLD}========================================${NC}\n"
log "Repo: $REPO_DIR"
log "Ping: $PING_URL"
printf "\n"

log "${BOLD}Step 1/3: Pinging HF Space${NC} ($PING_URL/reset) ..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" -d '{}' \
  "$PING_URL/reset" --max-time 30 || printf "000")

if [ "$HTTP_CODE" = "200" ]; then pass "HF Space is live and responds to /reset"
elif [ "$HTTP_CODE" = "000" ]; then fail "HF Space not reachable"; stop_at "Step 1"
else fail "HF Space /reset returned HTTP $HTTP_CODE"; stop_at "Step 1"
fi

log "${BOLD}Step 2/3: Running docker build${NC} ..."
if ! command -v docker &>/dev/null; then fail "docker not found — install Docker Desktop"; stop_at "Step 2"; fi

if [ -f "$REPO_DIR/Dockerfile" ]; then DOCKER_CONTEXT="$REPO_DIR"
elif [ -f "$REPO_DIR/server/Dockerfile" ]; then DOCKER_CONTEXT="$REPO_DIR/server"
else fail "No Dockerfile found"; stop_at "Step 2"
fi

log "  Found Dockerfile in $DOCKER_CONTEXT"
if docker build "$DOCKER_CONTEXT" 2>&1; then pass "Docker build succeeded"
else fail "Docker build failed"; stop_at "Step 2"
fi

log "${BOLD}Step 3/3: Running openenv validate${NC} ..."
if ! command -v openenv &>/dev/null; then fail "openenv not found — run: pip install openenv-core"; stop_at "Step 3"; fi

if (cd "$REPO_DIR" && openenv validate 2>&1); then pass "openenv validate passed"
else fail "openenv validate failed"; stop_at "Step 3"
fi

printf "\n${BOLD}========================================${NC}\n"
printf "${GREEN}${BOLD}  All 3/3 checks passed!${NC}\n"
printf "${GREEN}${BOLD}  Your submission is ready to submit.${NC}\n"
printf "${BOLD}========================================${NC}\n\n"
exit 0
