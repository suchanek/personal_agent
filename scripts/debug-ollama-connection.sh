#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to test Ollama connectivity with detailed diagnostics
debug_ollama_connection() {
    local url=$1
    local host_port=$(echo "$url" | sed 's|http://||' | sed 's|https://||')
    local host=$(echo "$host_port" | cut -d':' -f1)
    local port=$(echo "$host_port" | cut -d':' -f2)
    
    echo -e "${BLUE}=== Debugging Ollama Connection to $url ===${NC}"
    
    # Step 1: Test host resolution
    echo -e "\n${YELLOW}1. Testing host resolution for '$host'...${NC}"
    if ping -c 1 -W 3 "$host" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Host '$host' is reachable"
        ping -c 1 "$host" | head -1
    else
        echo -e "${RED}✗${NC} Cannot resolve/reach host '$host'"
        echo "  Try: ping $host"
        return 1
    fi
    
    # Step 2: Test port connectivity
    echo -e "\n${YELLOW}2. Testing port connectivity to $host:$port...${NC}"
    if command -v nc >/dev/null 2>&1; then
        if nc -z "$host" "$port" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Port $port is open on $host"
        else
            echo -e "${RED}✗${NC} Port $port is not accessible on $host"
            echo "  The Ollama server might not be running"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} 'nc' command not available, skipping port test"
    fi
    
    # Step 3: Test basic HTTP connectivity
    echo -e "\n${YELLOW}3. Testing basic HTTP connectivity...${NC}"
    if curl -s -I "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} HTTP server responding at $url"
    else
        echo -e "${RED}✗${NC} No HTTP response from $url"
        echo "  Server might not be running or not an HTTP server"
        return 1
    fi
    
    # Step 4: Test Ollama API endpoint
    echo -e "\n${YELLOW}4. Testing Ollama API endpoint...${NC}"
    local response=$(curl -s "$url/api/tags" 2>&1)
    local curl_exit_code=$?
    
    if [ $curl_exit_code -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Ollama API is responding"
        echo "  Response preview: $(echo "$response" | head -c 100)..."
    else
        echo -e "${RED}✗${NC} Ollama API not responding (curl exit code: $curl_exit_code)"
        return 0
        
        # Show curl error details
        case $curl_exit_code in
            6) echo "  Error: Couldn't resolve host" ;;
            7) echo "  Error: Failed to connect to host" ;;
            28) echo "  Error: Operation timeout" ;;
            *) echo "  Curl error: $response" ;;
        esac
        
        return 1
    fi
}

# Function to show system info
show_system_info() {
    echo -e "${BLUE}=== System Information ===${NC}"
    echo "OS: $(uname -s)"
    echo "Docker available: $(command -v docker >/dev/null && echo "Yes" || echo "No")"
    echo "Curl available: $(command -v curl >/dev/null && echo "Yes" || echo "No")"
    echo "NC available: $(command -v nc >/dev/null && echo "Yes" || echo "No")"
    
    if command -v docker >/dev/null; then
        echo "Docker running: $(docker info >/dev/null 2>&1 && echo "Yes" || echo "No")"
    fi
}

# Main execution
if [ $# -eq 0 ]; then
    echo -e "${BLUE}Usage: $0 <ollama-url>${NC}"
    echo "Examples:"
    echo "  $0 http://host.docker.internal:11434"
    echo "  $0 http://100.100.248.61:11434"
    echo "  $0 http://localhost:11434"
    exit 1
fi

show_system_info
echo ""
debug_ollama_connection "$1"
