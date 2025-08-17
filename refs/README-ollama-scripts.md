# Ollama Server Management Scripts

These scripts help you easily switch between local and remote Ollama servers and manage Docker services.

## Scripts

### `switch-ollama.sh` - Main switching script
Switches between local and remote Ollama servers and restarts Docker services.

**Usage:**
```bash
./switch-ollama.sh {local|remote|status}
```

**Commands:**
- `local` - Switch to local Ollama server (host.docker.internal:11434)
- `remote` - Switch to remote Ollama server (tesla.tail19187e.ts.net:11434)  
- `status` - Show current configuration and test connectivity

**Examples:**
```bash
# Switch to local Ollama
./switch-ollama.sh local

# Switch to remote Ollama (tesla.tail19187e.ts.net)
./switch-ollama.sh remote

# Check current status
./switch-ollama.sh status
```

### `restart-lightrag.sh` - Simple restart script
Just restarts Docker services without changing configuration.

**Usage:**
```bash
./restart-lightrag.sh
```

## What the scripts do

### When switching servers:
1. **Backup** - Creates timestamped backup of your `.env` file in `backups/` directory
2. **Update** - Changes `OLLAMA_URL` in `.env` file
3. **Test** - Tests connectivity to the Ollama server (optional, won't fail if unreachable)
4. **Restart** - Runs `docker-compose down && docker-compose up -d`
5. **Status** - Shows service status and current configuration

### Configuration Details:
- **Local**: `OLLAMA_URL=http://host.docker.internal:11434`
  - Uses Docker's special hostname to reach your host machine
  - For when Ollama is running locally on your Mac
  
- **Remote**: `OLLAMA_URL=http://tesla.tail19187e.ts.net:11434`
  - Points to your remote Ollama server
  - For when using your tesla.tail19187e.ts.net server

## Features

- ✅ **Colored output** for easy reading
- ✅ **Automatic backups** of .env file before changes
- ✅ **Connectivity testing** (optional, won't block if server is down)
- ✅ **Error handling** with rollback capability
- ✅ **Status checking** to avoid unnecessary restarts
- ✅ **Docker service management** with proper startup waiting

## File Structure

```
.
├── switch-ollama.sh          # Main switching script
├── restart-lightrag.sh       # Simple restart script
├── .env                      # Environment configuration
├── docker-compose.yml        # Docker services
└── backups/                  # Automatic .env backups
    ├── .env.backup.20231225_120000
    └── .env.backup.20231225_130000
```

## Troubleshooting

### "Cannot reach Ollama server"
This is normal if:
- The server is not currently running
- Network connectivity issues
- The server is starting up

The script will continue anyway since this is just a connectivity test.

### "Failed to restart Docker services"
Check:
- Docker is running
- No port conflicts
- `docker-compose.yml` is valid

### Script permissions
If you get permission denied:
```bash
chmod +x switch-ollama.sh restart-lightrag.sh
```

## Environment Variables

The scripts modify these variables in your `.env` file:
- `OLLAMA_URL` - Main Ollama server URL
- `EMBEDDING_BINDING_HOST=${OLLAMA_URL}` - Uses same URL for embeddings
- `LLM_BINDING_HOST=${OLLAMA_URL}` - Uses same URL for LLM

This ensures all LightRAG components use the same Ollama server.
