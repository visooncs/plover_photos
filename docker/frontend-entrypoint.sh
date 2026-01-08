#!/bin/sh
set -e

echo "Starting frontend entrypoint..."
cd /app

# 检查 node_modules 是否完整
if [ ! -f "node_modules/.bin/vite" ]; then
    echo "Dependencies missing or incomplete. Installing..."
    npm config set registry https://registry.npmmirror.com/
    npm install
else
    echo "Dependencies found."
fi

echo "Building frontend..."
npx vite build

echo "Deploying to Nginx..."
# 确保目标目录存在
mkdir -p /usr/share/nginx/html

# 清理旧文件
echo "Cleaning old files..."
rm -rf /usr/share/nginx/html/*

# 使用 . 复制目录下的所有内容（包含隐藏文件），比 * 更可靠
if [ -d "dist" ]; then
    echo "Copying files from dist to /usr/share/nginx/html/..."
    cp -r dist/. /usr/share/nginx/html/
    echo "Frontend deployed successfully."
else
    echo "Error: dist directory not found after build!"
    exit 1
fi

echo "Starting Nginx..."
exec nginx -g "daemon off;"
