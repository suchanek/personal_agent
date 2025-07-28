# Ollama Model Testing Script

This script tests multiple Ollama models with the same set of queries at the STANDARD instruction level, logging output to a file and monitoring duration for each query.

## Features

- Tests multiple Ollama models sequentially
- Uses STANDARD instruction level for consistent testing
- Measures initialization time and query response times
- Logs all results to a timestamped JSON file
- Provides detailed error handling and reporting
- Saves results after each model (crash-resistant)
- Generates comprehensive summary reports

## Models Tested

- `qwen3:4b`
- `qwen2.5-coder:3b`
- `qwen2.5:latest`
- `qwen3:8b`

## Test Queries

1. `"hello"` - Basic greeting test
2. `"list your tools"` - Tool awareness test
3. `"give me an analysis of NVDA"` - Complex analysis task

## Prerequisites

1. **Ollama Server**: Make sure Ollama is running and accessible
2. **Models**: Ensure all test models are pulled and available
3. **Environment**: Proper Python environment with all dependencies

### Check Ollama Models

```bash
# List available models
ollama list

# Pull missing models if needed
ollama pull qwen3:4b
ollama pull qwen2.5-coder:3b
ollama pull qwen2.5:latest
ollama pull qwen3:8b
```

## Usage

### Basic Usage

```bash
# Run the full test suite
python test_ollama_models.py
```

### Validation

```bash
# Validate the script before running
python test_script_validation.py
```

## Output

### Console Output

The script provides real-time progress updates:

```
🚀 Starting Ollama Model Testing
📋 Models to test: qwen3:4b, qwen2.5-coder:3b, qwen2.5:latest, qwen3:8b
📝 Queries: 3 queries
📄 Output file: model_test_results_20250124_142000.json
🔧 Instruction level: STANDARD
🌐 Ollama URL: http://localhost:11434

🤖 Testing model: qwen3:4b
==================================================
✅ Agent initialized in 2.34s

📝 Query 1/3: 'hello'
⏱️  Duration: 1.23s
🤖 Response: Hello charlie!

📝 Query 2/3: 'list your tools'
⏱️  Duration: 2.45s
🤖 Response: I have access to several tools including...

📝 Query 3/3: 'give me an analysis of NVDA'
⏱️  Duration: 8.67s
🤖 Response: NVIDIA Corporation (NVDA) is a leading...

✅ Model qwen3:4b completed in 14.69s total
💾 Results saved to model_test_results_20250124_142000.json
```

### JSON Output File

Results are saved to a timestamped JSON file with the following structure:

```json
{
  "qwen3:4b": {
    "model_name": "qwen3:4b",
    "test_timestamp": "2025-01-24T14:20:00.123456",
    "queries": {
      "query_1": {
        "query": "hello",
        "response": "Hello charlie!",
        "duration": 1.23,
        "success": true,
        "error": null
      },
      "query_2": {
        "query": "list your tools",
        "response": "I have access to several tools...",
        "duration": 2.45,
        "success": true,
        "error": null
      },
      "query_3": {
        "query": "give me an analysis of NVDA",
        "response": "NVIDIA Corporation (NVDA)...",
        "duration": 8.67,
        "success": true,
        "error": null
      }
    },
    "total_duration": 14.69,
    "initialization_time": 2.34,
    "errors": []
  },
  "_summary": {
    "total_models_tested": 4,
    "total_queries_per_model": 3,
    "overall_duration": 125.45,
    "test_completed": "2025-01-24T14:25:00.123456",
    "successful_models": ["qwen3:4b", "qwen2.5-coder:3b", "qwen2.5:latest", "qwen3:8b"],
    "failed_models": []
  }
}
```

### Summary Report

At the end, a comprehensive summary is displayed:

```
============================================================
📊 TEST SUMMARY
============================================================
🤖 Models tested: 4
📝 Queries per model: 3
⏱️  Total duration: 125.45s
✅ Successful: 4
❌ Failed: 0

✅ Successful models:
   • qwen3:4b: 14.69s total, 0 errors
   • qwen2.5-coder:3b: 18.23s total, 0 errors
   • qwen2.5:latest: 22.15s total, 0 errors
   • qwen3:8b: 28.34s total, 0 errors

📄 Detailed results saved to: model_test_results_20250124_142000.json
============================================================
```

## Configuration

The script uses settings from your `.env` file:

- `OLLAMA_URL`: Ollama server URL (default: http://localhost:11434)
- `USER_ID`: User identifier for the agent (default: from env.userid)

## Error Handling

The script handles various error scenarios:

1. **Model not available**: Logs error and continues with next model
2. **Network issues**: Retries and logs connection errors
3. **Query timeouts**: Captures timeout errors with duration
4. **Initialization failures**: Logs detailed error messages
5. **Keyboard interruption**: Saves partial results before exiting

## Customization

### Modify Models

Edit the `models` list in the `main()` function:

```python
models = [
    "qwen3:4b",
    "qwen2.5-coder:3b", 
    "qwen2.5:latest",
    "qwen3:8b",
    "llama3.2:3b",  # Add your own models
]
```

### Modify Queries

Edit the `queries` list in the `main()` function:

```python
queries = [
    "hello",
    "list your tools", 
    "give me an analysis of NVDA",
    "what is the weather like?",  # Add your own queries
]
```

### Change Instruction Level

Modify the `instruction_level` parameter in `test_model()`:

```python
instruction_level=InstructionLevel.CONCISE,  # or MINIMAL, EXPLICIT, etc.
```

## Troubleshooting

### Common Issues

1. **"Model not found"**: Run `ollama pull <model_name>` to download the model
2. **"Connection refused"**: Make sure Ollama server is running (`ollama serve`)
3. **"Import errors"**: Ensure you're in the correct Python environment
4. **"Permission denied"**: Make sure the script is executable (`chmod +x test_ollama_models.py`)

### Debug Mode

For more detailed logging, you can modify the script to enable debug mode:

```python
debug=True,  # Change from False to True in create_agno_agent()
```

## Performance Notes

- **Initialization**: Each model requires initialization time (2-5 seconds)
- **Query Time**: Varies by model size and complexity (1-30 seconds per query)
- **Memory Usage**: Models are cleaned up after each test to free memory
- **Total Time**: Expect 2-5 minutes for all 4 models with 3 queries each

## Files Generated

- `model_test_results_YYYYMMDD_HHMMSS.json`: Main results file
- `test_output.json`: Temporary file from validation (can be deleted)

## Results Analysis

### Parsing and Summarizing Results

Use the included `parse_test_results.py` script to analyze the JSON output:

```bash
# Basic analysis (console output only)
python parse_test_results.py model_test_results_20250124_142000.json

# Generate all outputs (charts, CSV, detailed report)
python parse_test_results.py model_test_results_20250124_142000.json --all

# Generate specific outputs
python parse_test_results.py model_test_results_20250124_142000.json --charts --csv --report

# Specify output directory
python parse_test_results.py model_test_results_20250124_142000.json --all --output-dir analysis/
```

### Parser Features

- **Rich Console Output**: Beautiful tables and summaries with color coding
- **Performance Charts**: Visual comparisons of model performance (requires matplotlib/seaborn)
- **CSV Export**: Structured data for spreadsheet analysis
- **Detailed Reports**: Comprehensive text reports with full analysis
- **Error Analysis**: Detailed breakdown of failures and issues

### Parser Output Examples

**Console Summary:**
- Executive summary with key metrics
- Model performance comparison table
- Detailed query analysis with response previews

**Generated Files:**
- `model_performance_comparison.png` - Bar charts comparing models
- `query_performance_heatmap.png` - Heatmap of response times
- `model_test_summary.csv` - Structured data export
- `detailed_report.txt` - Comprehensive text analysis

### Parser Dependencies

For chart generation, install additional dependencies:

```bash
pip install matplotlib seaborn pandas rich
```

The parser works without these dependencies but will skip chart generation.

## Integration

This script can be integrated into CI/CD pipelines or automated testing workflows. The JSON output format makes it easy to parse results programmatically for further analysis or reporting.

### Example Workflow

```bash
# 1. Run the model tests
python test_ollama_models.py

# 2. Parse and analyze results
python parse_test_results.py model_test_results_*.json --all --output-dir analysis/

# 3. View results
ls analysis/
# charts/model_performance_comparison.png
# charts/query_performance_heatmap.png
# model_test_summary.csv
# detailed_report.txt
```
