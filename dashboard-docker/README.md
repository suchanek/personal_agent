# Personal Agent Dashboard - Docker Edition

A standalone Docker container for the Personal Agent Management Dashboard. This containerized version provides all the dashboard functionality while connecting to external Personal Agent services.

## 🚀 Quick Start

### Prerequisites
- Docker installed and running
- Personal Agent services running (LightRAG, Ollama, etc.) - optional but recommended

### Build and Run
```bash
# Build the Docker image
./build.sh

# Run the dashboard
./run.sh
```

The dashboard will be available at: **http://localhost:8501**

### Using Docker Compose
```bash
# Start with docker-compose
docker-compose up -d

# Stop
docker-compose down
```

## 📋 Features

- **System Status**: Monitor system resources, memory usage, and service health
- **User Management**: Manage users and user configurations
- **Memory Management**: View and manage agent memories and knowledge
- **Docker Services**: Monitor and manage Docker containers
- **Theme Support**: Light and dark mode themes
- **Graceful Shutdown**: Safe container shutdown functionality

## 🔧 Configuration

### Environment Variables

The dashboard can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LIGHTRAG_URL` | `http://host.docker.internal:9621` | LightRAG service URL |
| `LIGHTRAG_MEMORY_URL` | `http://host.docker.internal:9622` | LightRAG memory service URL |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Ollama service URL |
| `USER_ID` | `dashboard_user` | Current user ID |
| `LOG_LEVEL` | `INFO` | Logging level |
| `STREAMLIT_SERVER_PORT` | `8501` | Dashboard port |

### Custom Configuration

Create a `.env` file in the dashboard-docker directory:

```bash
# External Services
LIGHTRAG_URL=http://your-lightrag-server:9621
OLLAMA_URL=http://your-ollama-server:11434

# Dashboard Settings
USER_ID=your_user_id
LOG_LEVEL=DEBUG
```

## 🐳 Docker Commands

### Basic Operations
```bash
# Build image
docker build -t personal-agent-dashboard:latest .

# Run container
docker run -d -p 8501:8501 --name personal-agent-dashboard personal-agent-dashboard:latest

# View logs
docker logs -f personal-agent-dashboard

# Stop container
docker stop personal-agent-dashboard

# Remove container
docker rm personal-agent-dashboard
```

### Advanced Usage
```bash
# Run with custom environment variables
docker run -d \
  -p 8501:8501 \
  -e LIGHTRAG_URL=http://custom-server:9621 \
  -e USER_ID=custom_user \
  --name personal-agent-dashboard \
  personal-agent-dashboard:latest

# Run with volume mounts for data persistence
docker run -d \
  -p 8501:8501 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  --name personal-agent-dashboard \
  personal-agent-dashboard:latest
```

## 📁 Directory Structure

```
dashboard-docker/
├── Dockerfile              # Multi-stage Docker build
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── build.sh                # Build script
├── run.sh                  # Run script
├── README.md               # This file
├── .dockerignore           # Docker ignore rules
├── config/                 # Configuration files
├── src/                    # Application source code
│   └── personal_agent/     # Personal Agent modules
│       ├── streamlit/      # Dashboard and components
│       ├── core/           # Core functionality
│       ├── config/         # Configuration modules
│       ├── tools/          # Tool modules
│       └── utils/          # Utility modules
└── static/                 # Static assets (CSS, etc.)
    └── css/
        └── dark_theme.css  # Dark theme styling
```

## 🔗 External Service Integration

The dashboard connects to external Personal Agent services:

### LightRAG Services
- **LightRAG Server** (port 9621): Knowledge and memory management
- **LightRAG Memory Server** (port 9622): Memory-specific operations

### Ollama Service
- **Ollama Server** (port 11434): AI model serving

### Docker Integration
- **Docker Socket**: Container management (mounted read-only)

## 🛠️ Development

### Modifying the Dashboard

1. Edit files in the `src/` directory
2. Rebuild the image: `./build.sh`
3. Restart the container: `./run.sh`

### Adding Dependencies

1. Update `requirements.txt`
2. Rebuild the image: `./build.sh`

### Debugging

```bash
# Run container in interactive mode
docker run -it --rm -p 8501:8501 personal-agent-dashboard:latest bash

# View detailed logs
docker logs -f personal-agent-dashboard

# Execute commands in running container
docker exec -it personal-agent-dashboard bash
```

## 🔒 Security Considerations

- Container runs as non-root user (`dashboard`)
- Docker socket mounted read-only
- No sensitive data stored in image
- Environment variables for configuration
- Resource limits configured in docker-compose.yml

## 🚨 Troubleshooting

### Common Issues

**Dashboard won't start:**
- Check if port 8501 is available
- Verify Docker is running
- Check container logs: `docker logs personal-agent-dashboard`

**External services not connecting:**
- Verify service URLs in environment variables
- Check if services are running and accessible
- For macOS/Windows: Use `host.docker.internal` instead of `localhost`

**Memory/performance issues:**
- Adjust resource limits in docker-compose.yml
- Monitor container resources: `docker stats personal-agent-dashboard`

### Health Checks

The container includes health checks:
```bash
# Check container health
docker inspect personal-agent-dashboard | grep -A 10 Health

# Manual health check
curl -f http://localhost:8501/_stcore/health
```

## 📝 Logs

Logs are available in multiple ways:
- Container logs: `docker logs personal-agent-dashboard`
- Mounted log directory: `./logs/` (if volume mounted)
- Streamlit logs: Available in the dashboard interface

## 🤝 Contributing

To contribute to the dashboard:

1. Make changes in the main Personal Agent repository
2. Copy updated files to the dashboard-docker directory
3. Test the changes in the container
4. Update documentation as needed

## 📄 License

This project follows the same license as the main Personal Agent project.
