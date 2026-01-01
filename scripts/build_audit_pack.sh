#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p audit_inputs/{schemas,events_raw,events_normalized,docs,rules,metrics,repo,edr}

if command -v docker >/dev/null 2>&1; then
  if docker compose config >/dev/null 2>&1; then
    docker compose config > audit_inputs/repo/docker_compose_resolved.yml
  fi
fi

python3 scripts/audit/export_opensearch_schema.py
python3 scripts/audit/schema_drift_report.py

if python3 scripts/audit/export_event_samples.py; then
  python3 scripts/audit/generate_mapping.py
else
  echo "No runtime events found; generating synthetic dataset and expected outputs."
  python3 scripts/audit/generate_synthetic_dataset.py
  python3 scripts/audit/generate_mapping.py
  python3 scripts/audit/seed_opensearch.py || true
fi

python3 scripts/audit/export_rules.py
python3 scripts/audit/export_metrics.py
python3 scripts/audit/export_edr_audit_logs.py
python3 scripts/audit/validate_audit_pack.py

echo "Audit pack generation complete."
