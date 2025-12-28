@echo off
REM Build script for Windows executable (uses local virtualenv)
setlocal enabledelayedexpansion

echo Building EventSec Agent for Windows...

set VENV_DIR=.build-venv

python -m venv %VENV_DIR%
call %VENV_DIR%\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r build-requirements.txt
python -m pip install -r requirements.txt
python -m pip install pyinstaller

python scripts/generate_icons.py

pyinstaller --noconfirm eventsec-agent.spec

call %VENV_DIR%\Scripts\deactivate
rmdir /s /q %VENV_DIR%

if exist dist\eventsec-agent.exe (
  copy /Y agent_config.json dist\agent_config.json >nul
)

echo.
echo Build complete! Double-click dist\eventsec-agent.exe to run the agent.
echo.
pause
