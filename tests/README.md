# Tests Directory

This directory contains all test scripts for the Personal Agent project. All test files have been organized here with proper import paths.

## Running Tests

### Run All Tests
```bash
# From project root
python tests/run_all_tests.py

# Or make it executable and run directly
./tests/run_all_tests.py
```

### Run Individual Tests
```bash
# From project root
python tests/test_context_detection.py
python tests/test_agent_with_working_finance.py
python tests/test_agno_agent_user_id.py
# ... etc
```

## Test Categories

### Core Agent Tests
- `test_agno_agent_user_id.py` - Tests user ID handling in AgnoPersonalAgent
- `test_agent_with_working_finance.py` - Tests agent with YFinance tools
- `test_context_detection.py` - Tests dynamic model context size detection

### Tool Tests
- `test_tools_direct.py` - Comprehensive direct testing of all tool classes
- `test_tools_simple.py` - Simple comprehensive test for Personal Agent tools
- `test_tool_call_detection.py` - Tests tool call detection in AgnoPersonalAgent

### Integration Tests
- `test_knowledge_tools_integration.py` - Tests KnowledgeTools integration with memory
- `test_streamlit_integration.py` - Tests Streamlit integration with SemanticMemoryManager

### Debug and Analysis Scripts
- `debug_yfinance_tools.py` - Debug script for YFinance tools
- `fix_yfinance_401.py` - Fix for YFinance 401 errors
- `analyze_knowledge_tools.py` - Analysis of KnowledgeTools from agno.tools.knowledge
- `similarity_analysis.py` - Analysis of similarity calculations
- `quick_knowledge_test.py` - Quick test for knowledge search functionality

### Test Runners
- `run_all_tests.py` - Runs all tests in the directory
- `run_knowledge_integration_test.py` - Specific runner for knowledge integration tests

## Import Path Changes

All test files have been updated to use the correct import paths from the tests/ directory:

```python
# Old (when in root directory)
sys.path.insert(0, str(Path(__file__).parent / "src"))

# New (in tests/ directory)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

## Test Organization Benefits

1. **Clean Project Structure** - All tests are now organized in one place
2. **Proper Import Paths** - All imports work correctly from the tests/ directory
3. **Easy Test Discovery** - All test files are in a predictable location
4. **Batch Testing** - Use `run_all_tests.py` to run all tests at once
5. **Better Maintenance** - Easier to manage and update test files

## Adding New Tests

When adding new test files:

1. Place them in the `tests/` directory
2. Use the proper import path pattern:
   ```python
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
   ```
3. Name test files with descriptive names (preferably starting with `test_`)
4. The test runner will automatically discover and run new test files

## Notes

- All test files maintain their original functionality
- Import paths have been updated to work from the tests/ directory
- The test runner provides comprehensive output and summary statistics
- Tests can still be run individually or as a batch
# SemanticMemoryManager Capability Tests

This directory contains comprehensive test suites for validating the direct SemanticMemoryManager capabilities in the refactored AgnoPersonalAgent.

## Test Files

### 1. `test_memory_capabilities_standalone.py` ⭐ **RECOMMENDED**
- **Standalone, self-contained test suite**
- No external dependencies on other test files
- Tests all 8 memory tools with comprehensive timing information
- Easy to run and debug

### 2. `test_direct_semantic_memory_capabilities.py`
- Original comprehensive test suite
- Requires import from other modules
- More modular but may have import issues

### 3. `run_memory_capability_tests.py`
- Test runner for the original test suite
- May have import path issues

## What Gets Tested

The test suite validates all **8 memory tools** from the refactored AgnoPersonalAgent:

1. **`store_user_memory`** - Store new memories with topics
2. **`query_memory`** - Search memories semantically  
3. **`update_memory`** - Update existing memories ✨ *NEW*
4. **`delete_memory`** - Delete specific memories ✨ *NEW*
5. **`clear_memories`** - Clear all user memories ✨ *NEW*
6. **`get_recent_memories`** - Get recent memories
7. **`get_all_memories`** - Get all memories
8. **`get_memory_stats`** - Get memory statistics ✨ *NEW*

## Test Features

### 📊 **Performance Benchmarking**
- Bulk storage timing (25+ test facts)
- Individual operation timing
- Average response times
- Memory throughput analysis

### 🔍 **Semantic Search Testing**
- Direct keyword matches
- Semantic similarity searches
- Topic-based searches
- Complex multi-term queries

### 🧠 **Memory Management**
- Create, Read, Update, Delete operations
- Duplicate detection validation
- Error handling verification
- Memory statistics analysis

### 📈 **Comprehensive Reporting**
- Detailed timing results
- Performance summaries
- Success/failure rates
- Error handling validation

## Requirements

Before running the tests, ensure you have:

- ✅ **Ollama server running** with `llama3.2:3b` model
- ✅ **Personal agent dependencies installed** (`pip install -r requirements.txt`)
- ✅ **Write access** to `./data/test_agno_comprehensive/` directory
- ✅ **Python 3.8+** with asyncio support

## How to Run

### Option 1: Standalone Test (Recommended)

```bash
cd tests/
python test_memory_capabilities_standalone.py
```

### Option 2: Original Test Suite

```bash
cd tests/
python test_direct_semantic_memory_capabilities.py
```

### Option 3: Test Runner

```bash
cd tests/
python run_memory_capability_tests.py
```

## Test Data

The test suite uses **25 comprehensive test facts** covering:

- **Personal Information** (name, age, location, background)
- **Work & Career** (job, skills, goals, projects)
- **Hobbies & Interests** (hiking, music, photography, cooking)
- **Food Preferences** (vegetarian, cuisines, allergies)
- **Health & Fitness** (exercise, supplements, wellness)
- **Technology & Skills** (programming languages, tools, interests)

## Expected Output

The test suite provides detailed output including:

```
🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠
🧠 SEMANTIC MEMORY MANAGER CAPABILITY TESTS 🧠
🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠

🔧 Setting up AgnoPersonalAgent...
✅ Agent setup completed in 2.34 seconds

🧹 Testing clear_memories...
✅ Clear operation took 0.123 seconds

💾 Testing bulk storage of 25 memories...
✅ Stored successfully in 0.045s
✅ Stored successfully in 0.038s
...

📊 Bulk Storage Results:
   Total time: 1.23 seconds
   Average time per memory: 0.049 seconds
   Successful stores: 25
   Duplicate detections: 0

🔍 Testing semantic search capabilities...
✅ Found results in 0.156s
🎯 Found expected topics: ['work', 'career']
...

================================================================================
🎯 COMPREHENSIVE TEST RESULTS
================================================================================

⏱️ TIMING RESULTS:
----------------------------------------
agent_setup: 2.340s
clear_memories: 0.123s
bulk_storage:
  total_time: 1.230s
  average_time: 0.049s
  successful_stores: 25
  duplicate_detections: 0
semantic_search:
  total_time: 2.145s
  average_time: 0.179s
  successful_searches: 12/12

📊 PERFORMANCE SUMMARY:
----------------------------------------
Memory Storage:
  • Stored 25 memories successfully
  • Detected 0 duplicates
  • Average storage time: 0.049s per memory

Semantic Search:
  • 12/12 searches successful
  • Average search time: 0.179s per query

✅ COMPREHENSIVE TESTING COMPLETED!
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Use the standalone test: `test_memory_capabilities_standalone.py`
   - Ensure you're running from the `tests/` directory

2. **Ollama Connection Issues**
   - Verify Ollama is running: `ollama list`
   - Check model availability: `ollama pull llama3.2:3b`

3. **Permission Errors**
   - Ensure write access to `./data/test_agno_comprehensive/`
   - Create directory manually if needed: `mkdir -p data/test_agno_comprehensive`

4. **Memory Errors**
   - Reduce test data size if running on limited memory
   - Close other applications to free up RAM

### Debug Mode

For more detailed output, the tests run with `debug=True` by default, providing:
- Detailed tool call information
- Memory operation logging
- Error stack traces
- Performance metrics

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run Memory Capability Tests
  run: |
    cd tests/
    python test_memory_capabilities_standalone.py
```

## Performance Benchmarks

Expected performance on typical hardware:

- **Agent Setup**: 2-5 seconds
- **Memory Storage**: 0.03-0.08 seconds per memory
- **Semantic Search**: 0.1-0.3 seconds per query
- **Memory Management**: 0.01-0.05 seconds per operation

## Contributing

When adding new memory capabilities:

1. Add test cases to the test suite
2. Update the expected tool count (currently 8)
3. Add timing benchmarks for new operations
4. Update this README with new features

---

**Happy Testing! 🧠✨**
# Tool Call Debug Output Test

This test verifies that the fix for Streamlit debug output is working correctly.

## What it tests

The test script `test_tool_call_debug_output.py` verifies that:

1. **Tool call arguments are properly parsed** - Instead of showing empty `{}`, the debug output should show actual argument values
2. **Different tool types work correctly** - Tests news search, finance queries, and memory operations
3. **Debug information is complete** - Verifies all debug fields are populated correctly

## How to run

```bash
# From the project root directory
cd /Users/egs/repos/personal_agent

# Run the test
python tests/test_tool_call_debug_output.py
```

## What you should see

### Before the fix:
```
Arguments: {}
```

### After the fix:
```
Arguments: {
  "max_results": 5,
  "query": "conflict in the Middle East and Iran's activities"
}
```

## Test scenarios

1. **News Search Test** - Triggers DuckDuckGo tool with query parameters
2. **Finance Query Test** - Triggers YFinance tool with stock symbol
3. **Memory Query Test** - Triggers memory tools (may have no arguments for some functions)

## Expected output

The test will show:
- ✅ Arguments properly parsed as dictionary
- Actual parameter names and values
- Tool call counts and debug information
- Success/failure status for each test

## Troubleshooting

If the test fails:
1. Make sure Ollama is running
2. Check that your model is available
3. Verify network connectivity for web searches
4. Check the error messages for specific issues

## What this fixes

This test validates the fix for the Streamlit debug output issue where tool call arguments were showing as empty `{}` instead of the actual parameters passed to the tools. The fix ensures proper JSON parsing and display of tool call arguments in the debug interface.
