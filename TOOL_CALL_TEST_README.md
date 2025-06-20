# Tool Call Detection Test

This test suite verifies that the `AgnoPersonalAgent` properly detects and reports tool calls through the new `get_last_tool_calls()` method.

## Files Created

- `test_tool_call_detection.py` - Main test script
- `run_tool_test.sh` - Shell script to run the test
- `TOOL_CALL_TEST_README.md` - This documentation

## What the Test Does

The test script performs the following checks:

### 1. Tool Call Detection Tests
Tests various queries that should trigger different tools:

- **Memory Storage Test**: "Remember that I like pizza and my favorite color is blue"
  - Expected: `store_user_memory` tool call
- **Memory Retrieval Test**: "What do you remember about me?"
  - Expected: `get_recent_memories` tool call
- **Finance Tool Test**: "What's the current price of AAPL stock?"
  - Expected: `get_current_stock_price` tool call
- **Web Search Test**: "Search for the latest news about artificial intelligence"
  - Expected: `duckduckgo_search` tool call
- **Python Calculation Test**: "Calculate 15 * 23 + 47"
  - Expected: `python_run` tool call
- **Simple Chat Test**: "Hello, how are you today?"
  - Expected: No tool calls

### 2. Memory Functionality Tests
Specific tests for memory operations:
- Store a memory about job and preferences
- Retrieve stored memories
- Verify tool calls are detected for both operations

### 3. Debug Information
The test provides detailed debug information including:
- Response structure analysis
- Tool call details (ID, type, function name, arguments)
- Agent configuration information
- Error handling and reporting

## How to Run

### Option 1: Using the shell script
```bash
./run_tool_test.sh
```

### Option 2: Direct Python execution
```bash
python3 test_tool_call_detection.py
```

## Expected Output

The test will show:
1. Agent initialization status
2. Individual test results with tool call detection
3. Pass/fail status for each test
4. Summary of all test results
5. Debug information about the agent's response structure

## What Success Looks Like

A successful test run should show:
- ✅ Agent initializes properly
- ✅ Tool calls are detected for queries that should use tools
- ✅ No tool calls detected for simple chat queries
- ✅ Detailed tool information is available (function names, arguments)
- ✅ Debug information shows proper response structure

## Troubleshooting

If tests fail:

1. **Agent initialization fails**: Check Ollama is running and accessible
2. **No tool calls detected**: Check the `get_last_tool_calls()` method implementation
3. **Wrong tool calls**: Verify agent instructions and tool availability
4. **Import errors**: Ensure you're running from the project root directory

## Integration with Streamlit

This test verifies the same functionality that the Streamlit frontend uses to display tool call information in the debug panels. If this test passes, the Streamlit frontend should properly show:

- Tool call counts in performance metrics
- Tool call details in debug expanders
- Tool indicators in request history
- Comprehensive debugging information

## Files Modified for Tool Call Detection

The following files were modified to enable tool call detection:

1. `src/personal_agent/core/agno_agent.py`:
   - Added `get_last_tool_calls()` method
   - Modified `run()` method to store last response
   - Enhanced tool call extraction logic

2. `tools/paga_streamlit_agno.py`:
   - Updated to use `agent.get_last_tool_calls()`
   - Enhanced debug display for new tool call format
   - Added comprehensive tool call information display

This test ensures these modifications work correctly and tool calls are properly detected and reported.
