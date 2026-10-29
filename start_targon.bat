@echo off
title Targon — Neural Photo Library
echo ========================================================
echo   Targon: Apple-Style Neural Drive Photo Scanner
echo ========================================================
echo.

netstat -ano | findstr :8420 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  echo [1/2] Targon backend is already running on port 8420.
) else (
  echo [1/2] Starting Targon Python Neural Backend on port 8420...
  start /B "" python "%~dp0backend\run_backend.py"
  timeout /t 3 /nobreak >nul
)

echo [2/2] Launching Targon Desktop Application Window...
cd /d "%~dp0frontend"
call npm run electron

if %ERRORLEVEL% NEQ 0 (
  echo.
  echo Opening Targon in your default web browser at http://127.0.0.1:8420/ ...
  start http://127.0.0.1:8420/
)
