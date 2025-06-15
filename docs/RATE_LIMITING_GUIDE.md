# Rate Limiting Guide for Personal Agent

This guide explains how to configure and use rate limiting in the Personal Agent to prevent hitting API rate limits, particularly with DuckDuckGo search.

## Overview

The Personal Agent now includes built-in rate limiting for DuckDuckGo search operations to prevent the `202 Ratelimit` errors you were experiencing. The rate limiting system includes:

- **Configurable delays** between search requests
- **Automatic retry logic** with exponential backoff
- **Environment variable configuration**
- **Preset configurations** for different use cases

## Quick Start

### 1. Using Environment Variables

Set these environment variables to configure rate limiting:

```bash
# DuckDuckGo specific settings
export DUCKDUCKGO_SEARCH_DELAY=3.0      # 3 seconds between searches
export DUCKDUCKGO_MAX_RETRIES=3         # Retry up to 3 times on rate limit
export DUCKDUCKGO_RETRY_DELAY=10.0      # 10 seconds base retry delay

# Default API settings (for other tools)
export DEFAULT_API_DELAY=1.0            # 1 second default delay
export DEFAULT_MAX_RETRIES=3            # 3 retries default
export DEFAULT_RETRY_DELAY=5.0          # 5 seconds default retry delay
```

### 2. Using Preset Configurations

You can apply preset configurations programmatically:

```python
from src.personal_agent.config.rate_limiting import apply_rate_limit_preset

# Apply conservative settings (slower but more reliable)
apply_rate_limit_preset("conservative")

# Apply balanced settings (default)
apply_rate_limit_preset("balanced")

# Apply aggressive settings (faster but higher risk)
apply_rate_limit_preset("aggressive")

# Apply development settings (fast for testing)
apply_rate_limit_preset("development")
```

## Configuration Options

### Rate Limiting Parameters

| Parameter | Description | Default | Recommended Range |
|-----------|-------------|---------|-------------------|
| `search_delay` | Seconds between search requests | 3.0 | 1.0 - 5.0 |
| `max_retries` | Maximum retries on rate limit | 3 | 2 - 5 |
| `retry_delay` | Base delay for retries (exponential backoff) | 10.0 | 5.0 - 15.0 |

### Preset Configurations

| Preset | Search Delay | Max Retries | Retry Delay | Use Case |
|--------|--------------|-------------|-------------|----------|
| `conservative` | 5.0s | 2 | 15.0s | Production, high reliability |
| `balanced` | 3.0s | 3 | 10.0s | Default, good balance |
| `aggressive` | 1.0s | 5 | 5.0s | Development, faster responses |
| `development` | 0.5s | 1 | 2.0s | Testing, minimal delays |

## Usage Examples

### 1. Check Current Configuration

```python
from src.personal_agent.config.rate_limiting import print_rate_limit_config

# Print current configuration
print_rate_limit_config()
```

### 2. Update Configuration Programmatically

```python
from src.personal_agent.config.rate_limiting import set_duckduckgo_rate_limits

# Set custom rate limits
set_duckduckgo_rate_limits(
    search_delay=2.5,
    max_retries=4,
    retry_delay=8.0
)
```

### 3. Test Rate Limiting

Run the test script to verify rate limiting is working:

```bash
python test_rate_limited_search.py
```

### 4. Using in Your Agent

The rate limiting is automatically applied when you create an agent:

```python
from src.personal_agent.core.agno_agent import create_agno_agent

# Create agent with automatic rate limiting
agent = await create_agno_agent(
    model_provider="ollama",
    model_name="llama3.2:3b",
    debug=True
)

# Rate limiting is automatically configured from environment variables
# or default settings
```

## How Rate Limiting Works

### 1. Request Spacing

The system enforces a minimum delay between consecutive search requests:

```python
# If last search was 1 second ago and search_delay is 3.0 seconds,
# the system will wait 2 more seconds before making the next request
```

### 2. Retry Logic

When a rate limit error is detected (HTTP 202 or "ratelimit" in error message):

1. **First retry**: Wait `retry_delay` seconds (e.g., 10s)
2. **Second retry**: Wait `retry_delay * 2` seconds (e.g., 20s)
3. **Third retry**: Wait `retry_delay * 3` seconds (e.g., 30s)
4. **Max retries exceeded**: Return error message

### 3. Error Detection

The system detects rate limiting errors by checking for:
- HTTP status code 202
- "ratelimit" or "rate limit" in error messages
- DuckDuckGo-specific rate limit responses

## Troubleshooting

### Still Getting Rate Limit Errors?

1. **Increase search delay**:
   ```bash
   export DUCKDUCKGO_SEARCH_DELAY=5.0
   ```

2. **Use conservative preset**:
   ```python
   apply_rate_limit_preset("conservative")
   ```

3. **Check your usage patterns**:
   - Are you making many searches in quick succession?
   - Consider batching or spacing out your requests

### Performance vs. Reliability

- **For production**: Use `conservative` or `balanced` presets
- **For development**: Use `development` or `aggressive` presets
- **For heavy usage**: Increase `search_delay` to 5+ seconds

### Monitoring Rate Limiting

The system logs rate limiting activities:

```python
# Enable debug logging to see rate limiting in action
import logging
logging.basicConfig(level=logging.DEBUG)
```

Look for log messages like:
- `Rate limiting: sleeping for X.X seconds`
- `Rate limit hit on attempt X, retrying in X.X seconds...`
- `Search successful on attempt X`

## Advanced Configuration

### Custom Rate Limiting for Other Tools

You can extend the rate limiting system for other tools:

```python
from src.personal_agent.config.rate_limiting import RateLimitConfig

# Add rate limiting for a custom tool
RateLimitConfig.update_tool_config("my_custom_tool", 
    search_delay=2.0,
    max_retries=3,
    retry_delay=5.0
)

# Get configuration for your tool
config = RateLimitConfig.get_tool_config("my_custom_tool")
```

### Environment Variable Priority

Configuration is loaded in this order (later overrides earlier):
1. Default values in code
2. Environment variables
3. Programmatic updates

## Best Practices

1. **Start Conservative**: Begin with the `conservative` preset and adjust as needed
2. **Monitor Logs**: Watch for rate limiting messages in your logs
3. **Test Thoroughly**: Use the test script to verify your configuration
4. **Environment-Specific**: Use different settings for development vs. production
5. **Gradual Adjustment**: Make small changes to timing parameters

## Files Modified

The rate limiting system includes these new files:

- `src/personal_agent/tools/rate_limited_duckduckgo.py` - Rate-limited DuckDuckGo tools
- `src/personal_agent/config/rate_limiting.py` - Configuration management
- `test_rate_limited_search.py` - Test script
- `docs/RATE_LIMITING_GUIDE.md` - This documentation

And these modified files:

- `src/personal_agent/core/agno_agent.py` - Updated to use rate-limited tools

## Support

If you continue to experience rate limiting issues:

1. Check the logs for specific error messages
2. Try the `conservative` preset
3. Increase the `search_delay` parameter
4. Consider using alternative search methods for high-volume use cases

The rate limiting system should significantly reduce or eliminate the `202 Ratelimit` errors you were experiencing with DuckDuckGo search.
