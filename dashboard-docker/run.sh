#!/bin/bash
# Run script for Personal Agent Dashboard Docker container

set -e

echo "🚀 Starting Personal Agent Dashboard..."

# Create data and logs directories if they don't exist
mkdir -p data logs

# Check if image exists
if ! docker image inspect personal-agent-dashboard:latest >/dev/null 2>&1; then
    echo "❌ Docker image not found. Building it first..."
    ./build.sh
fi

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q personal-agent-dashboard; then
    echo "🛑 Stopping existing container..."
    docker stop personal-agent-dashboard >/dev/null 2>&1 || true
    docker rm personal-agent-dashboard >/dev/null 2>&1 || true
fi

# Run the container
echo "🐳 Starting dashboard container..."
docker run -d \
    --name personal-agent-dashboard \
    -p 8501:8501 \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -v "$(pwd)/data:/app/data" \
    -v "$(pwd)/logs:/app/logs" \
    -e LIGHTRAG_URL=http://host.docker.internal:9621 \
    -e LIGHTRAG_MEMORY_URL=http://host.docker.internal:9622 \
    -e OLLAMA_URL=http://host.docker.internal:11434 \
    -e USER_ID=dashboard_user \
    -e LOG_LEVEL=INFO \
    --restart unless-stopped \
    personal-agent-dashboard:latest

echo "✅ Dashboard started successfully!"
echo ""
echo "📊 Dashboard URL: http://localhost:8501"
echo ""
echo "📋 Container status:"
docker ps --filter name=personal-agent-dashboard --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "📝 To view logs: docker logs -f personal-agent-dashboard"
echo "🛑 To stop: docker stop personal-agent-dashboard"
