$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Definition)
$DistDir = Join-Path $Root "..\agent\dist"
$BinDir = Join-Path $Root "bin"
$ConfigSrc = Join-Path $Root "agent_config.example.json"

if (!(Test-Path $DistDir)) {
    Write-Error "[agent-share] No build artifacts found in $DistDir. Run build_windows.bat first."
}

if (Test-Path $BinDir) {
    Remove-Item $BinDir -Recurse -Force
}
New-Item $BinDir -ItemType Directory | Out-Null

$copied = $false
Get-ChildItem -Path $DistDir -Filter "eventsec-agent*" | ForEach-Object {
    Copy-Item $_.FullName -Destination $BinDir -Recurse -Force
    $copied = $true
}

if (-not $copied) {
    Write-Error "[agent-share] No eventsec-agent binaries found in $DistDir"
}

Copy-Item $ConfigSrc (Join-Path $BinDir "agent_config.json")
Write-Output "[agent-share] Shareable bundle ready in $BinDir"


