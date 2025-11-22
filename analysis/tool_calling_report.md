# Ollama Model Tool Calling Test Report
**Test Date:** 2025-11-21 21:09:28
**Models Tested:** 14

## Summary
| Model | Status | Tool Calls Work | Parseable | Double-Call | Avg Time (s) | Input→Output (Total) |
|-------|--------|----------------|-----------|-------------|--------------|----------------------|
| llama32-tools:latest | ❌ BROKEN | ❌ | ❌ | ✅ | 1.052 | 350→28 (757) |
| llama3.1:8b | ✅ WORKING | ✅ | ✅ | ✅ | 1.787 | 337→42 (758) |
| llama3.2:3b | ⚠️ PARTIAL | ❌ | ✅ | ✅ | 0.829 | 283→29 (625) |
| hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:latest | ⚠️ PARTIAL | ❌ | ✅ | ✅ | 0.515 | 239→28 (534) |
| qwen3:latest | ✅ WORKING | ✅ | ✅ | ⚠️ | 9.036 | 614→372 (1974) |
| qwen3:8b | ✅ WORKING | ✅ | ✅ | ✅ | 7.252 | 475→298 (1546) |
| qwen3:4b | ✅ WORKING | ✅ | ✅ | ✅ | 3.811 | 475→222 (1394) |
| qwen3:1.7B | ✅ WORKING | ✅ | ✅ | ⚠️ | 2.887 | 614→278 (1785) |
| hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K | ✅ WORKING | ✅ | ✅ | ✅ | 1.008 | 471→35 (1013) |
| hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M | ⚠️ PARTIAL | ❌ | ✅ | ✅ | 0.677 | 350→22 (746) |
| hf.co/unsloth/Qwen3-4B-Thinking-2507-GGUF:Q6_K | 💥 ERROR | ✅ | ✅ | ✅ | 0.051 | 0→0 (0) |
| hf.co/qwen/qwen2.5-coder-7b-instruct-gguf:latest | ⚠️ PARTIAL | ❌ | ✅ | ✅ | 0.989 | 225→27 (505) |
| qwen2.5-coder:3b | ⚠️ PARTIAL | ❌ | ✅ | ✅ | 0.566 | 235→17 (505) |
| myaniu/qwen2.5-1m:latest | ✅ WORKING | ✅ | ✅ | ✅ | 1.439 | 476→39 (1031) |

## Detailed Results

### ✅ Working Models

#### llama3.1:8b
- **Status:** WORKING
- **Notes:** Tool calling works correctly
- **Successful Queries:** 2/2
- **Average Response Time:** 1.787s
- **Total Tokens:** 758

#### qwen3:latest
- **Status:** WORKING
- **Notes:** Tool calling works correctly (but has double-call issue)
- **Successful Queries:** 2/2
- **Average Response Time:** 9.036s
- **Total Tokens:** 1974

#### qwen3:8b
- **Status:** WORKING
- **Notes:** Tool calling works correctly
- **Successful Queries:** 2/2
- **Average Response Time:** 7.252s
- **Total Tokens:** 1546

#### qwen3:4b
- **Status:** WORKING
- **Notes:** Tool calling works correctly
- **Successful Queries:** 2/2
- **Average Response Time:** 3.811s
- **Total Tokens:** 1394

#### qwen3:1.7B
- **Status:** WORKING
- **Notes:** Tool calling works correctly (but has double-call issue)
- **Successful Queries:** 2/2
- **Average Response Time:** 2.887s
- **Total Tokens:** 1785

#### hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K
- **Status:** WORKING
- **Notes:** Tool calling works correctly
- **Successful Queries:** 2/2
- **Average Response Time:** 1.008s
- **Total Tokens:** 1013

#### myaniu/qwen2.5-1m:latest
- **Status:** WORKING
- **Notes:** Tool calling works correctly
- **Successful Queries:** 2/2
- **Average Response Time:** 1.439s
- **Total Tokens:** 1031

### ❌ Broken Models (Tool Calls Not Parsed)

#### llama32-tools:latest
- **Status:** BROKEN
- **Notes:** Tool calls generated but not parsed correctly
- **Issue:** Tool calls are generated but not parsed into structured format

### ⚠️ Partially Working Models

#### llama3.2:3b
- **Status:** PARTIAL
- **Notes:** Some queries work, others don't

#### hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:latest
- **Status:** PARTIAL
- **Notes:** Some queries work, others don't

#### hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M
- **Status:** PARTIAL
- **Notes:** Some queries work, others don't

#### hf.co/qwen/qwen2.5-coder-7b-instruct-gguf:latest
- **Status:** PARTIAL
- **Notes:** Some queries work, others don't

#### qwen2.5-coder:3b
- **Status:** PARTIAL
- **Notes:** Some queries work, others don't

### 💥 Error Models (Failed to Test)

#### hf.co/unsloth/Qwen3-4B-Thinking-2507-GGUF:Q6_K
- **Error:** Model failed to respond to queries

## Recommendations

Based on the test results:

**✅ Recommended models for tool calling:**
- `hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K` - 1.008s avg
- `myaniu/qwen2.5-1m:latest` - 1.439s avg
- `llama3.1:8b` - 1.787s avg
- `qwen3:1.7B` - 2.887s avg (⚠️ has double-call issue)
- `qwen3:4b` - 3.811s avg
- `qwen3:8b` - 7.252s avg
- `qwen3:latest` - 9.036s avg (⚠️ has double-call issue)

**❌ Avoid these models for tool calling:**
- `llama32-tools:latest` - Tool calls generated but not parsed correctly

## Technical Notes

### Double-Call Issue
Some models call tools multiple times for the same query. This can be mitigated with specific instructions or post-processing.

### Unparsed Tool Calls
Models marked as 'BROKEN' generate tool calls in text format (e.g., `<tool_call>...`) but the Ollama client does not parse them into structured tool_calls. This is likely an issue with the model's template or Ollama client compatibility.
