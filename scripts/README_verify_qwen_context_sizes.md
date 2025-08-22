# Qwen Model Context Size Verification Script

This script verifies that the context sizes configured in `src/personal_agent/config/model_contexts.py` match the actual context sizes reported by Ollama for Qwen models.

## Purpose

The script helps ensure that:
- All Qwen models have correct context size configurations
- The personal agent uses the optimal context window for each model
- Context size discrepancies are identified and can be corrected

## Usage

```bash
# Run the verification script
python scripts/verify_qwen_context_sizes.py

# Make the script executable (optional)
chmod +x scripts/verify_qwen_context_sizes.py
./scripts/verify_qwen_context_sizes.py
```

## What the Script Does

1. **Lists Available Models**: Uses `ollama list` to get all locally available models
2. **Identifies Qwen Models**: Filters models from the configuration that contain "qwen"
3. **Matches Models**: Handles case differences (e.g., `qwen3:1.7b` vs `qwen3:1.7B`)
4. **Queries Context Sizes**: Uses `ollama show` to get actual context lengths
5. **Compares Values**: Checks configured vs actual context sizes
6. **Reports Results**: Shows matches, mismatches, and unavailable models

## Output Example

```
🔍 Verifying Qwen model context sizes...
============================================================
📋 Checking available models...
✅ Found 20 available models
📊 Found 12 Qwen models in configuration

🔍 Checking qwen3:1.7b...
📝 Found as: qwen3:1.7B
✅ Context size matches: 40,960 tokens

🔍 Checking qwen3:8b...
✅ Context size matches: 40,960 tokens

============================================================
📊 SUMMARY
============================================================
✅ Verified models (4):
   qwen3:1.7b: 40,960 tokens
   qwen3:8b: 40,960 tokens
   qwen3:14b: 40,960 tokens
   hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M: 262,144 tokens

🎉 All available Qwen models have correct context sizes!
```

## When to Use

- After adding new Qwen models to the configuration
- When updating Ollama or model versions
- To verify context sizes are optimal for performance
- As part of system health checks

## Troubleshooting

### Model Not Found
If a model shows as "not available locally", you can:
- Install it with `ollama pull <model_name>`
- Remove it from the configuration if no longer needed

### Context Size Mismatch
If the script reports mismatches, it will suggest updates:
```
🔧 Suggested updates for model_contexts.py:
    "qwen3:8b": 40960,  # Updated from 32768
```

Apply these updates to `src/personal_agent/config/model_contexts.py`.

### Parsing Errors
If the script can't parse `ollama show` output:
- Check that Ollama is running and accessible
- Verify the model exists with `ollama list`
- Check the debug output for parsing issues

## Technical Details

The script parses the structured output from `ollama show` which looks like:
```
  Model
    architecture        qwen3     
    parameters          8.2B      
    context length      40960     
    embedding length    4096      
```

It extracts the "context length" value from the "Model" section and compares it with the configured value in the Python dictionary.

## Dependencies

- Python 3.6+
- Ollama CLI tool
- Access to the personal_agent configuration modules

## Files Modified

- `src/personal_agent/config/model_contexts.py` - Contains the model context size database
- `scripts/verify_qwen_context_sizes.py` - The verification script itself