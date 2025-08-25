# RunResponse Parsing Guide

## Overview

Based on analysis of the agno library, here's how to properly parse `RunResponse` and `TeamRunResponse` objects to extract the final response content and tool calls.

## RunResponse Structure

```python
@dataclass
class RunResponse:
    content: Optional[Any] = None                    # Main response content
    content_type: str = "str"                       # Type of content
    thinking: Optional[str] = None                  # AI thinking process
    reasoning_content: Optional[str] = None         # Reasoning steps
    messages: Optional[List[Message]] = None        # All messages
    tools: Optional[List[ToolExecution]] = None     # Tool executions
    formatted_tool_calls: Optional[List[str]] = None # Human-readable tool calls
    citations: Optional[Citations] = None           # References/citations
    status: RunStatus = RunStatus.running           # Execution status
    # ... other fields
```

## Key Fields for Parsing

### 1. Final Response Content
- **`content`**: The main response content (can be string, BaseModel, or dict)
- **`content_type`**: Indicates the type ("str", model class name, etc.)

### 2. Tool Calls
- **`tools`**: List of `ToolExecution` objects with detailed info
- **`formatted_tool_calls`**: Human-readable string representations

### 3. Status
- **`status`**: `RunStatus.completed`, `RunStatus.running`, `RunStatus.cancelled`, etc.

## Parsing Code Examples

### Basic Response Parser

```python
def parse_run_response(response):
    """Parse a RunResponse or TeamRunResponse object"""
    result = {
        'final_content': None,
        'content_type': 'str',
        'tool_calls': [],
        'formatted_tool_calls': [],
        'status': 'unknown',
        'thinking': None,
        'citations': None
    }
    
    # Extract final content
    if hasattr(response, 'content') and response.content is not None:
        result['final_content'] = response.content
        result['content_type'] = getattr(response, 'content_type', 'str')
    
    # Extract tool calls
    if hasattr(response, 'tools') and response.tools:
        result['tool_calls'] = response.tools
    
    # Extract formatted tool calls
    if hasattr(response, 'formatted_tool_calls') and response.formatted_tool_calls:
        result['formatted_tool_calls'] = response.formatted_tool_calls
    
    # Extract status
    if hasattr(response, 'status'):
        result['status'] = response.status.value if hasattr(response.status, 'value') else str(response.status)
    
    # Extract thinking
    if hasattr(response, 'thinking') and response.thinking:
        result['thinking'] = response.thinking
    
    # Extract citations
    if hasattr(response, 'citations') and response.citations:
        result['citations'] = response.citations
    
    return result
```

### Content Type Handler

```python
def get_final_content_as_string(response):
    """Extract final content as a string regardless of type"""
    if not hasattr(response, 'content') or response.content is None:
        return ""
    
    content = response.content
    content_type = getattr(response, 'content_type', 'str')
    
    # Handle different content types
    if isinstance(content, str):
        return content
    elif hasattr(content, 'model_dump_json'):  # Pydantic BaseModel
        return content.model_dump_json(exclude_none=True, indent=2)
    elif isinstance(content, dict):
        import json
        return json.dumps(content, indent=2)
    else:
        return str(content)
```

### Tool Calls Parser

```python
def parse_tool_calls(response):
    """Extract and parse tool calls from response"""
    tool_calls = []
    
    if not hasattr(response, 'tools') or not response.tools:
        return tool_calls
    
    for tool in response.tools:
        tool_info = {
            'name': getattr(tool, 'tool_name', 'unknown'),
            'args': getattr(tool, 'tool_args', {}),
            'result': getattr(tool, 'result', None),
            'status': getattr(tool, 'status', 'unknown'),
            'call_id': getattr(tool, 'tool_call_id', None),
            'error': getattr(tool, 'error', None)
        }
        tool_calls.append(tool_info)
    
    return tool_calls
```

### Complete Response Processor

```python
class ResponseProcessor:
    """Complete response processing class"""
    
    @staticmethod
    def process_response(response):
        """Process any type of response (RunResponse or TeamRunResponse)"""
        result = {
            'type': 'unknown',
            'final_content': '',
            'content_type': 'str',
            'tool_calls': [],
            'formatted_tool_calls': [],
            'member_responses': [],
            'status': 'unknown',
            'metadata': {}
        }
        
        # Determine response type
        if hasattr(response, 'team_id'):
            result['type'] = 'team_response'
            result = ResponseProcessor._process_team_response(response, result)
        else:
            result['type'] = 'agent_response'
            result = ResponseProcessor._process_agent_response(response, result)
        
        return result
    
    @staticmethod
    def _process_agent_response(response, result):
        """Process individual agent response"""
        # Final content
        result['final_content'] = ResponseProcessor._extract_content(response)
        result['content_type'] = getattr(response, 'content_type', 'str')
        
        # Tool calls
        result['tool_calls'] = ResponseProcessor._extract_tool_calls(response)
        result['formatted_tool_calls'] = getattr(response, 'formatted_tool_calls', [])
        
        # Status
        result['status'] = ResponseProcessor._extract_status(response)
        
        # Metadata
        result['metadata'] = {
            'thinking': getattr(response, 'thinking', None),
            'reasoning_content': getattr(response, 'reasoning_content', None),
            'citations': getattr(response, 'citations', None),
            'model': getattr(response, 'model', None),
            'agent_id': getattr(response, 'agent_id', None),
            'run_id': getattr(response, 'run_id', None)
        }
        
        return result
    
    @staticmethod
    def _process_team_response(response, result):
        """Process team response with member responses"""
        # Process as agent response first
        result = ResponseProcessor._process_agent_response(response, result)
        
        # Add team-specific data
        result['metadata']['team_id'] = getattr(response, 'team_id', None)
        result['metadata']['team_name'] = getattr(response, 'team_name', None)
        
        # Process member responses
        if hasattr(response, 'member_responses') and response.member_responses:
            for member_response in response.member_responses:
                member_result = ResponseProcessor._process_agent_response(member_response, {
                    'final_content': '',
                    'content_type': 'str',
                    'tool_calls': [],
                    'formatted_tool_calls': [],
                    'status': 'unknown',
                    'metadata': {}
                })
                result['member_responses'].append(member_result)
        
        return result
    
    @staticmethod
    def _extract_content(response):
        """Extract content as string"""
        if not hasattr(response, 'content') or response.content is None:
            return ""
        
        content = response.content
        
        if isinstance(content, str):
            return content
        elif hasattr(content, 'model_dump_json'):
            return content.model_dump_json(exclude_none=True, indent=2)
        elif isinstance(content, dict):
            import json
            return json.dumps(content, indent=2)
        else:
            return str(content)
    
    @staticmethod
    def _extract_tool_calls(response):
        """Extract tool calls information"""
        if not hasattr(response, 'tools') or not response.tools:
            return []
        
        tool_calls = []
        for tool in response.tools:
            tool_info = {
                'name': getattr(tool, 'tool_name', 'unknown'),
                'args': getattr(tool, 'tool_args', {}),
                'result': getattr(tool, 'result', None),
                'status': getattr(tool, 'status', 'unknown'),
                'call_id': getattr(tool, 'tool_call_id', None),
                'error': getattr(tool, 'error', None),
                'execution_time': getattr(tool, 'execution_time', None)
            }
            tool_calls.append(tool_info)
        
        return tool_calls
    
    @staticmethod
    def _extract_status(response):
        """Extract response status"""
        if hasattr(response, 'status'):
            status = response.status
            return status.value if hasattr(status, 'value') else str(status)
        return 'unknown'
```

## Usage Examples

### Simple Usage

```python
# For a basic response
response = agent.run("What's the weather?")
parsed = parse_run_response(response)

print("Final Response:", parsed['final_content'])
print("Tool Calls:", len(parsed['tool_calls']))
print("Status:", parsed['status'])
```

### Advanced Usage

```python
# For team responses with full processing
team_response = team.run("Analyze this data and create a report")
processed = ResponseProcessor.process_response(team_response)

print("Response Type:", processed['type'])
print("Final Content:", processed['final_content'])
print("Number of Tool Calls:", len(processed['tool_calls']))
print("Number of Member Responses:", len(processed['member_responses']))

# Access tool calls
for i, tool_call in enumerate(processed['tool_calls']):
    print(f"Tool {i+1}: {tool_call['name']}")
    print(f"  Result: {tool_call['result']}")
    print(f"  Status: {tool_call['status']}")

# Access member responses
for i, member in enumerate(processed['member_responses']):
    print(f"Member {i+1} Response: {member['final_content'][:100]}...")
```

### Streaming Response Handler

```python
def handle_streaming_response(response_stream):
    """Handle streaming responses and collect final result"""
    final_content = ""
    tool_calls = []
    status = "running"
    
    for event in response_stream:
        # Handle content events
        if hasattr(event, 'event') and event.event == 'RunResponseContent':
            if hasattr(event, 'content') and event.content:
                final_content += str(event.content)
        
        # Handle tool call events
        elif hasattr(event, 'event') and event.event == 'ToolCallCompleted':
            if hasattr(event, 'tool') and event.tool:
                tool_calls.append({
                    'name': getattr(event.tool, 'tool_name', 'unknown'),
                    'result': getattr(event.tool, 'result', None),
                    'status': getattr(event.tool, 'status', 'unknown')
                })
        
        # Handle completion
        elif hasattr(event, 'event') and event.event == 'RunCompleted':
            status = "completed"
            break
    
    return {
        'final_content': final_content,
        'tool_calls': tool_calls,
        'status': status
    }
```

## Key Points

1. **Always check for attribute existence** using `hasattr()` before accessing
2. **Handle different content types** (string, BaseModel, dict)
3. **Tool calls contain detailed execution info** including args, results, and status
4. **Team responses have member_responses** with individual agent results
5. **Status indicates completion state** (running, completed, cancelled, etc.)
6. **Streaming responses require event-based parsing**

## Common Patterns

```python
# Check if response is complete
if hasattr(response, 'status') and response.status == RunStatus.completed:
    # Process final response
    pass

# Get human-readable tool calls
if hasattr(response, 'formatted_tool_calls') and response.formatted_tool_calls:
    for call in response.formatted_tool_calls:
        print(f"Tool Call: {call}")

# Handle structured output
if hasattr(response, 'content_type') and response.content_type != 'str':
    # Content is structured (BaseModel or dict)
    structured_content = response.content
```

This guide provides everything needed to properly parse RunResponse objects and extract the final response content and tool calls from the agno library responses.
