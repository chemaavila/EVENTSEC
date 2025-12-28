# Smoke test for agent (Windows)

$ErrorActionPreference = "Stop"

Push-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)\..

Write-Host "Running smoke test..."

# Run agent with --run-once
Write-Host "Running agent --run-once..."
python -m agent.agent --run-once
if ($LASTEXITCODE -ne 0) {
    python agent\agent.py --run-once
}

# Check status.json exists
$statusFile = python -c "from agent.os_paths import get_status_path; print(get_status_path())"
if (Test-Path $statusFile) {
    Write-Host "✓ status.json created at $statusFile"
    Get-Content $statusFile
} else {
    Write-Host "✗ status.json not found at $statusFile"
    exit 1
}

# Check log file exists
$logFile = python -c "from agent.os_paths import get_logs_path; print(get_logs_path())"
if (Test-Path $logFile) {
    Write-Host "✓ log file created at $logFile"
    Write-Host "Last 10 lines:"
    Get-Content $logFile -Tail 10
} else {
    Write-Host "✗ log file not found at $logFile"
    exit 1
}

# Test healthcheck
Write-Host ""
Write-Host "Testing healthcheck..."
python -m agent.agent --healthcheck
if ($LASTEXITCODE -ne 0) {
    python agent\agent.py --healthcheck
}

Write-Host ""
Write-Host "Smoke test passed!"

Pop-Location

