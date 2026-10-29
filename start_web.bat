@echo off
title Targon Web UI
echo Starting Targon Backend Server on http://127.0.0.1:8420/ ...
start /B "" python "%~dp0backend\run_backend.py"
timeout /t 2 /nobreak >nul
echo Opening Targon in your default browser...
start http://127.0.0.1:8420/
