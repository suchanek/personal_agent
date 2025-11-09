#!/bin/bash

# Smart LightRAG Docker Restart Script
# Provides intelligent restart with proper port cleanup and waiting periods
# to prevent "port already allocated" errors.
# Assumes ~/.persag exists and that they contain the docker server dirs
#
# Author: Eric G. Suchanek, PhD.
# Last revision: 2025-11-08 18:19:18



# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
# Resolve base ~/.persag directory and allow env overrides
PERSAG_HOME="${PERSAG_HOME:-$HOME/.persag}"
LIGHTRAG_SERVER_DIR="${LIGHTRAG_SERVER_DIR:-$PERSAG_HOME/lightrag_server}"
LIGHTRAG_MEMORY_DIR="${LIGHTRAG_MEMORY_DIR:-$PERSAG_HOME/lightrag_memory_server}"
LIGHTRAG_SERVER_PORT=${LIGHTRAG_SERVER_PORT:-9621}
LIGHTRAG_MEMORY_PORT=${LIGHTRAG_MEMORY_PORT:-9622}
MAX_WAIT_TIME=${MAX_WAIT_TIME:-30}
CLEANUP_WAIT=${CLEANUP_WAIT:-5}

# Function to get AGNO_STORAGE_DIR from Python settings
get_agno_storage_dir() {
    poetry run python -c "from personal_agent.config.user_id_mgr import get_user_storage_paths; print(get_user_storage_paths()['AGNO_STORAGE_DIR'])"
}

# Get and export AGNO_STORAGE_DIR for Docker volume mounts
AGNO_STORAGE_DIR=$(get_agno_storage_dir)
if [ $? -ne 0 ] || [ -z "$AGNO_STORAGE_DIR" ]; then
    echo -e "${RED}❌ Failed to get AGNO_STORAGE_DIR from Python settings${NC}"
    exit 1
fi
export AGNO_STORAGE_DIR

# Ensure the storage directories exist
mkdir -p "$AGNO_STORAGE_DIR/rag_storage"
mkdir -p "$AGNO_STORAGE_DIR/inputs"
mkdir -p "$AGNO_STORAGE_DIR/memory_rag_storage"
mkdir -p "$AGNO_STORAGE_DIR/memory_inputs"

echo -e "${CYAN}📁 Using AGNO_STORAGE_DIR: ${AGNO_STORAGE_DIR}${NC}"

echo -e "${BLUE}🧠 Smart LightRAG Docker Restart${NC}"
echo -e "${CYAN}Intelligent restart with proper port cleanup and waiting periods${NC}"
printf '%*s\n' 70 '' | tr ' ' '='

# Function to check if a port is available
check_port_available() {
    local port=$1
    local timeout=${2:-30}
    local start_time=$(date +%s)
    
    while [ $(($(date +%s) - start_time)) -lt $timeout ]; do
        if ! nc -z localhost $port 2>/dev/null; then
            return 0  # Port is available
        fi
        sleep 1
    done
    return 1  # Port still in use
}

# Function to wait for container to stop
wait_for_container_stop() {
    local container_name=$1
    local timeout=${2:-30}
    local start_time=$(date +%s)
    
    while [ $(($(date +%s) - start_time)) -lt $timeout ]; do
        if ! docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
            return 0  # Container stopped
        fi
        sleep 1
    done
    return 1  # Container still running
}

# Function to force kill container
force_kill_container() {
    local container_name=$1
    echo -e "${YELLOW}⚠️  Force killing container: ${container_name}${NC}"
    
    if docker kill $container_name 2>/dev/null; then
        echo -e "${GREEN}✅ Force killed: ${container_name}${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to force kill: ${container_name}${NC}"
        return 1
    fi
}

# Function to smart stop a service
smart_stop_service() {
    local service_dir=$1
    local container_name=$2
    local port=$3
    local service_name=$4
    
    echo -e "\n${PURPLE}🛑 Smart stopping ${service_name}...${NC}"
    
    # Check if directory exists
    if [ ! -d "$service_dir" ]; then
        echo -e "${RED}❌ Directory not found: ${service_dir}${NC}"
        return 1
    fi
    
    cd "$service_dir" || {
        echo -e "${RED}❌ Failed to change to ${service_dir}${NC}"
        return 1
    }
    
    # Step 1: Graceful docker-compose down
    echo -e "${CYAN}   📝 Attempting graceful shutdown...${NC}"
    if docker-compose down; then
        echo -e "${GREEN}   ✅ Graceful shutdown completed${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Graceful shutdown failed${NC}"
    fi
    
    # Step 2: Wait for container to stop
    echo -e "${CYAN}   ⏳ Waiting for container to stop...${NC}"
    if ! wait_for_container_stop "$container_name" 15; then
        echo -e "${YELLOW}   ⚠️  Container didn't stop gracefully${NC}"
        if ! force_kill_container "$container_name"; then
            cd - > /dev/null
            return 1
        fi
    else
        echo -e "${GREEN}   ✅ Container stopped successfully${NC}"
    fi
    
    # Step 3: Wait for port to be released
    echo -e "${CYAN}   🔌 Waiting for port ${port} to be released...${NC}"
    if check_port_available $port $MAX_WAIT_TIME; then
        echo -e "${GREEN}   ✅ Port ${port} is now available${NC}"
    else
        echo -e "${RED}   ❌ Port ${port} still in use after ${MAX_WAIT_TIME} seconds${NC}"
        cd - > /dev/null
        return 1
    fi
    
    cd - > /dev/null
    echo -e "${GREEN}✅ Successfully stopped ${service_name}${NC}"
    return 0
}

# Function to smart start a service
smart_start_service() {
    local service_dir=$1
    local container_name=$2
    local port=$3
    local service_name=$4
    local max_retries=3
    
    echo -e "\n${PURPLE}🚀 Smart starting ${service_name}...${NC}"
    
    # Check if directory exists
    if [ ! -d "$service_dir" ]; then
        echo -e "${RED}❌ Directory not found: ${service_dir}${NC}"
        return 1
    fi
    
    cd "$service_dir" || {
        echo -e "${RED}❌ Failed to change to ${service_dir}${NC}"
        return 1
    }
    
    # Verify port is available
    echo -e "${CYAN}   🔌 Verifying port ${port} is available...${NC}"
    if ! check_port_available $port 5; then
        echo -e "${RED}   ❌ Port ${port} is still in use${NC}"
        cd - > /dev/null
        return 1
    fi
    
    # Try to start the service
    for attempt in $(seq 1 $max_retries); do
        echo -e "${CYAN}   📝 Starting service (attempt ${attempt}/${max_retries})...${NC}"
        
        if docker-compose up -d; then
            echo -e "${GREEN}   ✅ Docker-compose up completed${NC}"
            
            # Wait for service to initialize
            echo -e "${CYAN}   ⏳ Waiting for service to initialize...${NC}"
            sleep 3
            
            # Verify container is running
            if docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
                echo -e "${GREEN}   ✅ Container is running${NC}"
                cd - > /dev/null
                echo -e "${GREEN}✅ Successfully started ${service_name}${NC}"
                return 0
            else
                echo -e "${YELLOW}   ⚠️  Container not found in running state${NC}"
            fi
        else
            echo -e "${YELLOW}   ⚠️  Attempt ${attempt} failed${NC}"
            if [ $attempt -lt $max_retries ]; then
                echo -e "${CYAN}   ⏳ Waiting before retry...${NC}"
                sleep 2
            fi
        fi
    done
    
    cd - > /dev/null
    echo -e "${RED}❌ Failed to start ${service_name} after ${max_retries} attempts${NC}"
    return 1
}

# Function to cleanup Docker networks
cleanup_docker_networks() {
    echo -e "\n${CYAN}🧹 Cleaning up Docker networks...${NC}"
    if docker network prune -f > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Docker networks cleaned up${NC}"
    else
        echo -e "${YELLOW}⚠️  Network cleanup had issues (non-critical)${NC}"
    fi
}

# Main execution
main() {
    local target_service=""
    local restart_all=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --server)
                target_service="server"
                shift
                ;;
            --memory)
                target_service="memory"
                shift
                ;;
            --all)
                restart_all=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--server|--memory|--all]"
                echo "  --server  : Restart only LightRAG server"
                echo "  --memory  : Restart only LightRAG memory server"
                echo "  --all     : Restart all services (default)"
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Default to restart all if no specific service specified
    if [ -z "$target_service" ] && [ "$restart_all" = false ]; then
        restart_all=true
    fi
    
    # Determine which services to restart
    local services_to_restart=()
    
    if [ "$restart_all" = true ]; then
        services_to_restart=("server" "memory")
        echo -e "${BLUE}🔄 Restarting all LightRAG services${NC}"
    elif [ "$target_service" = "server" ]; then
        services_to_restart=("server")
        echo -e "${BLUE}🔄 Restarting LightRAG server only${NC}"
    elif [ "$target_service" = "memory" ]; then
        services_to_restart=("memory")
        echo -e "${BLUE}🔄 Restarting LightRAG memory server only${NC}"
    fi
    
    # Stop all specified services first
    local stop_success=true
    for service in "${services_to_restart[@]}"; do
        if [ "$service" = "server" ]; then
            if ! smart_stop_service "$LIGHTRAG_SERVER_DIR" "lightrag_pagent" $LIGHTRAG_SERVER_PORT "LightRAG Server"; then
                stop_success=false
            fi
        elif [ "$service" = "memory" ]; then
            if ! smart_stop_service "$LIGHTRAG_MEMORY_DIR" "lightrag_memory" $LIGHTRAG_MEMORY_PORT "LightRAG Memory Server"; then
                stop_success=false
            fi
        fi
    done
    
    if [ "$stop_success" = false ]; then
        echo -e "\n${RED}❌ Some services failed to stop properly${NC}"
        exit 1
    fi
    
    # Additional cleanup wait
    echo -e "\n${CYAN}⏳ Waiting ${CLEANUP_WAIT} seconds for complete cleanup...${NC}"
    sleep $CLEANUP_WAIT
    
    # Clean up Docker networks
    cleanup_docker_networks
    
    # Start all specified services
    local start_success=true
    for service in "${services_to_restart[@]}"; do
        if [ "$service" = "server" ]; then
            if ! smart_start_service "$LIGHTRAG_SERVER_DIR" "lightrag_pagent" $LIGHTRAG_SERVER_PORT "LightRAG Server"; then
                start_success=false
            fi
        elif [ "$service" = "memory" ]; then
            if ! smart_start_service "$LIGHTRAG_MEMORY_DIR" "lightrag_memory" $LIGHTRAG_MEMORY_PORT "LightRAG Memory Server"; then
                start_success=false
            fi
        fi
    done
    
    # Final status
    echo -e "\n${BLUE}📊 Final Status Check${NC}"
    echo "============================="
    
    if [ "$start_success" = true ]; then
        echo -e "${GREEN}🎉 Smart restart completed successfully!${NC}"
        
        # Show running containers
        echo -e "\n${CYAN}Running LightRAG containers:${NC}"
        docker ps --filter "name=lightrag" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        exit 0
    else
        echo -e "${RED}❌ Some services failed to start${NC}"
        echo -e "${YELLOW}💡 Check the logs above for details${NC}"
        exit 1
    fi
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running or not accessible${NC}"
    echo -e "${YELLOW}💡 Please start Docker and try again${NC}"
    exit 1
fi

# Check if netcat is available for port checking
if ! command -v nc > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  netcat (nc) not found - port checking may be limited${NC}"
fi

# Run main function
main "$@"
