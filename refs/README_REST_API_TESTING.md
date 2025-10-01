# Personal Agent REST API Testing

This directory contains comprehensive testing tools for the Personal Agent REST API endpoints.

## Overview

The Personal Agent REST API provides programmatic access to memory and knowledge storage capabilities, allowing external systems to interact with the agent's memory and knowledge base via standard HTTP requests.

## Files

### 1. `test_rest_api.py` - Comprehensive Test Suite
A complete test suite that validates all REST API endpoints with proper error handling and validation.

**Features:**
- Tests all memory endpoints (store, store-url, search, list, stats)
- Tests all knowledge endpoints (store-text, store-url, search, status)  
- Tests system endpoints (health, status)
- Validates error handling with invalid requests
- Provides detailed test results and statistics
- Tracks created memory IDs for cleanup

**Usage:**
```bash
# Basic usage
python test_rest_api.py

# With custom host/port
python test_rest_api.py --host localhost --port 8001

# Verbose output for debugging
python test_rest_api.py --verbose
```

### 2. `example_rest_api_usage.py` - Practical Examples
Demonstrates real-world usage of the REST API with practical examples for memory and knowledge storage.

**Features:**
- Shows how to store personal memories with topics
- Demonstrates URL content extraction and storage
- Provides memory search examples
- Shows knowledge base operations
- Includes error handling and status checking

**Usage:**
```bash
# Run all examples
python example_rest_api_usage.py

# With custom host/port
python example_rest_api_usage.py --host localhost --port 8001
```

### 3. `debug_rest_api.py` - Diagnostic Tool
A diagnostic script that helps identify and troubleshoot REST API issues.

**Features:**
- Tests API connectivity and health
- Checks system status and component availability
- Identifies why 503 errors occur
- Provides specific troubleshooting recommendations
- Tests basic memory operations

**Usage:**
```bash
# Basic diagnostic
python debug_rest_api.py

# With custom host/port
python debug_rest_api.py --host localhost --port 8001
```

## Prerequisites

1. **Personal Agent Streamlit App Running**
   ```bash
   streamlit run src/personal_agent/tools/paga_streamlit_agno.py
   ```

2. **REST API Server Active**
   - The REST API server starts automatically with the Streamlit app
   - Default URL: http://localhost:8001
   - Check the Streamlit UI for the green "REST API server running" indicator
   - **Important**: If you see "Memory system not available" errors, restart the Streamlit app to activate the global state manager

3. **Python Dependencies**
   ```bash
   pip install requests beautifulsoup4
   ```

## Architecture Notes

The REST API uses a **Global State Manager** to share agent/team instances between the Streamlit main thread and the REST API server thread. This solves the fundamental issue where Streamlit's session state is thread-local and cannot be accessed across threads.

**Key Components:**
- `global_state.py` - Thread-safe state manager
- `rest_api.py` - REST API server with global state integration
- `paga_streamlit_agno.py` - Streamlit app with state synchronization

## API Endpoints

### Memory Endpoints
- `POST /api/v1/memory/store` - Store text content as memory
- `POST /api/v1/memory/store-url` - Extract and store URL content as memory
- `GET /api/v1/memory/search?q=query` - Search existing memories
- `GET /api/v1/memory/list` - List all memories
- `GET /api/v1/memory/stats` - Get memory statistics

### Knowledge Endpoints
- `POST /api/v1/knowledge/store-text` - Store text in knowledge base
- `POST /api/v1/knowledge/store-url` - Extract and store URL content in knowledge base
- `GET /api/v1/knowledge/search?q=query` - Search knowledge base
- `GET /api/v1/knowledge/status` - Get knowledge base status

### System Endpoints
- `GET /api/v1/health` - Health check
- `GET /api/v1/status` - System status

## Example Usage

### Store Memory
```bash
curl -X POST http://localhost:8001/api/v1/memory/store \
  -H "Content-Type: application/json" \
  -d '{"content": "I work at Google as a software engineer", "topics": ["work", "career"]}'
```

### Store Memory from URL
```bash
curl -X POST http://localhost:8001/api/v1/memory/store-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "title": "Important Article", "topics": ["research"]}'
```

### List All Memories
```bash
curl -X GET "http://localhost:8001/api/v1/memory/list" \
  -H "Content-Type: application/json"

# With limit
curl -X GET "http://localhost:8001/api/v1/memory/list?limit=5" \
  -H "Content-Type: application/json"
```

### Search Memories
```bash
curl "http://localhost:8001/api/v1/memory/search?q=work&limit=5&similarity_threshold=0.3"
```

### Get Memory Statistics
```bash
curl -X GET "http://localhost:8001/api/v1/memory/stats" \
  -H "Content-Type: application/json"
```

### Store Knowledge
```bash
curl -X POST http://localhost:8001/api/v1/knowledge/store-text \
  -H "Content-Type: application/json" \
  -d '{"content": "Python is a programming language...", "title": "Python Guide", "file_type": "md"}'
```

### Store Knowledge from URL
```bash
curl -X POST http://localhost:8001/api/v1/knowledge/store-url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://docs.python.org/3/", "title": "Python Documentation"}'
```

### Search Knowledge
```bash
curl "http://localhost:8001/api/v1/knowledge/search?q=python&mode=auto&limit=5"
```

### System Status
```bash
# Health check
curl -X GET "http://localhost:8001/api/v1/health"

# System status
curl -X GET "http://localhost:8001/api/v1/status"
```

## Testing Workflow

1. **Start the Personal Agent**
   ```bash
   streamlit run src/personal_agent/tools/paga_streamlit_agno.py
   ```

2. **Verify API is Running**
   - Check Streamlit UI for "REST API server running" message
   - Or test health endpoint: `curl http://localhost:8001/api/v1/health`

3. **Run Comprehensive Tests**
   ```bash
   python test_rest_api.py --verbose
   ```

4. **Run Practical Examples**
   ```bash
   python example_rest_api_usage.py
   ```

5. **Check Results**
   - View stored memories and knowledge in the Streamlit UI
   - Use the search functionality to find stored content
   - Check test results and statistics

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure Streamlit app is running
   - Check that REST API server started (look for green indicator in UI)
   - Verify port 8001 is not blocked

2. **Memory/Knowledge System Not Available**
   - Wait for agent/team initialization to complete
   - Check system status endpoint: `curl http://localhost:8001/api/v1/status`
   - Restart Streamlit app if needed

3. **URL Extraction Fails**
   - Network connectivity issues
   - Invalid URL format
   - Website blocking automated requests
   - These are handled gracefully in the test scripts

4. **Test Failures**
   - Check verbose output for detailed error messages
   - Verify all dependencies are installed
   - Ensure sufficient system resources

### Debug Mode

Run tests with verbose output to see detailed request/response information:
```bash
python test_rest_api.py --verbose
```

This will show:
- Full request URLs and payloads
- Response status codes and bodies
- Detailed error messages
- Step-by-step test execution

## Integration

The REST API can be integrated into external applications:

1. **Python Applications** - Use the `PersonalAgentAPIClient` class from the examples
2. **Web Applications** - Make HTTP requests to the endpoints
3. **Mobile Apps** - Use standard HTTP client libraries
4. **Automation Scripts** - Integrate with CI/CD pipelines or cron jobs
5. **Third-party Services** - Webhook integrations and data synchronization

## Security Considerations

- The API currently runs without authentication (suitable for local development)
- For production use, consider adding API keys or OAuth
- CORS is enabled for cross-origin requests
- Input validation is performed on all endpoints
- URL extraction includes safety checks

## Performance Notes

- Memory and knowledge operations may take 1-2 seconds for indexing
- URL extraction depends on network speed and target website
- Large content may take longer to process
- The API uses threading to avoid blocking the Streamlit UI

## Support

For issues or questions:
1. Check the test script output for detailed error messages
2. Review the Streamlit app logs
3. Verify system status via the `/api/v1/status` endpoint
4. Ensure all prerequisites are met
