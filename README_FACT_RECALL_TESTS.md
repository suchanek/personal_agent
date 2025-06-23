# Fact Recall Testing Suite

This directory contains comprehensive testing tools for validating fact recall capabilities in the Personal Agent memory system.

## Overview

The fact recall tests are designed to address ongoing recall issues by providing structured testing of:
- Fact storage in memory
- Basic fact retrieval with direct questions
- Semantic search and topic-based queries
- Edge cases and challenging scenarios
- Memory persistence across queries

## Test Files

### 1. `test_fact_recall_comprehensive.py`
**Comprehensive fact recall testing suite**

- **Purpose**: Full validation of fact recall capabilities
- **Features**:
  - Stores 40+ structured facts from `eric_facts.json` and `send_facts_helper.py`
  - Tests basic fact recall with direct questions
  - Tests semantic search and topic-based queries
  - Tests edge cases and challenging scenarios
  - Tests memory persistence across queries
  - Generates detailed test reports with performance metrics
- **Runtime**: ~5-10 minutes
- **Use Case**: Complete validation after system changes

### 2. `test_quick_fact_recall.py`
**Quick fact recall validation**

- **Purpose**: Fast debugging and validation of basic recall
- **Features**:
  - Stores 5 key facts
  - Tests basic recall with simple queries
  - Tests direct memory search functionality
  - Quick pass/fail assessment
- **Runtime**: ~1-2 minutes
- **Use Case**: Quick debugging and daily validation

### 3. `run_fact_recall_tests.py`
**Test runner script**

- **Purpose**: Easy execution of recall tests
- **Features**:
  - Interactive or command-line execution
  - Options for quick, comprehensive, or both tests
  - Clear result reporting
- **Usage**: `python run_fact_recall_tests.py [option]`

## Quick Start

### Run Quick Test (Recommended for debugging)
```bash
python run_fact_recall_tests.py quick
# or
python run_fact_recall_tests.py 1
```

### Run Comprehensive Test
```bash
python run_fact_recall_tests.py comprehensive
# or
python run_fact_recall_tests.py 2
```

### Run Both Tests
```bash
python run_fact_recall_tests.py both
# or
python run_fact_recall_tests.py 3
```

### Interactive Mode
```bash
python run_fact_recall_tests.py
# Will prompt for test selection
```

## Test Categories

### Basic Info Tests
- Name, email, phone, address
- GitHub profile, current projects
- Basic biographical information

### Education Tests
- High school, undergraduate, graduate education
- Degrees, achievements, dissertation details
- Academic honors and rankings

### Professional Tests
- Current employment, job responsibilities
- Technical skills and programming languages
- Work experience and career history

### Achievement Tests
- Major accomplishments and innovations
- Database and software development
- Research contributions

### Technical Skills Tests
- Programming languages and tools
- Machine learning and data science
- System administration and certifications

## Test Metrics

### Success Rate Thresholds
- **Basic Fact Recall**: 70% pass rate required
- **Semantic Search**: 60% pass rate required
- **Edge Cases**: 50% pass rate required
- **Memory Persistence**: 80% consistency required

### Performance Metrics
- Response time per query
- Fact storage success rate
- Memory search functionality
- Overall system reliability

## Interpreting Results

### ✅ Excellent (80%+ success rate)
- Fact recall system is working well
- No immediate action required
- Consider running comprehensive tests periodically

### ⚠️ Good (60-79% success rate)
- Basic functionality working with some issues
- Consider investigating specific failure patterns
- May need semantic search improvements

### ❌ Poor (<60% success rate)
- Significant recall problems detected
- Immediate investigation required
- Check memory storage and retrieval mechanisms
- Consider model upgrade or configuration changes

## Troubleshooting

### Common Issues

1. **No facts stored successfully**
   - Check agent initialization
   - Verify memory system is enabled
   - Check database connectivity

2. **Facts stored but not recalled**
   - Check memory search functionality
   - Verify semantic similarity thresholds
   - Test direct memory tool access

3. **Inconsistent recall results**
   - Check memory persistence
   - Verify database integrity
   - Test with different query patterns

4. **Slow response times**
   - Check model performance
   - Verify database optimization
   - Consider memory system tuning

### Debug Steps

1. **Run Quick Test First**
   ```bash
   python run_fact_recall_tests.py quick
   ```

2. **Check Agent Logs**
   - Enable debug mode in tests
   - Review memory tool execution
   - Check for error messages

3. **Test Direct Memory Access**
   - Use the direct memory search test
   - Verify database contains stored facts
   - Check memory tool functionality

4. **Run Comprehensive Test**
   ```bash
   python run_fact_recall_tests.py comprehensive
   ```

## Integration with Existing Tests

These fact recall tests complement the existing test suite:

- **`test_pydantic_validation_fix.py`**: Validates tool calling and memory storage
- **`test_fact_recall_*.py`**: Validates fact retrieval and recall accuracy
- **Memory system tests**: Validate underlying memory infrastructure

## Test Data Sources

The tests use structured fact data from:

1. **`eric_facts.json`**: Comprehensive JSON structure with categorized facts
2. **`send_facts_helper.py`**: Organized fact categories for easy testing
3. **Hardcoded test facts**: Specific facts designed for testing edge cases

## Customization

### Adding New Test Categories
1. Edit the `_load_test_facts()` method in the test classes
2. Add new fact categories with appropriate test data
3. Update test queries to include new categories

### Modifying Success Thresholds
1. Adjust threshold values in test methods
2. Consider your specific use case requirements
3. Update documentation to reflect changes

### Adding New Test Scenarios
1. Create new test methods in the test classes
2. Follow the existing pattern for query/expected_terms
3. Update the main test execution flow

## Best Practices

1. **Run Quick Test First**: Always start with the quick test for rapid feedback
2. **Regular Testing**: Run tests after system changes or model updates
3. **Monitor Trends**: Track success rates over time to identify degradation
4. **Investigate Failures**: Don't ignore failed tests - they indicate real issues
5. **Update Test Data**: Keep test facts current and relevant

## Future Enhancements

Potential improvements to the test suite:

1. **Automated Scheduling**: Run tests on a schedule
2. **Performance Benchmarking**: Track response times over time
3. **Regression Testing**: Compare results across versions
4. **Custom Fact Sets**: Allow users to test with their own facts
5. **Integration Testing**: Test with real user scenarios

## Support

If you encounter issues with the fact recall tests:

1. Check the troubleshooting section above
2. Review the test output for specific error messages
3. Enable debug mode for more detailed logging
4. Consider running individual test components to isolate issues

The fact recall testing suite is designed to provide comprehensive validation of your Personal Agent's memory capabilities, helping ensure reliable fact storage and retrieval for optimal user experience.
