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
