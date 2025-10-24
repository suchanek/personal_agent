# LM Studio Provider Integration

This document describes how to use the new LM Studio provider with the Personal AI Agent.

## Overview

The LM Studio provider allows you to use locally running LM Studio models with the Personal AI Agent. It follows the LM Studio documentation example exactly, using a direct OpenAI client for maximum compatibility.

## Configuration

### Environment Variables

Set these environment variables to use LM Studio:

```bash
# Required: Set provider to lm-studio
PROVIDER=lm-studio

# Required: Specify your LM Studio model
LLM_MODEL=qwen3-4b-mlx

# Required: LM Studio server URL
LMSTUDIO_BASE_URL=http://100.73.95.100:1234

# Optional: Override context size for specific models
QWEN3_4B_MLX_CTX_SIZE=32768
```

### Example .env Configuration

```bash
# LM Studio Configuration
PROVIDER=lm-studio
LLM_MODEL=qwen3-4b-mlx
LMSTUDIO_BASE_URL=http://100.73.95.100:1234
QWEN3_4B_MLX_CTX_SIZE=32768
```

## Usage

### Basic Usage

```python
from personal_agent.core.agno_agent import AgnoPersonalAgent

# Create agent with LM Studio provider
agent = AgnoPersonalAgent(
    model_provider="lm-studio",
    model_name="qwen3-4b-mlx",
    lmstudio_base_url="http://100.73.95.100:1234",
    enable_memory=False,  # Recommended for LM Studio
    debug=True
)

# Initialize the agent
await agent.initialize()

# Use the agent (note: some limitations apply)
response = await agent.run("Hello! What's 2 + 2?", stream=False)
print(response)
```

### Streamlit Integration

The Streamlit app automatically detects LM Studio configuration:

1. Set your environment variables as shown above
2. Run the Streamlit app: `streamlit run src/personal_agent/streamlit/persag_app.py`
3. The app will automatically use LM Studio when `PROVIDER=lm-studio`

## Features

### ✅ Working Features

- **Model Creation**: Successfully creates LM Studio models
- **Agent Initialization**: Properly initializes with LM Studio provider
- **Server Connectivity**: Connects to LM Studio servers
- **Configuration**: Supports flexible URL and model configuration
- **Context Size**: Automatically configures appropriate context sizes
- **Tool Integration**: Supports built-in tools (Calculator, DuckDuckGo, etc.)

### ⚠️ Known Limitations

- **Memory System**: Agno's memory system has deepcopy issues with OpenAI clients
  - **Workaround**: Set `enable_memory=False` when creating agents
- **Streaming**: Some streaming features may have limitations
- **Complex Queries**: Very complex queries may encounter threading issues

## Architecture

The LM Studio provider uses a clean architecture:

1. **AgentModelManager**: Handles model creation and configuration
2. **Official Agno LMStudio**: Uses `agno.models.lmstudio.LMStudio` class (native support!)
3. **Configuration**: Unified configuration through environment variables
4. **Context Management**: Automatic context size configuration per model

## Testing

Run the test suite to verify your LM Studio setup:

```bash
# Test provider functionality
python test_lmstudio_provider.py

# Test integration (may show known limitations)
python test_lmstudio_integration.py
```

## Troubleshooting

### Common Issues

1. **Connection Errors**
   - Ensure LM Studio is running and serving on the specified port
   - Check that the model is loaded in LM Studio
   - Verify the URL is accessible from your machine

2. **Model Not Found**
   - Ensure the model name matches exactly what's loaded in LM Studio
   - Check LM Studio's model list at `http://your-url:1234/v1/models`

3. **Memory/Deepcopy Errors**
   - Set `enable_memory=False` when creating agents
   - This is a known limitation with OpenAI client serialization

### Debug Mode

Enable debug mode for detailed logging:

```python
agent = AgnoPersonalAgent(
    model_provider="lm-studio",
    debug=True,  # Enable detailed logging
    enable_memory=False
)
```

## Model Support

The provider supports any model running in LM Studio. Tested models include:

- `qwen3-4b-mlx` (32K context)
- `qwen3-8b-mlx` (32K context)
- `qwen3-1.7b` (32K context)

Context sizes are automatically configured based on model specifications.

## Implementation Details

The LM Studio provider:

1. Uses direct OpenAI client (exactly like LM Studio documentation)
2. Handles message format conversion between Agno and OpenAI
3. Supports tool calling through OpenAI's tools parameter
4. Manages context sizes automatically
5. Provides proper error handling and logging

## Future Improvements

Potential enhancements:

- [ ] Resolve deepcopy/memory system limitations
- [ ] Enhanced streaming support
- [ ] Better error recovery
- [ ] Model auto-detection from LM Studio
- [ ] Performance optimizations

## Support

For issues with the LM Studio provider:

1. Check the test results with `python test_lmstudio_provider.py`
2. Verify LM Studio server is running and accessible
3. Review the debug logs when `debug=True`
4. Ensure environment variables are set correctly
