#!/bin/sh
set -e

echo "Starting frontend entrypoint..."
cd /app

# Check if node_modules exists, if not install
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm config set registry https://registry.npmmirror.com/
    npm install
fi

echo "Building frontend..."
npm run build

echo "Deploying to Nginx..."
# Clean old files
rm -rf /usr/share/nginx/html/*
# Copy new files
cp -r dist/* /usr/share/nginx/html/

echo "Starting Nginx..."
exec nginx -g "daemon off;"
