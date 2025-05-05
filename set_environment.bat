@echo off
SETX FLASK_CONFIG "development"
echo FLASK_CONFIG environment variable set to development
echo.
echo To change to production mode, run:
echo SETX FLASK_CONFIG "production"
