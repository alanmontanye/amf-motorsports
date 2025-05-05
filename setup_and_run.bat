@echo off
echo Setting up AMF Motorsports Application
echo.

echo Step 1: Creating database tables
python create_tables.py
echo.

echo Step 2: Starting application
python -m flask run
echo.

pause
