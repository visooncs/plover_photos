@echo off
title Update All Services
cd /d "%~dp0"
echo Rebuilding and restarting all services...
docker-compose up -d --build
pause
