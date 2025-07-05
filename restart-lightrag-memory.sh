#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Restarting LightRAG MEMORY Docker Services...${NC}"

# Change to lightrag_memory_server directory
LIGHTRAG_DIR="lightrag_memory_server"
if [ ! -d "$LIGHTRAG_DIR" ]; then
    echo -e "${RED}✗${NC} Directory $LIGHTRAG_DIR not found"
    exit 1
fi

cd "$LIGHTRAG_DIR" || {
    echo -e "${RED}✗${NC} Failed to change to $LIGHTRAG_DIR directory"
    exit 1
}

echo -e "${BLUE}Working from directory: $(pwd)${NC}"

# Use the specific env file for the memory service
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Warning:${NC} $ENV_FILE not found. Creating from example."
    cp env.save "$ENV_FILE"
fi

# Stop services
echo -e "${YELLOW}Stopping services...${NC}"
if docker-compose --env-file .env --env-file "$ENV_FILE" down; then
    echo -e "${GREEN}✓${NC} Services stopped successfully"
else
    echo -e "${RED}✗${NC} Failed to stop services"
    exit 1
fi

# Start services
echo -e "${YELLOW}Starting services...${NC}"
if docker-compose --env-file .env --env-file "$ENV_FILE" up -d; then
    echo -e "${GREEN}✓${NC} Services started successfully"
else
    echo -e "${RED}✗${NC} Failed to start services"
    exit 1
fi

# Wait for services to initialize
echo -e "${YELLOW}Waiting for services to initialize...${NC}"
sleep 3

# Show service status
echo -e "${BLUE}Current Service Status:${NC}"
docker-compose --env-file .env --env-file "$ENV_FILE" ps

# Show current Ollama configuration
echo -e "\n${BLUE}Current Ollama Configuration:${NC}"
if [ -f ".env" ]; then
    current_url=$(grep "^OLLAMA_URL=" .env | cut -d'=' -f2)
    echo "  OLLAMA_URL=$current_url"
    
    if [[ "$current_url" == *"host.docker.internal"* ]]; then
        echo -e "  Mode: ${GREEN}LOCAL${NC}"
    elif [[ "$current_url" == *"tesla.local"* ]]; then
        echo -e "  Mode: ${GREEN}REMOTE${NC}"
    else
        echo -e "  Mode: ${YELLOW}CUSTOM${NC}"
    fi
else
    echo -e "${RED}✗${NC} .env file not found in this directory. Using parent .env if available."
fi

echo -e "\n${GREEN}✓ LightRAG Memory services restarted successfully${NC}"