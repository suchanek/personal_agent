# LightRAG Server Environment Variable Consolidation

## Overview

This document summarizes the environment variable consolidation performed for both the `lightrag_server` and `lightrag_memory_server` directories. The goal was to move all environment variables from the `docker-compose.yml` files into their respective env files, creating a single source of truth for configuration.

## Changes Made

### For lightrag_memory_server:

1. **Updated env.memory_server**:
   - Added all variables from docker-compose.yml's environment section
   - Changed PDF_CHUNK_SIZE from 2048 to 512 to match the docker-compose.yml value
   - Added new sections for CHUNK SETTINGS, WORKER SETTINGS, ADDITIONAL OLLAMA SETTINGS, etc.

2. **Updated docker-compose.yml**:
   - Removed the entire environment section
   - Kept all other configuration (volumes, ports, healthcheck, etc.)

### For lightrag_server:

1. **Updated env.server**:
   - Added the following variables from docker-compose.yml:
     - CHUNK_SIZE=512
     - CHUNK_OVERLAP_SIZE=100
     - MAX_PARALLEL_INSERT=1
   - Added these to the "Processing Configuration" section
   - All other variables were already present with identical values

2. **Updated docker-compose.yml**:
   - Removed the entire environment section
   - Kept all other configuration (build, volumes, ports, healthcheck, etc.)

## Benefits

1. **Single Source of Truth**: All environment variables are now defined in one place
2. **Simplified Maintenance**: Easier to update and manage environment variables
3. **Cleaner Docker Configuration**: The docker-compose.yml files are more concise and focused on container configuration
4. **Consistent Configuration**: Eliminates the risk of inconsistent values between files

## Testing Instructions

To test these changes, you'll need to:

1. **Copy env files to .env**:
   ```bash
   cp lightrag_memory_server/env.memory_server lightrag_memory_server/.env
   cp lightrag_server/env.server lightrag_server/.env
   ```

2. **Restart the Docker containers**:
   ```bash
   # For lightrag_memory_server
   cd lightrag_memory_server
   docker-compose down
   docker-compose up -d

   # For lightrag_server
   cd lightrag_server
   docker-compose down
   docker-compose up -d
   ```

3. **Verify the containers are running correctly**:
   ```bash
   docker-compose ps
   ```
   The containers should be in the "Up" state.

4. **Check the container logs for any errors**:
   ```bash
   docker-compose logs
   ```
   There should be no errors related to missing environment variables.

5. **Verify the applications are accessible**:
   - LightRAG Memory Server: http://localhost:9622/webui
   - LightRAG Server: http://localhost:9621/webui

## Troubleshooting

If you encounter any issues:

1. **Check if all environment variables are being passed correctly**:
   ```bash
   docker-compose exec lightrag env | sort
   ```
   This will show all environment variables inside the container.

2. **Verify the .env file was mounted correctly**:
   ```bash
   docker-compose exec lightrag ls -la /app/.env
   ```
   This should show the .env file in the container.

3. **If needed, revert to the previous configuration**:
   ```bash
   # Restore the original files from backups if you created them
   ```

## Conclusion

The environment variable consolidation simplifies the configuration management for both LightRAG servers. All environment variables are now defined in a single place, making it easier to maintain and update the configuration.