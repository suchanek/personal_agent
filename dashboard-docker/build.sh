#!/bin/bash
# Build script for Personal Agent Dashboard Docker image

set -e

echo "🐳 Building Personal Agent Dashboard Docker image..."

# Create data and logs directories if they don't exist
mkdir -p data logs

# Build the Docker image
docker build -t personal-agent-dashboard:latest .

echo "✅ Docker image built successfully!"
echo ""
echo "To run the dashboard:"
echo "  ./run.sh"
echo ""
echo "Or use docker-compose:"
echo "  docker-compose up -d"
echo ""
echo "Dashboard will be available at: http://localhost:8501"
