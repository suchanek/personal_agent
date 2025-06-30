#!/bin/bash

set -e

echo "🧼 Verifying Docker installation..."

if ! command -v docker &> /dev/null
then
    echo "❌ Docker is not installed. Please install Docker Desktop for Mac first:"
    echo "   https://www.docker.com/products/docker-desktop/"
    exit 1
fi

echo "✅ Docker is installed."

# Create system-wide Ollama directory structure
echo "📦 Setting up system-wide Ollama directory..."

sudo mkdir -p /Users/Shared/ollama/models
sudo mkdir -p /Users/Shared/ollama/config
sudo mkdir -p /Users/Shared/ollama/data

# Migrate existing models and configuration files
echo "🔄 Migrating existing Ollama data..."

# Copy models from user directory if they exist
if [ -d ~/.ollama/models ]; then
    echo "📁 Copying models from ~/.ollama/models to /Users/Shared/ollama/models..."
    sudo cp -r ~/.ollama/models/* /Users/Shared/ollama/models/ 2>/dev/null || true
    echo "✅ Models migrated successfully"
else
    echo "ℹ️  No existing models found in ~/.ollama/models"
fi

# Copy configuration files (ignore missing files gracefully)
echo "📋 Copying configuration files..."
sudo cp ~/.ollama/config /Users/Shared/ollama/config/ 2>/dev/null || true
sudo cp ~/.ollama/ollama.db /Users/Shared/ollama/data/ 2>/dev/null || true
sudo cp ~/.ollama/history /Users/Shared/ollama/data/ 2>/dev/null || true

# Set proper permissions - readable by all, writable by root and current user
echo "🔐 Setting permissions..."
sudo chown -R $(whoami):staff /Users/Shared/ollama
sudo chmod -R 755 /Users/Shared/ollama

# Pull latest Ollama Docker image
echo "🐳 Pulling Ollama Docker image..."
docker pull ollama/ollama

# Stop and remove any existing container
docker rm -f ollama-server || true

# Start Docker container with absolute path mounts
echo "🚀 Launching Ollama Docker container..."
docker run -d \
  --name ollama-server \
  --restart always \
  -p 11434:11434 \
  -v /Users/Shared/ollama:/root/.ollama \
  ollama/ollama

# Create launchd plist for automatic boot
echo "📝 Creating launchd plist for boot persistence..."

sudo tee /Library/LaunchDaemons/com.ollama.docker.plist > /dev/null <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.ollama.docker</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-c</string>
    <string>
      until docker info &> /dev/null; do
        echo 'Waiting for Docker to start...';
        sleep 5;
      done;
      docker start ollama-server
    </string>
  </array>

  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>/var/log/ollama-docker.stdout.log</string>
  <key>StandardErrorPath</key>
  <string>/var/log/ollama-docker.stderr.log</string>
</dict>
</plist>
EOF

# Fix plist permissions
sudo chown root:wheel /Library/LaunchDaemons/com.ollama.docker.plist
sudo chmod 644 /Library/LaunchDaemons/com.ollama.docker.plist

# Load plist into launchd
echo "🚀 Loading launchd daemon..."
sudo launchctl load /Library/LaunchDaemons/com.ollama.docker.plist

echo "✅ Local Docker headless Ollama server fully installed and boot-persistent!"
echo "🌐 Models and data are now stored in: /Users/Shared/ollama/"
echo "📁 Directory structure:"
echo "   /Users/Shared/ollama/models/  - Model files"
echo "   /Users/Shared/ollama/config/  - Configuration"
echo "   /Users/Shared/ollama/data/    - Database and history"
echo ""
echo "🔍 You can verify with:"
echo "    curl http://kepler.local:11434/api/tags"
echo "    docker ps"
echo "    ls -la /Users/Shared/ollama/"
