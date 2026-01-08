# Plover Photos Startup Script
# Encoding: UTF-8 with BOM

$root = $PSScriptRoot
if (-not $root) { $root = Get-Location }

# Set Encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "--- Plover Photos Starting ---" -ForegroundColor Cyan

# 1. Backend Check
Write-Host "Checking Backend..." -ForegroundColor Yellow
$backendDir = Join-Path $root "backend"
if (-not (Test-Path (Join-Path $backendDir ".env"))) {
    Write-Host "Warning: .env not found in backend folder" -ForegroundColor Red
}

# Detect Virtual Environment
$venvPython = "python" # Default to system python
$possibleVenvs = @(
    "$root\.venv\Scripts\python.exe",
    "$root\venv\Scripts\python.exe",
    "$backendDir\.venv\Scripts\python.exe",
    "$backendDir\venv\Scripts\python.exe"
)

foreach ($path in $possibleVenvs) {
    if (Test-Path $path) {
        $venvPython = $path
        Write-Host "Found Virtual Environment: $path" -ForegroundColor Green
        break
    }
}

# 2. Frontend Check
Write-Host "Checking Frontend..." -ForegroundColor Yellow
$frontendDir = Join-Path $root "frontend"
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
    Start-Process npm -ArgumentList "install" -WorkingDirectory $frontendDir -Wait
}

# 3. Start Services
Write-Host "Starting Services..." -ForegroundColor Yellow

try {
    # Start Backend
    Write-Host "Launching Backend (Port 8200)..." -ForegroundColor Green
    # Use the detected python interpreter
    $backendCmd = "& '$venvPython' manage.py runserver 0.0.0.0:8200"
    $backendArgs = @("-NoExit", "-Command", $backendCmd)
    Start-Process powershell -ArgumentList $backendArgs -WorkingDirectory $backendDir

    # Start Frontend
    Write-Host "Launching Frontend (Vite)..." -ForegroundColor Green
    $frontendArgs = @("-NoExit", "-Command", "npm run dev")
    Start-Process powershell -ArgumentList $frontendArgs -WorkingDirectory $frontendDir

    Write-Host "`nSuccess!" -ForegroundColor Cyan
    Write-Host "Backend: http://127.0.0.1:8200" -ForegroundColor Gray
    Write-Host "Frontend: http://127.0.0.1:5173" -ForegroundColor Gray
    Start-Sleep -Seconds 3
}
catch {
    Write-Host "Error occurred: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
