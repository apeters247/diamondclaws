@echo off
title DiamondClaws Server
cd /d "%~dp0"

echo Loading environment...
for /f "usebackq tokens=1,2 delims==" %%a in (".env") do set "%%a=%%b"

echo Activating venv...
call venv\Scripts\activate.bat

echo Starting DiamondClaws at http://127.0.0.1:8888
echo Press Ctrl+C to stop.
echo.
uvicorn main:app --host 127.0.0.1 --port 8888
