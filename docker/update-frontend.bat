@echo off
title Plover Photos - Frontend Rebuild & Update
cd /d "%~dp0"

echo ==========================================
echo    Plover Photos - Frontend Updater
echo ==========================================
echo.
echo Rebuilding and deploying frontend container...
echo This will run: docker compose up -d --build frontend
echo.

docker compose up -d --build frontend

echo.
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Frontend updated successfully!
) else (
    echo [ERROR] Frontend update failed.
)
echo.
echo ==========================================
pause
