@echo off
echo Running database migration to add hours tracking fields...

rem Run the SQL script to alter the database
sqlite3 app.db < db_alter.sql

echo Database updated! Press any key to exit...
pause
