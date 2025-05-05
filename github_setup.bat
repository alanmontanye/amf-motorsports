@echo off
echo ======================================================
echo GitHub Setup for AMF Motorsports
echo ======================================================
echo.
echo This script will help you push your code to GitHub
echo First, please edit the .github-env file with your info
echo.
echo Press any key to open the .github-env file for editing...
pause >nul

notepad .github-env

echo.
echo Running GitHub setup script...
python github_setup.py
echo.
echo If successful, your code is now on GitHub!
echo.
pause
