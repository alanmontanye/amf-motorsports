@echo off
echo Starting Hours Tracking Migration...
echo.
echo This script will add hours tracking columns to your database.
echo A backup will be created before any changes are made.
echo.
echo Press Ctrl+C to cancel or any other key to continue...
pause

python migrate_hours.py

if %errorlevel% neq 0 (
    echo.
    echo Migration failed! Please check the error message above.
    echo The database was not modified or a backup was created.
) else (
    echo.
    echo Migration completed successfully!
    echo Hours tracking columns have been added to your database.
    echo.
    echo You can now use the application with hours tracking functionality.
)

echo.
pause
