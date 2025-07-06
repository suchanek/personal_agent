#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENV_FILE=".env"
BACKUP_DIR="backups"
LOCAL_URL="http://localhost:11434"
LOCAL_DOCKER_URL="http://host.docker.internal:11434"
REMOTE_URL="http://tesla.local:11434"
REMOTE_DOCKER_URL="http://192.168.1.126:11434"
LOCAL_LIGHTRAG_URL="http://localhost:9621"
REMOTE_LIGHTRAG_URL="http://tesla.local:9621"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage: $0 {local|remote|status}${NC}"
    echo ""
    echo "Commands:"
    echo "  local   - Switch to local Ollama server (host.docker.internal:11434)"
    echo "  remote  - Switch to remote Ollama server (tesla.local:11434)"
    echo "  status  - Show current Ollama configuration"
    echo ""
    echo "Examples:"
    echo "  $0 local"
    echo "  $0 remote"
    echo "  $0 status"
}

# Function to backup .env file
backup_env() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$BACKUP_DIR/.env.backup.$timestamp"
    cp "$ENV_FILE" "$backup_file"
    echo -e "${GREEN}✓${NC} Backed up .env to $backup_file"
}

# Function to get current OLLAMA_URL
get_current_url() {
    grep "^OLLAMA_URL=" "$ENV_FILE" | cut -d'=' -f2
}

# Function to show current status
show_status() {
    local current_url=$(get_current_url)
    echo -e "${BLUE}Current Ollama Configuration:${NC}"
    echo "  OLLAMA_URL=$current_url"
    
    if [[ "$current_url" == "$LOCAL_URL" ]]; then
        echo -e "  RAG Mode: ${GREEN}LOCAL${NC} (host.docker.internal)"
    elif [[ "$current_url" == "$REMOTE_URL" ]]; then
        echo -e "  RAG Mode: ${GREEN}REMOTE${NC} (tesla.local)"
    else
        echo -e "  RAG Mode: ${YELLOW}CUSTOM${NC}"
    fi
}

# Function to test Ollama connectivity
test_ollama_connection() {
    local url=$1
    local host_port=$(echo "$url" | sed 's|http://||' | sed 's|https://||')
    
    echo -e "${YELLOW}Testing connection to $url...${NC}"
    
    # Test basic connectivity first
    if curl -s "$url/api/tags" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Ollama server is reachable at $url"
        return 1
    else
        echo -e "${RED}✗${NC} Cannot reach Ollama server at $url"
        echo -e "${YELLOW}Note: This might be normal if the server is not running${NC}"
        return 0
    fi
}

# Function to update both OLLAMA_URL and OLLAMA_DOCKER_URL in .env file
update_urls() {
    local new_ollama_url=$1
    local new_ollama_docker_url=$2
    local new_lightrag_url=$3
    local temp_file=$(mktemp)
    
    sed -e "s|^OLLAMA_URL=.*|OLLAMA_URL=$new_ollama_url|" \
        -e "s|^OLLAMA_DOCKER_URL=.*|OLLAMA_DOCKER_URL=$new_ollama_docker_url|" \
        -e "s|^LIGHTRAG_URL=.*|LIGHTRAG_URL=$new_lightrag_url|" \
        "$ENV_FILE" > "$temp_file"
    
    if grep -q "^OLLAMA_URL=$new_ollama_url" "$temp_file" && \
       grep -q "^OLLAMA_DOCKER_URL=$new_ollama_docker_url" "$temp_file" && \
       grep -q "^LIGHTRAG_URL=$new_lightrag_url" "$temp_file"; then
        mv "$temp_file" "$ENV_FILE"
        echo "✓ Updated OLLAMA_URL to: $new_ollama_url"
        echo "✓ Updated OLLAMA_DOCKER_URL to: $new_ollama_docker_url"
        echo "✓ Updated LIGHTRAG_URL to: $new_lightrag_url"
        return 0
    else
        rm "$temp_file"
        echo "✗ Failed to update URLs"
        return 1
    fi
}

# Function to restart Docker services
restart_docker_services() {
    echo -e "${BLUE}Restarting LightRAG Docker Services...${NC}"

    # Change to lightrag_server directory
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
    echo -e "${YELLOW}Stopping services...${NC}"
    if docker-compose down; then
        echo -e "${GREEN}✓${NC} Services stopped successfully"
    else
        echo -e "${RED}✗${NC} Failed to stop services"
        cd - > /dev/null
        return 1
    fi

    # Start services
    echo -e "${YELLOW}Starting services...${NC}"
    if docker-compose up -d; then
        echo -e "${GREEN}✓${NC} Services started successfully"
    else
        echo -e "${RED}✗${NC} Failed to start services"
        cd - > /dev/null
        return 1
    fi

    # Wait for services to initialize
    echo -e "${YELLOW}Waiting for services to initialize...${NC}"
    sleep 3

    # Show service status
    echo -e "${BLUE}Current Service Status:${NC}"
    docker-compose ps

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
        echo -e "${RED}✗${NC} .env file not found"
    fi

    # Return to original directory
    cd - > /dev/null

    echo -e "\n${GREEN}✓ LightRAG services restarted successfully${NC}"
    return 0
}

# Main script logic
case "$1" in
    "local")
        echo -e "${BLUE}Switching to LOCAL Ollama server...${NC}"
        
        # Check if already local
        current_url=$(get_current_url)
        if [[ "$current_url" == "$LOCAL_URL" ]]; then
            echo -e "${YELLOW}Already using local Ollama server${NC}"
            show_status
            exit 0
        fi
        
        # Backup current config
        backup_env
        
        # Update configuration
        if update_urls "$LOCAL_URL" "$LOCAL_DOCKER_URL" "$LOCAL_LIGHTRAG_URL"; then
            # Test connection (optional, don't fail if unreachable)
            test_ollama_connection "$LOCAL_URL"
            
            # Restart Docker services
            if restart_docker_services; then
                echo -e "${GREEN}✓ Successfully switched to LOCAL Ollama server${NC}"
                show_status
            else
                echo -e "${RED}✗ Failed to restart Docker services${NC}"
                exit 1
            fi
        else
            echo -e "${RED}✗ Failed to update configuration${NC}"
            exit 1
        fi
        ;;
        
    "remote")
        echo -e "${BLUE}Switching to REMOTE Ollama server (tesla.local)...${NC}"
        
        # Check if already remote
        current_url=$(get_current_url)
        if [[ "$current_url" == "$REMOTE_URL" ]]; then
            echo -e "${YELLOW}Already using remote Ollama server${NC}"
            show_status
            exit 0
        fi
        
        # Backup current config
        backup_env
        
        # Update configuration
        if update_urls "$REMOTE_URL" "$REMOTE_DOCKER_URL" "$REMOTE_LIGHTRAG_URL"; then
            # Test connection (optional, don't fail if unreachable)
            test_ollama_connection "$REMOTE_URL"
            
            # Restart Docker services
            if restart_docker_services; then
                echo -e "${GREEN}✓ Successfully switched to REMOTE Ollama server${NC}"
                show_status
            else
                echo -e "${RED}✗ Failed to restart Docker services${NC}"
                exit 1
            fi
        else
            echo -e "${RED}✗ Failed to update configuration${NC}"
            exit 1
        fi
        ;;
        
    "status")
        show_status
        
        # Test current connection
        current_url=$(get_current_url)
        test_ollama_connection "$current_url"
        
        # Show Docker service status
        echo -e "\n${BLUE}Docker Service Status:${NC}"
        docker-compose ps
        ;;
        
    *)
        show_usage
        exit 1
        ;;
esac
