# Fact Storage Utility

This utility allows you to store facts directly in the Personal AI Agent's knowledge base (Weaviate vector database).

## Usage

### From Project Root

```bash
# Activate virtual environment
source .venv/bin/activate

# Store a simple fact
python store_fact.py "Python was created by Guido van Rossum"

# Store a fact with a specific topic
python store_fact.py "The speed of light is 299,792,458 m/s" --topic "physics"

# Store and verify the fact was saved
python store_fact.py "My favorite coffee shop is downtown" --topic "personal" --verify

# Quiet mode (minimal output)
python store_fact.py "Earth has one moon" --topic "astronomy" --quiet
```

### Using the Module

```bash
# From project root
python -m personal_agent.utils.store_fact "Your fact here" --topic "category"
```

## Options

- `--topic, -t`: Specify the topic category (default: "fact")
- `--verify, -v`: Verify the fact was stored by searching for it
- `--quiet, -q`: Suppress verbose output
- `--help, -h`: Show help message

## Examples

```bash
# Technology facts
python store_fact.py "GitHub Copilot is an AI programming assistant" --topic "technology"

# Science facts
python store_fact.py "Water boils at 100°C at sea level" --topic "science"

# Personal information
python store_fact.py "I prefer dark roast coffee" --topic "personal"

# Programming tips
python store_fact.py "Use virtual environments for Python projects" --topic "programming"
```

## Requirements

1. **Weaviate Running**: The Weaviate database must be running

   ```bash
   docker-compose up -d
   ```

2. **Virtual Environment**: Activate the project's virtual environment

   ```bash
   source .venv/bin/activate
   ```

3. **Environment Variables**: Ensure your `.env` file is properly configured

## How It Works

1. **Connection**: The script connects to the Weaviate vector database
2. **Embedding**: Facts are converted to vector embeddings using Ollama's `nomic-embed-text` model
3. **Storage**: Facts are stored with metadata including timestamp and topic
4. **Retrieval**: Stored facts can be queried by the AI agent using semantic similarity

## Integration with AI Agent

Once facts are stored, they become part of the AI agent's knowledge base and can be:

- **Queried**: Ask the agent questions related to stored facts
- **Retrieved**: Facts are automatically included in relevant conversations
- **Searched**: Use semantic similarity to find related information

## Troubleshooting

### "Cannot connect to Weaviate"

- Ensure Weaviate is running: `docker-compose up -d`
- Check if port 8080 is available: `curl http://localhost:8080/v1/.well-known/ready`

### "Weaviate is disabled"

- Check your `.env` file has `USE_WEAVIATE=true`
- Verify configuration in `src/personal_agent/config/settings.py`

### Import Errors

- Activate virtual environment: `source .venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt` or `poetry install`

## File Locations

- **Main script**: `store_fact.py` (project root)
- **Module**: `src/personal_agent/utils/store_fact.py`
- **Simple version**: `src/personal_agent/utils/store_fact_simple.py`
