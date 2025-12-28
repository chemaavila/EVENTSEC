#requires -version 5.1
Set-StrictMode -Version Latest
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root\..

Write-Host "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r build-requirements.txt
python -m pip install pyinstaller

Write-Host "Generating icons..."
python -m agent.assets.generate_icons -ErrorAction SilentlyContinue

Write-Host "Building agent worker..."
pyinstaller --noconfirm --clean eventsec-agent.spec

Write-Host "Building launcher..."
pyinstaller --noconfirm --clean eventsec-launcher.spec

Write-Host ""
Write-Host "Build complete!"
Write-Host "  Agent worker: dist\eventsec-agent.exe"
Write-Host "  Launcher: dist\eventsec-launcher.exe"
Write-Host ""
Write-Host "NOTE: For distribution, create an installer using Inno Setup or NSIS."

Pop-Location
