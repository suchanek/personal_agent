# Agno Agent Streaming vs Non-Streaming Response Analysis

This document provides a comprehensive analysis of the differences between streaming and non-streaming responses from Agno agents, including how to properly collect and analyze chunks for use in Streamlit applications.

## Overview

Agno agents provide two distinct modes for receiving responses:
1. **Streaming Mode**: Returns an iterator of `RunResponseEvent` chunks for real-time updates
2. **Non-Streaming Mode**: Returns a single complete `RunResponse` object when processing is finished

## Key Differences

### Streaming Mode (`stream=True`)

**Return Type**: Iterator of `RunResponseEvent` objects

**Characteristics**:
- Provides real-time updates as the agent processes the request
- Returns multiple chunks that must be collected and analyzed
- Tool calls appear in individual chunks with `tool` attribute (single tool)
- Image URLs are embedded in content as markdown in final chunks
- Final response is in the last chunk or a chunk with `RunStatus.completed`

**Chunk Structure**:
- Each chunk is a `RunResponseEvent` object
- Chunks may have different attributes:
  - `content`: Response content (appears in most chunks)
  - `tool`: Single tool execution (appears in specific chunks)
  - `tools`: List of tool executions (rarely appears in streaming)
  - `status`: Run status (unknown, running, completed)
  - `event`: Event type (run_response_content, tool_call_started, etc.)

**Collection Process**:
```python
# Get streaming iterator
run_stream = agent.run(prompt, stream=True, stream_intermediate_steps=True)

# Collect ALL chunks by iterating through the iterator
chunks = list(run_stream)  # or use a for loop to process each chunk

# Analyze chunks to extract final response and tool calls
```

### Non-Streaming Mode (`stream=False`)

**Return Type**: Single `RunResponse` object

**Characteristics**:
- Blocks until processing is complete
- Returns one complete response object
- Tool calls appear in `RunResponse.tools` list
- Image URLs are in the final content
- No need to collect multiple chunks

**Response Structure**:
- Single `RunResponse` object with complete information
- `content`: Final response content
- `tools`: List of all tool executions
- `status`: Final run status
- `images`: List of image artifacts

**Collection Process**:
```python
# Get complete response (blocks until done)
response = agent.run(prompt, stream=False)

# Directly access response properties
final_content = response.content
tool_calls = response.tools
```

## How to Collect Streaming Chunks

### Method 1: Simple Collection
```python
def collect_streaming_response(run_stream: Iterator[RunResponseEvent]) -> List[RunResponseEvent]:
    """Collect all chunks from streaming iterator."""
    return list(run_stream)
```

### Method 2: Detailed Collection with Analysis
```python
def collect_and_analyze_chunks(run_stream: Iterator[RunResponseEvent]) -> List[Dict[str, Any]]:
    """Collect all chunks and examine each one for detailed information."""
    chunks_data = []
    
    for i, chunk in enumerate(run_stream):
        chunk_info = {
            "index": i,
            "chunk_object": chunk,
            "has_content": hasattr(chunk, 'content') and chunk.content is not None,
            "content_length": len(str(chunk.content)) if hasattr(chunk, 'content') and chunk.content else 0,
            "has_tool": hasattr(chunk, 'tool') and chunk.tool is not None,
            "has_tools": hasattr(chunk, 'tools') and chunk.tools is not None,
            "status": str(chunk.status) if hasattr(chunk, 'status') else None
        }
        chunks_data.append(chunk_info)
    
    return chunks_data
```

## Tool Call Information in Streaming Chunks

### Key Findings:
1. **Tool calls primarily appear in the `tool` attribute** (single tool) rather than `tools` attribute (list)
2. **Tool calls appear in specific chunks** (e.g., chunks #259 and #260 in testing)
3. **Tool call information includes**:
   - `tool_name`: Name of the tool executed
   - `arguments`: Arguments passed to the tool
   - `status`: Status of the tool execution

### Extraction Process:
```python
def extract_tool_calls_from_chunks(chunks: List[RunResponseEvent]) -> List[Dict[str, Any]]:
    """Extract all tool calls from streaming chunks."""
    tool_calls = []
    
    for chunk in chunks:
        # Check for tool in 'tool' attribute (single tool)
        if hasattr(chunk, 'tool') and chunk.tool:
            tool_info = {
                "name": getattr(chunk.tool, 'tool_name', 'Unknown'),
                "arguments": getattr(chunk.tool, 'arguments', {}),
                "status": getattr(chunk.tool, 'status', 'unknown')
            }
            tool_calls.append(tool_info)
        
        # Check for tools in 'tools' attribute (list of tools)
        if hasattr(chunk, 'tools') and chunk.tools:
            for tool in chunk.tools:
                tool_info = {
                    "name": getattr(tool, 'tool_name', 'Unknown'),
                    "arguments": getattr(tool, 'arguments', {}),
                    "status": getattr(tool, 'status', 'unknown')
                }
                tool_calls.append(tool_info)
    
    # Remove duplicates while preserving order
    unique_tool_calls = []
    for tool_call in tool_calls:
        if tool_call not in unique_tool_calls:
            unique_tool_calls.append(tool_call)
    
    return unique_tool_calls
```

## Image URL Extraction

### From Streaming Chunks:
Image URLs are embedded in the content as markdown: `![alt text](URL)`

```python
def extract_image_urls_from_chunks(chunks: List[RunResponseEvent]) -> List[Dict[str, str]]:
    """Extract image URLs from streaming chunks."""
    image_urls = []
    
    for chunk in chunks:
        if hasattr(chunk, 'content') and chunk.content:
            # Find markdown image patterns ![alt](url)
            import re
            image_matches = re.findall(r'!\[([^\]]*)\]\((https?://[^\)]+)\)', str(chunk.content))
            for alt_text, url in image_matches:
                if url not in [img["url"] for img in image_urls]:
                    image_urls.append({
                        "alt_text": alt_text,
                        "url": url
                    })
    
    return image_urls
```

### From Non-Streaming Response:
Image URLs can be accessed directly from the response:

```python
def extract_image_urls_from_response(response: RunResponse) -> List[Dict[str, str]]:
    """Extract image URLs from non-streaming response."""
    image_urls = []
    
    # Check response.content for markdown image URLs
    if hasattr(response, 'content') and response.content:
        import re
        image_matches = re.findall(r'!\[([^\]]*)\]\((https?://[^\)]+)\)', str(response.content))
        for alt_text, url in image_matches:
            image_urls.append({
                "alt_text": alt_text,
                "url": url
            })
    
    # Check response.images for ImageArtifact objects
    if hasattr(response, 'images') and response.images:
        for image in response.images:
            if hasattr(image, 'url') and image.url:
                image_urls.append({
                    "alt_text": getattr(image, 'description', 'Generated Image'),
                    "url": image.url
                })
    
    return image_urls
```

## Best Practices for Streamlit Applications

### 1. Unified Interface for Both Modes:
```python
def get_complete_response_from_agent(
    agent: Agent,
    message: str,
    stream: bool = False,
    **kwargs
) -> Union[RunResponse, Dict[str, Any]]:
    """Get complete response from an Agno agent, handling both streaming and non-streaming modes."""
    if stream:
        # Streaming mode - collect and analyze chunks
        run_stream = agent.run(message, stream=True, **kwargs)
        chunks = collect_streaming_response(run_stream)
        analysis = extract_final_response_and_tools(chunks)
        return format_for_streamlit_display(analysis)
    else:
        # Non-streaming mode - return complete response
        return agent.run(message, stream=False, **kwargs)
```

### 2. Proper Chunk Collection:
Always collect ALL chunks from the streaming iterator to ensure complete information:

```python
# ✅ Correct way to collect all chunks
run_stream = agent.run(prompt, stream=True)
chunks = list(run_stream)  # Collects ALL chunks

# ❌ Incorrect way - only processes first chunk
run_stream = agent.run(prompt, stream=True)
first_chunk = next(run_stream)  # Only gets first chunk, misses the rest
```

### 3. Intelligent Analysis:
Analyze all chunks to extract complete information:

```python
def intelligent_response_analysis(chunks: List[RunResponseEvent]) -> Dict[str, Any]:
    """Intelligently analyze collected chunks to extract final response and tool calls."""
    analysis = {
        "final_content": "",
        "tool_calls": [],
        "image_urls": [],
        "status": "unknown"
    }
    
    # Process ALL chunks to build complete picture
    for chunk in chunks:
        # Extract tool calls from both 'tool' and 'tools' attributes
        if hasattr(chunk, 'tool') and chunk.tool:
            # Single tool extraction
            pass
        if hasattr(chunk, 'tools') and chunk.tools:
            # List of tools extraction
            pass
            
        # Extract image URLs from content
        if hasattr(chunk, 'content') and chunk.content:
            # Image URL extraction from markdown
            pass
        
        # Identify final chunk
        if hasattr(chunk, 'status') and str(chunk.status) == 'RunStatus.completed':
            # This is the final chunk
            pass
    
    return analysis
```

## Summary

The key to successfully working with Agno agent responses is understanding that:

1. **Streaming mode** provides real-time updates but requires collecting ALL chunks
2. **Tool calls** primarily appear in the `tool` attribute of specific chunks
3. **Image URLs** are embedded in content as markdown
4. **Non-streaming mode** provides complete information in a single object
5. **Proper collection** of streaming chunks is essential for complete information

By following these patterns and using the provided utilities, Streamlit applications can effectively handle both streaming and non-streaming responses from Agno agents.