# Deploy Script for Plover Photos
$ErrorActionPreference = "Stop"

Write-Host "Checking Docker..."
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not in PATH."
}

Write-Host "Checking requirements.txt..."
$reqPath = "..\backend\requirements.txt"
if (-not (Test-Path $reqPath)) {
    Write-Error "backend/requirements.txt not found!"
}

Write-Host "Building and Starting Services..."
docker-compose -f docker-compose.yml up -d --build

if ($?) {
    Write-Host "`nDeployment Successful!" -ForegroundColor Green
    Write-Host "Frontend: http://localhost"
    Write-Host "Backend API: http://localhost:8000/api/"
    Write-Host "Admin: http://localhost:8000/admin/"
} else {
    Write-Error "Deployment failed."
}
