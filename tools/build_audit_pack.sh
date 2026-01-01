#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p audit_inputs/{schemas,events_raw,events_normalized,docs,rules,metrics,repo,edr}

python3 tools/export_opensearch_schema.py
python3 tools/export_event_samples.py
python3 tools/generate_mapping_from_examples.py
python3 tools/export_rules.py
python3 tools/export_metrics.py
python3 tools/export_edr_audit_logs.py

if [[ ! -s audit_inputs/metrics/metrics_ingest.json ]]; then
  echo "No runtime metrics found; generating synthetic dataset and expected outputs."
  python3 tools/generate_synthetic_dataset.py
fi

echo "Audit pack generation complete."
