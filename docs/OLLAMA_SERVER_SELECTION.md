# Ollama Server Selection

The Personal AI Agent now supports the ability to switch between local and remote Ollama servers, making it easy to use more powerful models running on a remote machine when needed.

## Usage

### Command Line Interface

To run the agent with the local Ollama server (default):

```bash
# Activate virtual environment
source .venv/bin/activate

# Run with local Ollama (default)
python -m personal_agent.agno_main --cli
```

To run the agent with a remote Ollama server (on tesla.local):

```bash
# Activate virtual environment
source .venv/bin/activate

# Run with remote Ollama
python -m personal_agent.agno_main --cli --remote-ollama
```

### Web Interface

To run the web interface with the local Ollama server (default):

```bash
# Activate virtual environment
source .venv/bin/activate

# Run with local Ollama (default)
python -m personal_agent.agno_main
```

To run the web interface with a remote Ollama server (on tesla.local):

```bash
# Activate virtual environment
source .venv/bin/activate

# Run with remote Ollama
python -m personal_agent.agno_main --remote-ollama
```

## Configuration

The remote Ollama URL is configured to use `http://tesla.local:11434` when the `--remote-ollama` flag is specified. The local Ollama URL is determined by the `OLLAMA_URL` environment variable, which defaults to `http://localhost:11434` if not set.

You can modify these values in the following ways:

1. To change the local Ollama URL, update the `OLLAMA_URL` in your `.env` file:

   ```
   OLLAMA_URL=http://localhost:11434
   ```

2. To change the remote Ollama URL, modify the `initialize_agno_system` function in `agno_main.py`:

   ```python
   if use_remote_ollama:
       ollama_url = "http://your-custom-server:11434"
   ```

## Benefits

- **Flexibility**: Easily switch between local and remote Ollama servers
- **Performance**: Use more powerful models running on dedicated hardware
- **Convenience**: Run lightweight models locally for quick tasks
