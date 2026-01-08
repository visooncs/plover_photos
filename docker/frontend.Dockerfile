# Frontend Dockerfile (Runtime Build Version)
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/node:18-alpine

# Install Nginx
RUN apk add --no-cache nginx

# Create nginx run directory
RUN mkdir -p /run/nginx

# Set working directory
WORKDIR /app

# Copy entrypoint script
COPY docker/frontend-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/frontend-entrypoint.sh

# Expose port
EXPOSE 80

# Set entrypoint
ENTRYPOINT ["frontend-entrypoint.sh"]
