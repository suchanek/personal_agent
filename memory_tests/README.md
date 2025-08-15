# Memory Tests

This directory contains tests for the Personal Agent's memory systems.

## CLI Memory Commands Tests

The `test_cli_memory_commands.py` script tests the CLI memory commands to ensure they properly update both storage systems:
1. Local SQLite memory system
2. LightRAG graph memory system

### Purpose

These tests verify that the CLI memory commands correctly:
- Store memories in both storage systems
- Retrieve memories from both storage systems
- Delete memories from both storage systems
- Handle errors gracefully

### Running the Tests

To run the CLI memory commands tests:

```bash
./memory_tests/run_cli_memory_tests.sh
```

Or directly:

```bash
python memory_tests/test_cli_memory_commands.py
```

### Test Coverage

The tests cover:
- Memory storage operations
- Memory retrieval operations
- Memory deletion operations
- Error handling
- Edge cases

### Expected Results

The tests should output detailed information about each test case and whether it passed or failed. A successful test run will end with a message indicating all tests passed.

## Adding New Tests

When adding new memory-related tests:
1. Create a new test script in this directory
2. Update this README to document the new tests
3. Consider adding a shell script to run the tests