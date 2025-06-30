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
