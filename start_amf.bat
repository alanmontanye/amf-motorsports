@echo off
cd /d "%~dp0"
start /b pythonw desktop_app.py
timeout /t 2 /nobreak > nul
start http://localhost:5000
