# Update Script for Plover Photos
# 此脚本用于更新代码后重新构建和重启服务
$ErrorActionPreference = "Stop"

Write-Host "=== Plover Photos Update System ===" -ForegroundColor Cyan

# 1. 代码更新检查
Write-Host "`n[1/4] Checking for code updates..."
if (Test-Path "..\.git") {
    try {
        Write-Host "Git repository detected. Pulling latest changes..." -ForegroundColor Yellow
        git pull
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Git pull failed. Please check your git status manually."
            # 不强制退出，允许用户手动更新了代码的情况
        }
    } catch {
        Write-Warning "Failed to run git pull. Continuing..."
    }
} else {
    Write-Host "Not a git repository. Skipping git pull."
    Write-Host "Ensure you have manually updated the code files in '../backend' and '../frontend'."
}

# 2. 停止服务（可选，为了稳健）
# Write-Host "`n[2/4] Stopping current services..."
# docker-compose down --remove-orphans

# 3. 重建并启动服务
# --build: 强制重新构建镜像（确保前端代码更新，以及后端依赖更新）
# -d: 后台运行
# --remove-orphans: 清理未定义的容器
Write-Host "`n[2/4] Rebuilding and restarting services..." -ForegroundColor Cyan
docker-compose -f docker-compose.yml up -d --build --remove-orphans

if ($?) {
    Write-Host "Services updated successfully." -ForegroundColor Green
} else {
    Write-Error "Failed to update services."
}

# 4. 清理旧镜像
Write-Host "`n[3/4] Cleaning up old images..."
docker image prune -f
Write-Host "Cleanup complete."

# 5. 检查状态
Write-Host "`n[4/4] Checking service status..."
docker-compose ps

Write-Host "`n=== Update Complete! ===" -ForegroundColor Green
Write-Host "Frontend: http://localhost"
Write-Host "Backend API: http://localhost:8000/api/"
