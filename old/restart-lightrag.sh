#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to display usage
show_usage() {
    echo -e "${BLUE}PersonalAgent LightRAG Restart Script${NC}"
    echo -e "${CYAN}Usage: $0 [OPTIONS]${NC}"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  -s, --server     Restart only the regular LightRAG server (port 9621)"
    echo "  -m, --memory     Restart only the memory server (port 9622)"
    echo "  -a, --all        Restart both servers (default)"
    echo "  -h, --help       Show this help message"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0               # Restart both servers"
    echo "  $0 --all         # Restart both servers"
    echo "  $0 --server      # Restart only regular server"
    echo "  $0 --memory      # Restart only memory server"
}

# Function to restart regular LightRAG server
restart_server() {
    echo -e "${BLUE}=== Restarting Regular LightRAG Server ===${NC}"
    
    LIGHTRAG_DIR="lightrag_server"
    if [ ! -d "$LIGHTRAG_DIR" ]; then
        echo -e "${RED}✗${NC} Directory $LIGHTRAG_DIR not found"
        return 1
    fi

    cd "$LIGHTRAG_DIR" || {
        echo -e "${RED}✗${NC} Failed to change to $LIGHTRAG_DIR directory"
        return 1
    }

    echo -e "${BLUE}Working from directory: $(pwd)${NC}"

    # Stop services
    echo -e "${YELLOW}Stopping regular LightRAG services...${NC}"
    if docker-compose down; then
        echo -e "${GREEN}✓${NC} Regular LightRAG services stopped successfully"
    else
        echo -e "${RED}✗${NC} Failed to stop regular LightRAG services"
        cd ..
        return 1
    fi

    # Start services
    echo -e "${YELLOW}Starting regular LightRAG services...${NC}"
    if docker-compose up -d; then
        echo -e "${GREEN}✓${NC} Regular LightRAG services started successfully"
    else
        echo -e "${RED}✗${NC} Failed to start regular LightRAG services"
        cd ..
        return 1
    fi

    # Wait for services to initialize
    echo -e "${YELLOW}Waiting for regular LightRAG services to initialize...${NC}"
    sleep 3

    # Show service status
    echo -e "${BLUE}Regular LightRAG Service Status:${NC}"
    docker-compose ps

    # Show current Ollama configuration
    echo -e "\n${BLUE}Regular LightRAG Ollama Configuration:${NC}"
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
        echo -e "${RED}✗${NC} .env file not found"
    fi

    cd ..
    echo -e "${GREEN}✓ Regular LightRAG server restarted successfully${NC}"
    return 0
}

# Function to restart memory server
restart_memory() {
    echo -e "${BLUE}=== Restarting LightRAG Memory Server ===${NC}"
    
    LIGHTRAG_DIR="lightrag_memory_server"
    if [ ! -d "$LIGHTRAG_DIR" ]; then
        echo -e "${RED}✗${NC} Directory $LIGHTRAG_DIR not found"
        return 1
    fi

    cd "$LIGHTRAG_DIR" || {
        echo -e "${RED}✗${NC} Failed to change to $LIGHTRAG_DIR directory"
        return 1
    }

    echo -e "${BLUE}Working from directory: $(pwd)${NC}"

    # Use the specific env file for the memory service
    ENV_FILE=".env"
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}Warning:${NC} $ENV_FILE not found. Creating from example."
        cp env.save "$ENV_FILE"
    fi

    # Stop services
    echo -e "${YELLOW}Stopping memory services...${NC}"
    if docker-compose --env-file .env --env-file "$ENV_FILE" down; then
        echo -e "${GREEN}✓${NC} Memory services stopped successfully"
    else
        echo -e "${RED}✗${NC} Failed to stop memory services"
        cd ..
        return 1
    fi

    # Start services
    echo -e "${YELLOW}Starting memory services...${NC}"
    if docker-compose --env-file .env --env-file "$ENV_FILE" up -d; then
        echo -e "${GREEN}✓${NC} Memory services started successfully"
    else
        echo -e "${RED}✗${NC} Failed to start memory services"
        cd ..
        return 1
    fi

    # Wait for services to initialize
    echo -e "${YELLOW}Waiting for memory services to initialize...${NC}"
    sleep 3

    # Show service status
    echo -e "${BLUE}Memory Service Status:${NC}"
    docker-compose --env-file .env --env-file "$ENV_FILE" ps

    # Show current Ollama configuration
    echo -e "\n${BLUE}Memory Server Ollama Configuration:${NC}"
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

    cd ..
    echo -e "${GREEN}✓ LightRAG Memory server restarted successfully${NC}"
    return 0
}

# Function to show overall status
show_status() {
    echo -e "\n${CYAN}=== Overall LightRAG Services Status ===${NC}"
    echo -e "${BLUE}All running LightRAG containers:${NC}"
    docker ps --filter "name=lightrag" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# Main script logic
RESTART_SERVER=false
RESTART_MEMORY=false
RESTART_ALL=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--server)
            RESTART_SERVER=true
            RESTART_ALL=false
            shift
            ;;
        -m|--memory)
            RESTART_MEMORY=true
            RESTART_ALL=false
            shift
            ;;
        -a|--all)
            RESTART_ALL=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# If no specific options, restart all
if [ "$RESTART_ALL" = true ]; then
    RESTART_SERVER=true
    RESTART_MEMORY=true
fi

# Execute restart operations
SUCCESS=true

if [ "$RESTART_SERVER" = true ]; then
    if ! restart_server; then
        SUCCESS=false
    fi
    echo ""
fi

if [ "$RESTART_MEMORY" = true ]; then
    if ! restart_memory; then
        SUCCESS=false
    fi
    echo ""
fi

# Show final status
show_status

# Final result
if [ "$SUCCESS" = true ]; then
    echo -e "\n${GREEN}✓ All requested LightRAG services restarted successfully${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Some services failed to restart${NC}"
    exit 1
fi
