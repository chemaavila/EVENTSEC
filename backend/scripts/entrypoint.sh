diff --git a/backend/scripts/entrypoint.sh b/backend/scripts/entrypoint.sh
index e94d2e3..ee6e8cf 100755
--- a/backend/scripts/entrypoint.sh
+++ b/backend/scripts/entrypoint.sh
@@ -16,6 +16,13 @@ else
   exit 1
 fi
 
+export PYTHONPATH="$PWD"
+
+if [[ -z "${JWT_SECRET:-}" && -z "${SECRET_KEY:-}" ]]; then
+  log "ERROR: Missing JWT_SECRET or SECRET_KEY"
+  exit 1
+fi
+
 if [[ -n "${DATABASE_URL:-}" ]]; then
   scheme="${DATABASE_URL%%:*}"
   normalized="$DATABASE_URL"
@@ -40,7 +47,8 @@ if [[ "${EVENTSEC_DB_FORCE_PUBLIC:-}" == "1" ]]; then
 fi
 
 log "RUN_MIGRATIONS=${RUN_MIGRATIONS:-<unset>}"
-log "PORT=${PORT:-8000}"
+log "RUN_MIGRATIONS_ON_START=${RUN_MIGRATIONS_ON_START:-<unset>}"
+log "PORT=${PORT:-10000}"
 
 if [[ -z "${DATABASE_URL:-}" ]]; then
   log "ERROR: DATABASE_URL is required for startup"
@@ -83,33 +91,29 @@ truthy() {
 }
 
 should_migrate=false
-if truthy "${RUN_MIGRATIONS:-}"; then
+if truthy "${RUN_MIGRATIONS_ON_START:-}"; then
+  should_migrate=true
+elif truthy "${RUN_MIGRATIONS:-}"; then
+  should_migrate=true
+elif [[ -z "${RUN_MIGRATIONS_ON_START:-}" && -z "${RUN_MIGRATIONS:-}" ]]; then
   should_migrate=true
 fi
 
-missing_tables=$(python - <<'PY'
+get_missing_tables() {
+  python - <<'PY'
 import os
-from sqlalchemy import create_engine, text
+from sqlalchemy import create_engine
+
+from app import database
 
-required = [
-    "public.alembic_version",
-    "public.users",
-    "public.pending_events",
-    "public.detection_rules",
-]
 engine = create_engine(os.environ["DATABASE_URL"], future=True)
-missing = []
 with engine.connect() as conn:
-    for table in required:
-        exists = conn.execute(
-            text("SELECT to_regclass(:table_name)"),
-            {"table_name": table},
-        ).scalar()
-        if exists is None:
-            missing.append(table)
+    missing = database.get_missing_tables(conn)
 print(",".join(missing))
 PY
-) || missing_tables=""
+}
+
+missing_tables="$(get_missing_tables 2>/dev/null || true)"
 
 if [[ -n "$missing_tables" ]]; then
   log "Detected missing tables: ${missing_tables}"
@@ -128,36 +132,33 @@ if [[ "$should_migrate" == true ]]; then
     exit 1
   fi
   log "Alembic migrations finished"
-  log_db_identity
-  post_missing_tables=$(python - <<'PY'
+  post_missing_tables="$(get_missing_tables 2>/dev/null || true)"
+  if [[ -n "$post_missing_tables" ]]; then
+    log "ERROR: missing tables after migrations: ${post_missing_tables}"
+    exit 1
+  fi
+else
+  log "Skipping migrations"
+fi
+
+if [[ -n "${EVENTSEC_DB_DEBUG:-}" ]]; then
+  log "DB debug enabled; printing connection identity"
+  python - <<'PY'
 import os
 from sqlalchemy import create_engine, text
 
-required = [
-    "public.alembic_version",
-    "public.users",
-    "public.pending_events",
-    "public.detection_rules",
-]
 engine = create_engine(os.environ["DATABASE_URL"], future=True)
-missing = []
 with engine.connect() as conn:
-    for table in required:
-        exists = conn.execute(
-            text("SELECT to_regclass(:table_name)"),
-            {"table_name": table},
-        ).scalar()
-        if exists is None:
-            missing.append(table)
-print(",".join(missing))
+    row = conn.execute(
+        text(
+            "SELECT current_database() AS db, current_user AS user, "
+            "inet_server_addr() AS server_addr, inet_server_port() AS server_port, "
+            "current_setting('search_path') AS search_path"
+        )
+    ).mappings().first()
+    print(f"[entrypoint][db-debug] {row}")
 PY
-  ) || post_missing_tables=""
-  if [[ -n "$post_missing_tables" ]]; then
-    log "Warning: missing tables after migrations: ${post_missing_tables}"
-  fi
-else
-  log "Skipping migrations"
 fi
 
 log "Starting app"
-exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
+exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
diff --git a/backend/scripts/render_start.sh b/backend/scripts/render_start.sh
index fd0864e..7b585e1 100755
--- a/backend/scripts/render_start.sh
+++ b/backend/scripts/render_start.sh
@@ -5,130 +5,5 @@ log() {
   echo "[render-start] $*"
 }
 
-require_env() {
-  local name="$1"
-  if [[ -z "${!name:-}" ]]; then
-    echo "[render-start] Missing required env: $name" >&2
-    exit 1
-  fi
-}
-
-export PYTHONPATH="$PWD"
-
-require_env "DATABASE_URL"
-if [[ -z "${JWT_SECRET:-}" && -z "${SECRET_KEY:-}" ]]; then
-  echo "[render-start] Missing JWT_SECRET or SECRET_KEY" >&2
-  exit 1
-fi
-
-if [[ -n "${DATABASE_URL:-}" ]]; then
-  scheme="${DATABASE_URL%%:*}"
-  normalized="$DATABASE_URL"
-  if [[ "$DATABASE_URL" == postgres://* ]]; then
-    normalized="postgresql+psycopg2://${DATABASE_URL#postgres://}"
-  elif [[ "$DATABASE_URL" == postgresql://* && "$DATABASE_URL" != postgresql+* ]]; then
-    normalized="postgresql+psycopg2://${DATABASE_URL#postgresql://}"
-  fi
-  export DATABASE_URL="$normalized"
-  normalized_scheme="${DATABASE_URL%%:*}"
-  if [[ "$scheme" != "$normalized_scheme" ]]; then
-    log "Normalized DATABASE_URL scheme (${scheme} -> ${normalized_scheme})"
-  fi
-fi
-
-if [[ "${EVENTSEC_DB_FORCE_PUBLIC:-}" == "1" ]]; then
-  export PGOPTIONS="--search_path=public"
-  log "EVENTSEC_DB_FORCE_PUBLIC=1; setting PGOPTIONS=--search_path=public"
-fi
-
-RUN_MIGRATIONS_ON_START="${RUN_MIGRATIONS_ON_START:-true}"
-if [[ "${RUN_MIGRATIONS_ON_START}" == "true" ]]; then
-  log "Running database migrations and table verification"
-else
-  log "RUN_MIGRATIONS_ON_START=${RUN_MIGRATIONS_ON_START}; skipping migrations"
-fi
-
-python - <<'PY'
-...
-PY
-fi
-
-if [[ -n "${EVENTSEC_DB_DEBUG:-}" ]]; then
-  log "DB debug enabled; printing connection identity"
-  python - <<'PY'
-...
-PY
-fi
-
-log "Starting EventSec backend on port ${PORT:-8000}"
-exec uvicorn app.main:app \
-  --host 0.0.0.0 \
-  --port "${PORT:-8000}" \
-  --proxy-headers \
-  --forwarded-allow-ips="*"
+log "Delegating Render start to scripts/entrypoint.sh"
+exec bash scripts/entrypoint.sh
