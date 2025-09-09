# Streaming Response Analysis: Key Findings

## Overview

This document summarizes the critical findings from analyzing streaming responses in Agno agents, specifically focusing on where the final agent response and tool call results are located within the streaming chunk structure.

## The Problem

When using `agent.run(stream=True)`, developers often struggle to identify:
1. Where the actual final agent response is located
2. How to extract tool call results from streaming chunks
3. The difference between internal agent reasoning and user-facing content

## Key Discoveries

### 1. Final Agent Response Location

**❌ Common Misconception:** The final response is in a separate field like `response` or `final_response`

**✅ Reality:** The final response is embedded within the `content` field of the final chunk, specifically the content that appears **after** the `</think>` tags.

```python
# Extract actual final response
if '</think>' in content_str:
    parts = content_str.split('</think>')
    if len(parts) > 1:
        actual_response = parts[-1].strip()
```

### 2. Chunk Structure Analysis

#### Final Chunk Identification
- **Event Type:** `RunCompleted`
- **Location:** Last chunk in the streaming sequence
- **Key Attributes:**
  - `content`: Contains both thinking process AND final response
  - `images`: Array of `ImageArtifact` objects (if applicable)
  - `event`: `RunCompleted`
  - `status`: May be "unknown" rather than explicitly "completed"

#### Content Structure
```
<think>
[Internal agent reasoning process]
[Multiple thinking blocks possible]
</think>

[ACTUAL FINAL RESPONSE - This is what users should see]
```

### 3. Tool Call Flow Analysis

#### Tool Execution Pattern
1. **Tool Call Initiation Chunk**
   - Contains tool arguments and setup
   - `result: None` (not yet executed)
   - `tool_name`: Function name (e.g., "create_image")
   - `tool_args`: Parameters passed to the tool

2. **Tool Execution Result Chunk**
   - Contains actual results from tool execution
   - `result`: The tool's output/response
   - `metrics`: Execution timing and performance data
   - `tool_call_error`: Success/failure status

#### Example Tool Call Structure
```python
# Tool Call Initiation (Chunk #295)
{
    "tool_name": "create_image",
    "tool_args": {"prompt": "A cyberpunk cityscape..."},
    "result": None,
    "status": "unknown"
}

# Tool Execution Result (Chunk #296)
{
    "tool_name": "create_image", 
    "result": "Image has been generated at URL...",
    "metrics": {"time": 22.7, "tokens": 0},
    "tool_call_error": False
}
```

### 4. Message Flow Pattern

```
User Request 
    ↓
Tool Call Initiation (Chunk N)
    ↓
Tool Execution (22+ seconds)
    ↓
Tool Result (Chunk N+1)
    ↓
[Multiple tool calls possible]
    ↓
Final Agent Response (Last Chunk)
```

## Implementation Guide

### Extracting the Final Response

```python
def extract_final_response(chunks_data):
    # Find the final chunk
    final_chunk = None
    for chunk_info in reversed(chunks_data):
        if chunk_info.get("event") == "RunCompleted":
            final_chunk = chunk_info["chunk_object"]
            break
    
    if not final_chunk or not hasattr(final_chunk, 'content'):
        return None
    
    # Extract content after </think> tags
    content_str = str(final_chunk.content)
    if '</think>' in content_str:
        parts = content_str.split('</think>')
        if len(parts) > 1:
            return parts[-1].strip()
    
    return content_str
```

### Extracting Tool Call Results

```python
def extract_tool_results(chunks_data):
    tool_results = []
    
    for chunk_info in chunks_data:
        chunk = chunk_info["chunk_object"]
        
        # Check for tool results
        if hasattr(chunk, 'tool') and chunk.tool:
            if hasattr(chunk.tool, 'result') and chunk.tool.result:
                tool_results.append({
                    "name": chunk.tool.tool_name,
                    "result": chunk.tool.result,
                    "execution_time": getattr(chunk.tool.metrics, 'time', 0),
                    "error": chunk.tool.tool_call_error
                })
    
    return tool_results
```

## Real-World Example

### Input
```python
prompt = "Create an image of a cyberpunk cityscape"
run_stream = agent.run(prompt, stream=True, stream_intermediate_steps=True)
```

### Streaming Chunks Analysis
- **Total Chunks:** 649
- **Tool Call Chunks:** #295 (initiation), #296 (result)
- **Final Response Chunk:** #648

### Raw Content vs. Final Response

**Raw Content (1,945 characters):**
```
<think>
Okay, the user wants an image of a cyberpunk cityscape. Let me think about what that entails...
[extensive reasoning process]
</think>

![](https://oaidalleapiprodscus.blob.core.windows.net/private/org-we2jMOH9AUnPw2slIrKSKB73/user-jdNMbB7SDHRhJx7mweVp1Nt9/img-P8VY6HbUhKZ7Q0N40LSSIC4U.png?st=2025-08-28T22%3A53%3A18Z&se=2025-08-29T00%3A53%3A18Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=6e4237ed-4a31-4e1d-a677-4df21834ece0&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-08-28T23%3A53%3A18Z&ske=2025-08-29T23%3A53%3A18Z&sks=b&skv=2024-08-04&sig=653YZQBrfkGOeCkzZGju5%2BZE2kzD47izf7Rw2NTUa2c%3D)
```

**Actual Final Response (479 characters):**
```
![](https://oaidalleapiprodscus.blob.core.windows.net/private/org-we2jMOH9AUnPw2slIrKSKB73/user-jdNMbB7SDHRhJx7mweVp1Nt9/img-P8VY6HbUhKZ7Q0N40LSSIC4U.png?st=2025-08-28T22%3A53%3A18Z&se=2025-08-29T00%3A53%3A18Z&sp=r&sv=2024-08-04&sr=b&rscd=inline&rsct=image/png&skoid=6e4237ed-4a31-4e1d-a677-4df21834ece0&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-08-28T23%3A53%3A18Z&ske=2025-08-29T23%3A53%3A18Z&sks=b&skv=2024-08-04&sig=653YZQBrfkGOeCkzZGju5%2BZE2kzD47izf7Rw2NTUa2c%3D)
```

## Best Practices

### 1. Response Processing
- Always extract content after `</think>` tags for user-facing responses
- Preserve raw content for debugging and analysis
- Handle cases where no `</think>` tags exist

### 2. Tool Call Handling
- Track tool calls across multiple chunks
- Monitor execution timing via `metrics`
- Check `tool_call_error` for failure detection
- Store both arguments and results for complete context

### 3. Chunk Analysis
- Process chunks sequentially to maintain conversation flow
- Look for `RunCompleted` event to identify final chunk
- Handle edge cases where status might be "unknown"

### 4. Error Handling
```python
def safe_extract_response(chunks_data):
    try:
        final_response = extract_final_response(chunks_data)
        if not final_response:
            # Fallback to last chunk with content
            for chunk_info in reversed(chunks_data):
                if chunk_info.get("has_content"):
                    return chunk_info["chunk_object"].content
        return final_response
    except Exception as e:
        print(f"Error extracting response: {e}")
        return None
```

## Common Pitfalls

### ❌ Don't Do This
```python
# Wrong: Looking for response in separate field
final_response = chunk.response  # This doesn't exist

# Wrong: Using raw content directly
user_response = chunk.content  # Includes thinking process

# Wrong: Assuming tool results are in separate chunks
tool_result = chunk.tool_result  # Results are in tool.result
```

### ✅ Do This Instead
```python
# Correct: Extract content after </think>
content = str(chunk.content)
if '</think>' in content:
    final_response = content.split('</think>')[-1].strip()

# Correct: Get tool results from tool object
if hasattr(chunk, 'tool') and chunk.tool and chunk.tool.result:
    tool_result = chunk.tool.result
```

## Conclusion

Understanding the streaming response structure is crucial for building robust applications with Agno agents. The key insights are:

1. **Final responses are embedded within content fields, not separate**
2. **Tool calls span multiple chunks with detailed execution information**
3. **User-facing content must be extracted from agent reasoning**
4. **Proper chunk analysis enables complete conversation reconstruction**

These findings enable developers to properly extract and display agent responses while maintaining access to detailed execution information for debugging and analysis.

## Related Files

- `comprehensive_streaming_analyzer.py` - Complete analysis tool
- `examples/team_with_intermediate_steps.py` - Basic streaming example
- `streaming_response_analyzer.py` - Original analysis script

---

*Generated from analysis of Agno agent streaming responses - January 2025*
