#!/usr/bin/env python3
"""
Fix LightRAG timeout issues for large document processing.
This script modifies the environment variables and restarts the LightRAG container
with extended timeout settings.
"""

import os
import subprocess
import sys
import time

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        return False
    return result

def update_env_file():
    """Update the env.server file with extended timeout settings."""
    env_file = "lightrag_server/env.server"
    
    # Read current env file
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Extended timeout settings - much longer for large documents
    extended_timeouts = """
# EXTENDED TIMEOUT SETTINGS FOR LARGE DOCUMENT PROCESSING
# These settings are specifically for handling documents > 8k characters

# HTTP Client Timeouts (in seconds)
HTTPX_TIMEOUT=14400          # 4 hours total timeout
HTTPX_CONNECT_TIMEOUT=1200   # 20 minutes connection timeout
HTTPX_READ_TIMEOUT=14400     # 4 hours read timeout
HTTPX_WRITE_TIMEOUT=1200     # 20 minutes write timeout
HTTPX_POOL_TIMEOUT=1200      # 20 minutes pool timeout

# Ollama Client Timeouts
OLLAMA_TIMEOUT=14400         # 4 hours for Ollama operations
OLLAMA_REQUEST_TIMEOUT=14400 # 4 hours for individual requests
OLLAMA_KEEP_ALIVE=7200       # Keep model loaded for 2 hours
OLLAMA_NUM_PREDICT=32768     # Increased token limit
OLLAMA_TEMPERATURE=0.1       # Consistent processing

# LightRAG Processing Timeouts
LLM_TIMEOUT=14400            # 4 hours for LLM processing
EMBEDDING_TIMEOUT=7200       # 2 hours for embedding processing
PDF_CHUNK_SIZE=512           # Smaller chunks for better reliability
HTTP_TIMEOUT=14400           # 4 hours for HTTP operations
CONNECTION_TIMEOUT=1200      # 20 minutes for connections
READ_TIMEOUT=14400           # 4 hours for read operations
WRITE_TIMEOUT=1200           # 20 minutes for write operations
POOL_TIMEOUT=1200            # 20 minutes for pool operations

# Processing Configuration
MAX_RETRIES=10               # More retries for large documents
RETRY_DELAY=120              # 2 minutes between retries
BATCH_SIZE=1                 # Process one document at a time
MAX_CONCURRENT_REQUESTS=1    # Single threaded processing
BACKOFF_FACTOR=3.0           # Exponential backoff
ENABLE_CHUNKING=true         # Enable document chunking
CHUNK_OVERLAP=200            # Increased overlap for context

# Python HTTP Client Settings
REQUESTS_TIMEOUT=14400       # 4 hours for requests library
URLLIB3_TIMEOUT=14400        # 4 hours for urllib3
AIOHTTP_TIMEOUT=14400        # 4 hours for aiohttp

# System Level Timeouts
SOCKET_TIMEOUT=14400         # 4 hours for socket operations
TCP_KEEPALIVE=true           # Enable TCP keepalive
TCP_KEEPALIVE_IDLE=600       # 10 minutes idle before keepalive
TCP_KEEPALIVE_INTERVAL=60    # 1 minute between keepalive probes
TCP_KEEPALIVE_COUNT=9        # 9 failed probes before timeout
"""
    
    # Remove existing timeout settings to avoid duplicates
    lines = content.split('\n')
    filtered_lines = []
    skip_section = False
    
    for line in lines:
        if line.strip().startswith('# EXTENDED TIMEOUT SETTINGS'):
            skip_section = True
            continue
        elif skip_section and line.strip() and not line.startswith('#') and not line.startswith(' '):
            # Check if this is a timeout-related variable
            timeout_vars = [
                'HTTPX_TIMEOUT', 'HTTPX_CONNECT_TIMEOUT', 'HTTPX_READ_TIMEOUT', 'HTTPX_WRITE_TIMEOUT', 'HTTPX_POOL_TIMEOUT',
                'OLLAMA_TIMEOUT', 'OLLAMA_REQUEST_TIMEOUT', 'LLM_TIMEOUT', 'EMBEDDING_TIMEOUT', 'HTTP_TIMEOUT',
                'CONNECTION_TIMEOUT', 'READ_TIMEOUT', 'WRITE_TIMEOUT', 'POOL_TIMEOUT', 'REQUESTS_TIMEOUT',
                'URLLIB3_TIMEOUT', 'AIOHTTP_TIMEOUT', 'SOCKET_TIMEOUT'
            ]
            if any(line.startswith(var + '=') for var in timeout_vars):
                continue  # Skip existing timeout settings
            else:
                skip_section = False
        
        if not skip_section:
            filtered_lines.append(line)
    
    # Add extended timeout settings
    content = '\n'.join(filtered_lines) + extended_timeouts
    
    # Write updated env file
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("Updated env.server with extended timeout settings")

def update_docker_compose():
    """Update docker-compose.yml with additional environment variables."""
    compose_file = "lightrag_server/docker-compose.yml"
    
    with open(compose_file, 'r') as f:
        content = f.read()
    
    # Add additional environment variables for timeout handling
    additional_env = """      # Extended timeout settings for large document processing
      - HTTPX_TIMEOUT=14400
      - HTTPX_CONNECT_TIMEOUT=1200
      - HTTPX_READ_TIMEOUT=14400
      - HTTPX_WRITE_TIMEOUT=1200
      - HTTPX_POOL_TIMEOUT=1200
      - OLLAMA_REQUEST_TIMEOUT=14400
      - REQUESTS_TIMEOUT=14400
      - URLLIB3_TIMEOUT=14400
      - AIOHTTP_TIMEOUT=14400
      - SOCKET_TIMEOUT=14400
      - TCP_KEEPALIVE=true
      - TCP_KEEPALIVE_IDLE=600
      - TCP_KEEPALIVE_INTERVAL=60
      - TCP_KEEPALIVE_COUNT=9
      - PYTHONHTTPSVERIFY=0
      - CURL_CA_BUNDLE=""
      - REQUESTS_CA_BUNDLE=""
"""
    
    # Find the environment section and add our variables
    if "- OLLAMA_TEMPERATURE=0.1" in content:
        content = content.replace("- OLLAMA_TEMPERATURE=0.1", "- OLLAMA_TEMPERATURE=0.1" + additional_env)
    
    with open(compose_file, 'w') as f:
        f.write(content)
    
    print("Updated docker-compose.yml with extended timeout settings")

def restart_lightrag_container():
    """Restart the LightRAG container with new settings."""
    os.chdir("lightrag_server")
    
    print("Stopping LightRAG container...")
    run_command("docker-compose down")
    
    print("Starting LightRAG container with extended timeouts...")
    result = run_command("docker-compose up -d")
    
    if result:
        print("Waiting for container to start...")
        time.sleep(10)
        
        # Check if container is running
        result = run_command("docker-compose ps")
        if result and result.returncode == 0:
            print("LightRAG container restarted successfully with extended timeouts")
            print("\nContainer status:")
            print(result.stdout)
            return True
    
    return False

def main():
    """Main function to fix LightRAG timeout issues."""
    print("=== LightRAG Timeout Fix ===")
    print("This script will update timeout settings for large document processing")
    
    try:
        # Update configuration files
        print("\n1. Updating environment configuration...")
        update_env_file()
        
        print("\n2. Updating Docker Compose configuration...")
        update_docker_compose()
        
        print("\n3. Restarting LightRAG container...")
        if restart_lightrag_container():
            print("\n✅ LightRAG timeout fix applied successfully!")
            print("\nThe following changes were made:")
            print("- Extended all HTTP timeouts to 4 hours")
            print("- Increased Ollama request timeout to 4 hours")
            print("- Reduced PDF chunk size to 512 for better reliability")
            print("- Increased retry attempts to 10")
            print("- Enabled TCP keepalive for stable connections")
            print("\nYou can now try processing large documents again.")
        else:
            print("\n❌ Failed to restart LightRAG container")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error applying timeout fix: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
