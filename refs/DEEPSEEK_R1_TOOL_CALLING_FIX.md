# DeepSeek-R1 Tool Calling Error Fix

## Problem Description

The Personal AI Agent was failing to start with the following error when using the `deepseek-r1:1.5b` model:

```
💥 Error: registry.ollama.ai/library/deepseek-r1:1.5b does not support tools (status code: 400)
```

## Root Cause

The `deepseek-r1:1.5b` model does not support function calling/tools, which is essential for the Personal AI Agent system that relies on 28+ tools including:
- 6 MCP servers (filesystem, GitHub, Brave search, Puppeteer)
- 15 memory management tools
- Built-in tools (Google search, YFinance, Python execution, etc.)

## Solution

### 1. Identify Compatible Models

Based on the agent's model manager configuration (`src/personal_agent/core/agent_model_manager.py`), the following model families support function calling:

**Recommended Models (Available on System):**
- **Qwen models**: `qwen3:1.7B`, `qwen3:4b`, `qwen3:8b`, `qwen2.5:7b-instruct`
- **Llama models**: `llama3.2:3b`, `llama3.1:8b-instruct-q8_0`
- **SmolLM2 models**: `smollm2:1.7B` (has optimized configuration)

### 2. Update Configuration

Change the model in `.env` file:

```bash
# Before (causing error)
LLM_MODEL=deepseek-r1:1.5b

# After (working solution)
LLM_MODEL=qwen3:8b
```

### 3. Verification

After the change, the agent should:
- Start without tool-related errors
- Load all 28+ tools successfully
- Process user input normally
- Show "Model: qwen3:8b" in debug logs

## Model Comparison

| Model | Function Calling | Context Size | Parameter Size | Status |
|-------|------------------|--------------|----------------|---------|
| `deepseek-r1:1.5b` | ❌ No | 4096 | 1.8B | **Incompatible** |
| `qwen3:8b` | ✅ Yes | 40960 | 8.2B | **Recommended** |
| `qwen3:4b` | ✅ Yes | 40960 | 4.0B | Good alternative |
| `llama3.2:3b` | ✅ Yes | 131072 | 3.2B | Good alternative |
| `smollm2:1.7B` | ✅ Yes | 8192 | 1.7B | Optimized config |

## Alternative Models

If `qwen3:8b` is not available or too resource-intensive, try these alternatives in order:

1. `qwen3:4b` - Good balance of performance and resource usage
2. `llama3.2:3b` - Large context window (131K tokens)
3. `qwen3:1.7B` - Smallest Qwen model with tool support
4. `smollm2:1.7B` - Has special optimized configuration

## Technical Details

### Model Manager Configuration

The agent's model manager (`AgentModelManager`) has special handling for:

- **Qwen models**: Optimized parameters for tool calling
- **SmolLM2 models**: Deterministic generation with specific stop tokens
- **Reasoning models**: Enhanced reasoning capabilities for compatible models

### Context Size Detection

The system automatically detects context sizes using:
1. Environment variable overrides
2. Ollama API queries
3. Model name pattern extraction
4. Curated database lookup
5. Default fallback (4096 tokens)

## Testing

To verify the fix works:

```bash
poetry run paga_cli --instruction-level MINIMAL
```

Expected output should show:
- No tool-related errors
- Model loading successfully
- All tools being added to the agent
- Normal greeting response to "hello!"

## Prevention

To avoid this issue in the future:

1. **Check tool support** before switching models
2. **Test with simple greeting** after model changes
3. **Monitor debug logs** for tool loading errors
4. **Use recommended models** from the compatibility list above

## Related Files

- `.env` - Model configuration
- `src/personal_agent/core/agent_model_manager.py` - Model creation logic
- `src/personal_agent/config/model_contexts.py` - Context size database
- `src/personal_agent/config/settings.py` - Environment settings

## Date Fixed

January 23, 2025

## Status

✅ **RESOLVED** - Agent now works with `qwen3:8b` model and all tools load successfully.