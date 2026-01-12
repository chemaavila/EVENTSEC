#!/usr/bin/env bash
set -u
DIR=$(cd "$(dirname "$0")" && pwd)
LOG_FILE="${DIR}/send_results.log"
: > "$LOG_FILE"
for payload in "$DIR"/*.json; do
  echo "# Sending ${payload}" | tee -a "$LOG_FILE"
  if ! "${DIR}/send_one.sh" "$payload" | tee -a "$LOG_FILE"; then
    echo "# ERROR sending ${payload}" | tee -a "$LOG_FILE"
  fi
  echo | tee -a "$LOG_FILE"
done
