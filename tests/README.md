# Personal Agent Test Suite Organization

This document describes the organization of the Personal Agent test suite and how to run tests effectively.

## Overview

The test suite has been reorganized into logical subdirectories based on system components. This makes it easier to:
- Find tests related to specific features
- Run tests for particular components independently
- Understand test coverage at a glance
- Onboard new developers

**Total Test Files**: ~110 organized tests + 28 archived fix tests

## Directory Structure

```
tests/
├── core/                    # Critical core managers (5 tests)
├── system/                  # System integration tests (49 tests)
├── memory/                  # Memory system tests (28 tests)
├── knowledge/               # Knowledge base tests (13 tests)
├── team/                    # Team coordination tests (7 tests)
├── user/                    # User management tests (6 tests)
├── tools/                   # Tools & MCP integration (9 tests)
├── ui/                      # Streamlit/UI tests (4 tests)
├── config/                  # Configuration tests (2 tests)
├── archived/                # Historical/temporary tests
│   ├── fixes/              # Fix tests from development iterations (28)
│   └── README.md           # Documentation for archived tests
└── conftest.py             # Shared pytest fixtures
```

## Component Tests

### Core Managers (5 tests)
**Location**: `tests/core/`

Tests for the critical foundational manager classes:
- `test_agent_memory_manager.py` - Memory manager unit/async tests
- `test_agent_knowledge_manager.py` - Knowledge manager tests
- `test_agent_tool_manager.py` - Tool registration and management
- `test_agent_instruction_manager.py` - Instruction level management
- `test_agent_model_manager.py` - Model provider management

**Why they matter**: These managers are fundamental to system operation. All other components depend on them.

**Run with**: `pytest tests/core/ -v`

### Memory System (28 tests)
**Location**: `tests/memory/`

Comprehensive tests for the dual-memory architecture:
- Memory manager operations (storage, retrieval, search)
- Semantic deduplication and fact restatement
- LightRAG integration and graph memory
- Dual storage synchronization
- Memory interfaces and utilities

**Coverage**:
- Local SQLite memory operations
- LanceDB vector search
- LightRAG graph memory
- Memory priority and topics
- Comprehensive search across 52+ diverse memory samples

**Run with**: `pytest tests/memory/ -v`

### Knowledge Base (13 tests)
**Location**: `tests/knowledge/`

Tests for knowledge management:
- Agent knowledge manager
- Knowledge coordinator (routing between local and graph)
- Combined knowledge base operations
- Knowledge search and retrieval
- Knowledge graph relationships
- Tools integration

**Run with**: `pytest tests/knowledge/ -v`

### Team Coordination (7 tests)
**Location**: `tests/team/`

Tests for multi-agent team functionality:
- Team creation and management
- Instruction level coordination
- Agent member management
- Team memory and state
- Reasoning team workflows

**Run with**: `pytest tests/team/ -v`

### User Management (6 tests)
**Location**: `tests/user/`

Tests for multi-user support:
- User ID propagation across system
- User context switching
- User endpoints and REST API
- Persistent user context
- User profile management

**Run with**: `pytest tests/user/ -v`

### Tools & MCP Integration (9 tests)
**Location**: `tests/tools/`

Tests for tool system and MCP servers:
- MCP server availability
- Tool registration and discovery
- Tool call detection and execution
- Tool parameter handling
- External tools integration

**Run with**: `pytest tests/tools/ -v`

### Streamlit UI (4 tests)
**Location**: `tests/ui/`

Tests for Streamlit web interface:
- UI component integration
- Interface workflows
- Streamlit memory operations
- Dashboard functionality

**Run with**: `pytest tests/ui/ -v`

### Configuration (2 tests)
**Location**: `tests/config/`

Tests for system configuration:
- Environment variable handling
- Config extraction
- Path management
- Filesystem operations

**Run with**: `pytest tests/config/ -v`

### System Integration (49 tests)
**Location**: `tests/system/`

Broader integration tests that span multiple components:
- Agent initialization and workflow
- Docker integration
- REST API endpoints
- End-to-end scenarios
- Error handling and edge cases
- Streaming and responses

**Run with**: `pytest tests/system/ -v`

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Component Tests
```bash
# Run only core manager tests
pytest tests/core/ -v

# Run only memory tests
pytest tests/memory/ -v

# Run only team tests
pytest tests/team/ -v
```

### Run Tests by Marker
Tests are marked with pytest markers for flexible filtering:

```bash
# Run all critical tests (core managers)
pytest -m core -v

# Run only integration tests
pytest -m integration -v

# Run all except slow tests
pytest -m "not slow" -v
```

### Run with Coverage
```bash
pytest tests/ --cov=src/personal_agent --cov-report=html
```

### Run in Parallel
```bash
pytest tests/ -n auto  # Requires pytest-xdist
```

### Run Specific Test File
```bash
pytest tests/memory/test_semantic_memory_manager.py -v
```

### Run Specific Test Function
```bash
pytest tests/memory/test_semantic_memory_manager.py::test_memory_search -v
```

## CI/CD Integration

The test suite is organized to support efficient CI/CD:

1. **Fast feedback**: Run `tests/core/` first (5 tests, <1 min)
2. **Component tests**: Run each component directory in parallel
3. **Integration tests**: Run `tests/system/` for full integration
4. **Coverage**: Generate reports on successful runs

## Adding New Tests

When writing new tests:

1. **Identify the component**: Which system does it test (memory, knowledge, etc)?
2. **Place in correct directory**: Add to `tests/component/test_*.py`
3. **Use appropriate markers**: Apply `@pytest.mark.component` where relevant
4. **Follow naming conventions**: `test_feature_scenario.py`
5. **Add docstrings**: Describe what the test validates

Example:
```python
# tests/memory/test_new_memory_feature.py
"""Tests for the new memory feature."""

import pytest

@pytest.mark.memory
def test_memory_feature_basic():
    """Validate basic memory feature functionality."""
    # Test code here
    pass
```

## Test Organization Principles

1. **Cohesion**: Tests for a component are grouped together
2. **Naming**: Clear, descriptive file and function names
3. **Independence**: Tests can run in any order
4. **Speed**: Fast tests in root directories, slower in subdirectories
5. **Documentation**: Each test file has a docstring explaining its purpose

## Archived Tests

**Location**: `tests/archived/`

The `fixes/` subdirectory contains 28 temporary tests that were created during bug fixes:
- These are not run in regular test suites
- They are preserved for historical reference
- Each is documented with the issue/PR it addresses
- They can be deleted once corresponding issues are marked as resolved

See `tests/archived/fixes/README.md` for details.

## Common Test Patterns

### Testing Async Functions
```python
@pytest.mark.asyncio
async def test_async_memory_operation():
    result = await memory_manager.get_memory(user_id)
    assert result is not None
```

### Testing with Fixtures
```python
def test_with_agent(agent):  # Uses conftest.py fixture
    response = agent.run("test query")
    assert response is not None
```

### Testing Memory Operations
```python
def test_memory_search(user_id):
    manager.add_memory("I like coffee", user_id=user_id)
    results = manager.search_memories("coffee", user_id=user_id)
    assert len(results) > 0
```

## Troubleshooting

### Tests not found
Make sure pytest is discovering tests in subdirectories:
```bash
pytest --collect-only tests/
```

### Import errors
Ensure the package is installed in editable mode:
```bash
pip install -e .
```

### Async test issues
Install pytest-asyncio:
```bash
pip install pytest-asyncio
```

### Missing fixtures
Check that `conftest.py` exists in the tests directory and defines necessary fixtures.

## Performance Notes

- **Fast tests**: `tests/core/` - <1 minute
- **Medium tests**: `tests/memory/`, `tests/knowledge/` - 2-5 minutes
- **Slow tests**: `tests/system/` - 5+ minutes (Docker integration)
- **Total suite**: ~15-20 minutes

For rapid development, run only the component you're working on.

## Future Improvements

- [ ] Add pytest markers for test classification
- [ ] Set up parallel test execution in CI/CD
- [ ] Add performance benchmarks
- [ ] Increase coverage to 80%+
- [ ] Document test data/fixtures
- [ ] Add integration test scenarios

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
