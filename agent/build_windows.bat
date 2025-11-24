@echo off
REM Build script for Windows executable (uses local virtualenv)
setlocal enabledelayedexpansion

echo Building EventSec Agent for Windows...

set VENV_DIR=.build-venv

python -m venv %VENV_DIR%
call %VENV_DIR%\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

pyinstaller --onefile --name eventsec-agent --console --clean agent.py

call %VENV_DIR%\Scripts\deactivate
rmdir /s /q %VENV_DIR%

copy /Y agent_config.json dist\agent_config.json >nul
echo.
echo Build complete! Executable is in the 'dist' folder: dist\eventsec-agent.exe
echo.
pause
