# Dynamic Model Context Size Detection

This document explains the new dynamic context size detection system that automatically configures the optimal context window size for different LLM models.

## Overview

Previously, the system used a hardcoded context size of 8192 tokens for all models. Now, each model automatically gets its optimal context size based on its actual capabilities.

## How It Works

The system uses a multi-tier detection approach:

1. **Environment Variable Override** (highest priority)
2. **Ollama API Query** (when available)
3. **Model Name Pattern Extraction**
4. **Curated Database Lookup**
5. **Default Fallback** (4096 tokens for unknown models)

## Supported Models

The system currently supports 42+ models including:

### Qwen Models (32K context)
- `qwen3:1.7b`, `qwen3:7b`, `qwen3:14b`
- `qwen2.5:0.5b` through `qwen2.5:72b`

### Llama 3.1/3.2 Models (128K context)
- `llama3.1:8b`, `llama3.1:8b-instruct-q8_0`, `llama3.1:70b`, `llama3.1:405b`
- `llama3.2:1b`, `llama3.2:3b`, `llama3.2:11b`, `llama3.2:90b`

### Llama 3 Models (8K context)
- `llama3:8b`, `llama3:70b`

### Mistral Models (32K-64K context)
- `mistral:7b`, `mistral:instruct` (32K)
- `mixtral:8x7b` (32K), `mixtral:8x22b` (64K)

### Phi Models (128K context)
- `phi3:3.8b`, `phi3:14b`, `phi3.5:3.8b`

### Other Models
- CodeLlama, Gemma, Neural Chat, Orca, Vicuna models

## Environment Variable Overrides

You can override context sizes for specific models using environment variables:

```bash
# Override for specific model (replace : with _ and . with _)
export QWEN3_1_7B_CTX_SIZE=16384
export LLAMA3_1_8B_INSTRUCT_Q8_0_CTX_SIZE=65536

# Set default for unknown models
export DEFAULT_MODEL_CTX_SIZE=8192
```

Add these to your `.env` file:

```env
# MODEL CONTEXT SIZE OVERRIDES
QWEN3_1_7B_CTX_SIZE=16384
LLAMA3_1_8B_INSTRUCT_Q8_0_CTX_SIZE=65536
DEFAULT_MODEL_CTX_SIZE=8192
```

## Usage Examples

### Automatic Detection
```python
from src.personal_agent.config.model_contexts import get_model_context_size_sync

# Get context size for your model
context_size, method = get_model_context_size_sync("qwen3:1.7b")
print(f"Context size: {context_size} tokens (detected via: {method})")
# Output: Context size: 32768 tokens (detected via: database_lookup)
```

### Adding New Models
```python
from src.personal_agent.config.model_contexts import add_model_to_database

# Add a new model to the database
add_model_to_database("custom-model:7b", 16384)
```

### Getting Model Summary
```python
from src.personal_agent.config.model_contexts import get_context_size_summary

summary = get_context_size_summary("qwen3:1.7b")
print(summary)
```

## Integration with Agno Agent

The dynamic context sizing is automatically integrated into the `AgnoPersonalAgent`. When you create an agent, it will:

1. Detect the optimal context size for your model
2. Log the detection method used
3. Configure the Ollama model with the correct `num_ctx` parameter

```python
# Your agent will automatically use optimal context size
agent = AgnoPersonalAgent(model_name="qwen3:1.7b")
await agent.initialize()
# Logs: "Using context size 32768 for model qwen3:1.7b (detected via: database_lookup)"
```

## Testing

Run the test script to verify context size detection:

```bash
# Quick synchronous test
python test_context_detection.py --sync-only

# Full test with Ollama API queries
python test_context_detection.py
```

## Benefits

✅ **Automatic Optimization**: Each model uses its full context capacity  
✅ **Better Performance**: No more wasted context or truncated conversations  
✅ **Easy Configuration**: Override any model's context size via environment variables  
✅ **Extensible**: Easy to add new models to the database  
✅ **Fallback Safety**: Unknown models get a safe default context size  
✅ **Multiple Detection Methods**: Robust detection with multiple fallback strategies  

## Current Model Context Sizes

Your current configuration:
- **Model**: `qwen3:1.7B`
- **Context Size**: 32,768 tokens (32K)
- **Detection Method**: Database lookup

This means your model can now handle much longer conversations and documents compared to the previous 8K limit!

## Troubleshooting

### Model Not Recognized
If your model isn't in the database, it will use the default 4096 tokens. You can:
1. Add it to the database using `add_model_to_database()`
2. Set an environment variable override
3. Submit a request to add it to the built-in database

### Context Size Too Large
If you experience memory issues, you can reduce the context size:
```bash
export YOUR_MODEL_NAME_CTX_SIZE=8192
```

### Ollama API Errors
The system gracefully falls back to other detection methods if Ollama API queries fail.

## Future Enhancements

- Automatic context size detection from model files
- Dynamic adjustment based on available memory
- Model-specific optimization parameters
- Integration with other LLM providers (OpenAI, Anthropic, etc.)
