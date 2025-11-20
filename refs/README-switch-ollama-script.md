# Switch Ollama Script Documentation

## Overview

The `switch-ollama.sh` script is a comprehensive bash utility that manages switching between local and remote Ollama server configurations for a multi-service AI system. It handles configuration updates, service restarts, and connectivity testing across multiple components including Ollama, LightRAG, and memory services.

## Script Purpose

This script enables seamless switching between:
- **Local Mode**: Uses localhost/host.docker.internal for all services
- **Remote Mode**: Uses 100.115.62.30 for all services

## Configuration Variables

### URL Definitions
```bash
LOCAL_URL="http://localhost:11434"
LOCAL_DOCKER_URL="http://host.docker.internal:11434"
REMOTE_URL="http://100.115.62.30:11434"
REMOTE_DOCKER_URL="http://100.115.62.30:11434"
LOCAL_LIGHTRAG_URL="http://localhost:9621"
REMOTE_LIGHTRAG_URL="http://100.115.62.30:9621"
LOCAL_EMBEDDING_BINDING_HOST="http://host.docker.internal:11434"
REMOTE_EMBEDDING_BINDING_HOST="http://100.115.62.30:11434"
```

### Environment Variables Updated

When switching modes, the script updates these 4 variables in the `.env` file:

| Variable | Local Value | Remote Value |
|----------|-------------|--------------|
| `OLLAMA_URL` | `http://localhost:11434` | `http://100.115.62.30:11434` |
| `OLLAMA_DOCKER_URL` | `http://host.docker.internal:11434` | `http://100.115.62.30:11434` |
| `LIGHTRAG_URL` | `http://localhost:9621` | `http://100.115.62.30:9621` |
| `EMBEDDING_BINDING_HOST` | `http://host.docker.internal:11434` | `http://100.115.62.30:11434` |

## Commands

### Usage
```bash
./switch-ollama.sh {local|remote|status}
```

### Available Commands

1. **local** - Switch to local Ollama server (host.docker.internal:11434)
2. **remote** - Switch to remote Ollama server (100.115.62.30:11434)
3. **status** - Show current Ollama configuration

## Key Functions

### `backup_env()`
- Creates timestamped backups of the `.env` file
- Stores backups in the `backups/` directory
- Format: `.env.backup.YYYYMMDD_HHMMSS`

### `get_current_url()`
- Extracts the current `OLLAMA_URL` from the `.env` file
- Used to determine current configuration state

### `show_status()`
- Displays current Ollama configuration
- Shows whether system is in LOCAL, REMOTE, or CUSTOM mode
- Color-coded output for easy identification

### `test_ollama_connection()`
- Tests connectivity to the specified Ollama server
- Uses curl to check `/api/tags` endpoint
- Provides feedback on server reachability

### `update_urls()`
- Core function that updates all 4 environment variables
- Uses sed to perform in-place replacements
- Validates changes before committing
- Updates:
  - `OLLAMA_URL`
  - `OLLAMA_DOCKER_URL`
  - `LIGHTRAG_URL`
  - `EMBEDDING_BINDING_HOST`

### `restart_docker_services()`
- Changes to `lightrag_server` directory
- Stops existing Docker services with `docker-compose down`
- Starts services with `docker-compose up -d`
- Waits for initialization and shows service status
- Returns to original directory

### `switch_memory_server()`
- Calls external Python script `switch-lightrag-memory-server.py`
- Passes the mode (local/remote/status) as parameter
- Uses python3 with fallback to python
- Handles memory server configuration switching

## Workflow

### Local Mode Switch
1. Check if already in local mode
2. Backup current `.env` file
3. Update all 4 environment variables to local values
4. Test Ollama connectivity
5. Restart LightRAG Docker services
6. Switch memory server to local mode
7. Display final status

### Remote Mode Switch
1. Check if already in remote mode
2. Backup current `.env` file
3. Update all 4 environment variables to remote values
4. Test Ollama connectivity
5. Restart LightRAG Docker services
6. Switch memory server to remote mode
7. Display final status

### Status Check
1. Display current configuration
2. Test connectivity to current Ollama server
3. Show Docker service status
4. Call memory server status check

## Dependencies

### External Scripts
- `switch-lightrag-memory-server.py` - Handles memory server switching

### Required Directories
- `lightrag_server/` - Contains Docker Compose configuration
- `backups/` - Created automatically for .env backups

### Required Files
- `.env` - Main environment configuration file
- `lightrag_server/docker-compose.yml` - Docker services configuration

## Error Handling

- Validates directory existence before operations
- Checks for required files before execution
- Provides colored output for success/failure states
- Returns appropriate exit codes for automation
- Validates configuration changes before committing

## Color Coding

- **RED**: Errors and failures
- **GREEN**: Success messages and confirmations
- **YELLOW**: Warnings and informational messages
- **BLUE**: Headers and section dividers
- **NC**: No color (reset)

## Integration Points

The script integrates with:
1. **Main .env configuration** - Updates primary environment variables
2. **LightRAG Docker services** - Restarts containerized services
3. **Memory server system** - Coordinates memory service switching
4. **Ollama server** - Tests connectivity and manages endpoints

## Best Practices

1. Always creates backups before making changes
2. Validates changes before committing
3. Tests connectivity after configuration updates
4. Provides comprehensive status information
5. Handles both Docker and native service configurations
6. Supports both local development and remote deployment scenarios

## Troubleshooting

- Check that `lightrag_server/` directory exists
- Ensure Docker and docker-compose are installed
- Verify network connectivity to 100.115.62.30 for remote mode
- Check that required Python scripts are present
- Review backup files if rollback is needed
