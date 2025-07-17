# LightRAG Timeout Fix Summary

## Problem
The LightRAG server was failing to process files longer than about 8k characters with `httpx.ReadTimeout` errors. The error occurred in the Ollama client when making HTTP requests for text processing/embedding generation on large documents.

## Root Cause
The issue was caused by default timeout settings in the httpx client library used by the Ollama Python client. Even though the LightRAG configuration had timeout settings, the underlying HTTP client was using shorter default timeouts that weren't being properly overridden.

## Solution Applied
Applied extended timeout configurations at multiple levels:

### 1. Environment Variables (env.server)
- Extended all HTTP timeouts to 4 hours (14400 seconds)
- Increased Ollama request timeout to 4 hours
- Reduced PDF chunk size to 512 for better reliability
- Increased retry attempts to 10
- Added TCP keepalive settings for stable connections

### 2. Docker Compose Environment
- Added explicit timeout environment variables in docker-compose.yml
- Configured httpx client timeouts directly
- Set Ollama-specific timeout parameters
- Enabled TCP keepalive for long-running connections

### 3. Key Timeout Settings
```bash
# HTTP Client Timeouts
HTTPX_TIMEOUT=14400          # 4 hours total timeout
HTTPX_CONNECT_TIMEOUT=1200   # 20 minutes connection timeout
HTTPX_READ_TIMEOUT=14400     # 4 hours read timeout
HTTPX_WRITE_TIMEOUT=1200     # 20 minutes write timeout
HTTPX_POOL_TIMEOUT=1200      # 20 minutes pool timeout

# Ollama Client Timeouts
OLLAMA_TIMEOUT=14400         # 4 hours for Ollama operations
OLLAMA_REQUEST_TIMEOUT=14400 # 4 hours for individual requests
OLLAMA_KEEP_ALIVE=7200       # Keep model loaded for 2 hours

# Processing Configuration
PDF_CHUNK_SIZE=512           # Smaller chunks for better reliability
MAX_RETRIES=10               # More retries for large documents
RETRY_DELAY=120              # 2 minutes between retries
BATCH_SIZE=1                 # Process one document at a time
MAX_CONCURRENT_REQUESTS=1    # Single threaded processing
```

## Files Modified
1. `lightrag_server/env.server` - Added extended timeout environment variables
2. `lightrag_server/docker-compose.yml` - Added timeout environment variables to container
3. `fix_lightrag_timeout.py` - Created automated fix script

## Testing
The fix was applied and the LightRAG container was successfully restarted with the new timeout settings. The server is now running properly and should be able to handle large documents (>8k characters) without timeout errors.

## Usage
To apply this fix in the future, run:
```bash
python3 fix_lightrag_timeout.py
```

This script will:
1. Update environment configuration with extended timeouts
2. Update Docker Compose configuration
3. Restart the LightRAG container with new settings

## Expected Results
- Large documents (>8k characters) should now process successfully
- PDF processing should be more reliable with smaller chunk sizes
- Increased retry attempts should handle temporary network issues
- TCP keepalive should maintain stable connections during long processing

## Monitoring
Monitor the container logs for successful processing:
```bash
cd lightrag_server && docker-compose logs -f
```

If timeout issues persist, the timeout values can be further increased by modifying the environment variables and restarting the container.
