#!/usr/bin/env bash
set -u

TS="$(date +%Y%m%d_%H%M%S)"
OUTDIR="${OUTDIR:-./audits}"
OUT="${OUT:-$OUTDIR/project_audit_${TS}.txt}"
TMPDIR="$(mktemp -d 2>/dev/null || mktemp -d -t eventsec_audit)"

mkdir -p "$OUTDIR"

# Mirror output to terminal + file
exec > >(tee "$OUT") 2>&1

have() { command -v "$1" >/dev/null 2>&1; }

sec() {
  echo
  echo "============================================================"
  echo "$1"
  echo "============================================================"
}

run() {
  echo
  echo "+ $*"
  "$@"
  local rc=$?
  if [ $rc -ne 0 ]; then
    echo "(exit $rc)"
  fi
  return 0
}

sec "PROJECT AUDIT REPORT"
echo "Date: $(date)"
echo "Root: $(pwd)"
echo "Output: $OUT"

sec "SYSTEM / TOOLING"
run uname -a
run sw_vers || true
run sh -lc 'echo "Shell: $SHELL"'
run git --version || true
run python3 --version || true
run node --version || true
run npm --version || true
run docker --version || true
run docker compose version || true
run rg --version || true
run tree --version || true

sec "GIT STATE"
run git rev-parse --abbrev-ref HEAD || true
run git status -sb || true
run git diff --stat || true

sec "REPO TREE (trimmed)"
if have tree; then
  run tree -a -L 4 -I "node_modules|.venv|dist|build|__pycache__|.git" .
else
  run find . -maxdepth 4 -type f | head -n 400
fi

sec "COMPOSE: CONFIG + SERVICES + PORTS"
if [ -f docker-compose.yml ]; then
  # This works even if containers are not running.
  run docker compose config > "$TMPDIR/compose_config.yml" || true

  echo
  echo "--- docker compose config (first 260 lines) ---"
  sed -n '1,260p' "$TMPDIR/compose_config.yml" || true

  echo
  echo "--- PORT MATRIX (from compose config) ---"
  # Extract published ports
  awk '
    /published:/ {gsub(/"/,"",$2); print $2}
    /- "[0-9]+:[0-9]+"/ {
      gsub(/.*- "/,""); gsub(/".*/,""); print
    }
  ' "$TMPDIR/compose_config.yml" 2>/dev/null \
  | sed 's/:/ -> /' \
  | sed 's/ -> \([0-9]\+\)$/ -> \1 (host->container)/' \
  | sort -n -u || true

else
  echo "No docker-compose.yml found."
fi

sec "DOCKER DAEMON STATUS"
if have docker; then
  run docker info >/dev/null || {
    echo "Docker daemon not reachable. Start Docker Desktop and re-run to get container inspection + integrated tests."
  }
fi

sec "COMPOSE STATUS / INSPECT (if running)"
if have docker && docker info >/dev/null 2>&1; then
  run docker compose ps || true
  IDS="$(docker compose ps -q 2>/dev/null || true)"
  if [ -n "$IDS" ]; then
    echo
    echo "--- CONTAINERS: PORTS / HEALTH / MOUNTS (summary) ---"
    for id in $IDS; do
      echo
      echo "### $id"
      docker inspect --format \
'Name={{.Name}}
Image={{.Config.Image}}
State={{.State.Status}} Health={{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}}
Ports={{json .NetworkSettings.Ports}}
Mounts={{range .Mounts}}{{.Type}}:{{.Source}} -> {{.Destination}} (ro={{.RW}}) ; {{end}}
' "$id" 2>/dev/null || true
    done

    echo
    echo "--- docker compose logs (tail 200) ---"
    run docker compose logs --tail 200 || true
  else
    echo "No compose containers running (docker compose ps -q empty)."
  fi
fi

sec "REPO PORT CLUES (code + docs, excluding big dirs)"
if have rg; then
  run rg -n --hidden --glob '!**/node_modules/**' --glob '!**/.venv/**' --glob '!**/dist/**' --glob '!**/__pycache__/**' \
    -S '(localhost|127\.0\.0\.1|0\.0\.0\.0|ws://localhost|http://localhost|--port\s+|:\s*[0-9]{2,5})' . \
    | head -n 400 || true
fi

sec "STATIC CHECKS (HOST, best-effort)"
if have python3; then
  run python3 -m compileall -q . || true
fi
if have ruff; then
  run ruff check . || true
else
  echo "ruff not available (optional)."
fi
if have bandit; then
  run bandit -r . -q || true
else
  echo "bandit not available (optional)."
fi

sec "NPM AUDIT (HOST, if frontend present)"
if [ -f frontend/package.json ] && have npm; then
  (cd frontend && run npm audit --audit-level=moderate) || true
else
  echo "No frontend/package.json or npm missing."
fi

sec "INTEGRATED TEST RUN (best-effort via Docker)"
if have docker && docker info >/dev/null 2>&1 && [ -f docker-compose.yml ]; then
  echo "Bringing up core services (opensearch, db, backend) ..."
  run docker compose up -d --build opensearch db backend || true

  echo
  echo "Waiting for OpenSearch (up to ~60s) ..."
  for i in $(seq 1 30); do
    if curl -sSf http://localhost:9200 >/dev/null 2>&1; then
      echo "OpenSearch OK"
      break
    fi
    sleep 2
  done

  echo
  echo "--- backend: migrations + pytest (if available) ---"
  run docker compose exec -T backend alembic upgrade head || true
  run docker compose exec -T backend pytest -q || true

  echo
  echo "--- frontend: build (since no test script may exist) ---"
  run docker compose up -d --build frontend || true
  run docker compose exec -T frontend npm run build || true

  echo
  echo "--- email_protection: basic import/compile (best-effort) ---"
  run docker compose up -d --build email_protection || true
  run docker compose exec -T email_protection python -m py_compile app.py || true
else
  echo "Docker not available/running or no compose file; skipping integrated tests."
fi

sec "DONE"
echo "Report saved to: $OUT"
