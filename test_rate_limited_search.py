#!/usr/bin/env python3
"""
Test script for rate-limited DuckDuckGo search functionality.

This script tests the rate limiting features to ensure they work properly
and prevent hitting DuckDuckGo's rate limits.
"""

import asyncio
import time
from src.personal_agent.tools.rate_limited_duckduckgo import RateLimitedDuckDuckGoTools


async def test_rate_limited_search():
    """Test the rate-limited DuckDuckGo search tools."""
    print("🧪 Testing Rate-Limited DuckDuckGo Search Tools")
    print("=" * 50)
    
    # Create rate-limited tools with aggressive settings for testing
    search_tools = RateLimitedDuckDuckGoTools(
        search_delay=2.0,    # 2 seconds between searches
        max_retries=2,       # 2 retries max
        retry_delay=5.0,     # 5 seconds base retry delay
    )
    
    # Test queries
    test_queries = [
        "Python programming",
        "artificial intelligence news",
        "rate limiting best practices"
    ]
    
    print(f"📊 Configuration:")
    print(search_tools.get_rate_limit_info())
    print()
    
    # Test multiple searches to verify rate limiting
    for i, query in enumerate(test_queries, 1):
        print(f"🔍 Test {i}: Searching for '{query}'")
        start_time = time.time()
        
        try:
            result = search_tools.duckduckgo_search(query, max_results=3)
            end_time = time.time()
            
            print(f"⏱️  Search completed in {end_time - start_time:.2f} seconds")
            
            # Show first few lines of result
            result_lines = result.split('\n')[:5]
            for line in result_lines:
                if line.strip():
                    print(f"   {line}")
            
            if len(result.split('\n')) > 5:
                print("   ... (truncated)")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("📈 Final rate limit status:")
    print(search_tools.get_rate_limit_info())


def test_sync_rate_limited_search():
    """Test the synchronous version of rate-limited search."""
    print("🧪 Testing Synchronous Rate-Limited DuckDuckGo Search")
    print("=" * 50)
    
    # Create rate-limited tools
    search_tools = RateLimitedDuckDuckGoTools(
        search_delay=1.5,    # 1.5 seconds between searches
        max_retries=2,       # 2 retries max
        retry_delay=3.0,     # 3 seconds base retry delay
    )
    
    print(f"📊 Initial Configuration:")
    print(search_tools.get_rate_limit_info())
    print()
    
    # Test a single search
    query = "rate limiting techniques"
    print(f"🔍 Searching for '{query}'")
    start_time = time.time()
    
    try:
        result = search_tools.duckduckgo_search(query, max_results=2)
        end_time = time.time()
        
        print(f"⏱️  Search completed in {end_time - start_time:.2f} seconds")
        print("📄 Results:")
        
        # Show result
        result_lines = result.split('\n')[:10]
        for line in result_lines:
            if line.strip():
                print(f"   {line}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("📈 Final rate limit status:")
    print(search_tools.get_rate_limit_info())


if __name__ == "__main__":
    print("🚀 Starting Rate-Limited DuckDuckGo Search Tests")
    print()
    
    # Test synchronous version first
    test_sync_rate_limited_search()
    
    print("\n" + "="*60 + "\n")
    
    # Test async version
    asyncio.run(test_rate_limited_search())
    
    print("✅ All tests completed!")
