#!/usr/bin/env python3
"""
Test script to get top 5 headlines about Middle East unrest using DuckDuckGo search.
This demonstrates the correct way to search for news headlines.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agno.tools.duckduckgo import DuckDuckGoTools


async def get_middle_east_headlines():
    """Get top 5 headlines about Middle East unrest using DuckDuckGo."""
    
    print("🔍 Searching for Middle East unrest headlines...")
    
    # Create DuckDuckGo tools instance
    ddg_tools = DuckDuckGoTools()
    
    # Search for Middle East unrest news
    search_query = "Middle East unrest news headlines 2024 2025"
    
    try:
        # Use the news search function
        results = ddg_tools.duckduckgo_news(query=search_query, max_results=5)
        
        print("\n📰 Top 5 Headlines about Middle East Unrest:")
        print("=" * 60)
        
        if results and "Here are the news results" in results:
            print(results)
        else:
            print("❌ No results found or unexpected format")
            print(f"Raw results: {results}")
            
    except Exception as e:
        print(f"❌ Error during search: {e}")
        
        # Try alternative search
        try:
            print("\n🔄 Trying alternative search...")
            results = ddg_tools.duckduckgo_search(query=search_query, max_results=5)
            print(f"Alternative results: {results}")
        except Exception as e2:
            print(f"❌ Alternative search also failed: {e2}")


if __name__ == "__main__":
    asyncio.run(get_middle_east_headlines())
