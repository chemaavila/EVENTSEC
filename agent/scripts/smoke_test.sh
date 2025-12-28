#!/usr/bin/env bash
# Smoke test for agent (macOS/Linux)

set -euo pipefail

cd "$(dirname "$0")/.."

echo "Running smoke test..."

# Run agent with --run-once
echo "Running agent --run-once..."
python -m agent.agent --run-once || python agent/agent.py --run-once

# Check status.json exists
STATUS_FILE=$(python -c "from agent.os_paths import get_status_path; print(get_status_path())")
if [ -f "$STATUS_FILE" ]; then
    echo "✓ status.json created at $STATUS_FILE"
    cat "$STATUS_FILE"
else
    echo "✗ status.json not found at $STATUS_FILE"
    exit 1
fi

# Check log file exists
LOG_FILE=$(python -c "from agent.os_paths import get_logs_path; print(get_logs_path())")
if [ -f "$LOG_FILE" ]; then
    echo "✓ log file created at $LOG_FILE"
    echo "Last 10 lines:"
    tail -n 10 "$LOG_FILE"
else
    echo "✗ log file not found at $LOG_FILE"
    exit 1
fi

# Test healthcheck
echo ""
echo "Testing healthcheck..."
python -m agent.agent --healthcheck || python agent/agent.py --healthcheck

echo ""
echo "Smoke test passed!"

