#!/usr/bin/env python3
"""
Test script to directly test the DuckDuckGo search functionality.
"""

import asyncio
import sys
from pathlib import Path

import pytest

from personal_agent.utils import add_src_to_path

add_src_to_path()

from agno.tools.duckduckgo import DuckDuckGoTools


@pytest.mark.asyncio
async def test_direct_duckduckgo():
    """Test DuckDuckGo search directly."""
    
    print("🔍 Testing DuckDuckGo search directly...")
    
    # Create DuckDuckGo tools instance
    ddg_tools = DuckDuckGoTools()
    
    # Test news search
    try:
        print("📰 Searching for Middle East unrest news...")
        results = ddg_tools.duckduckgo_news(
            query="Middle East unrest headlines", 
            max_results=5
        )
        
        print("\n📋 DuckDuckGo News Results:")
        print("=" * 60)
        print(results)
        print("=" * 60)
        
        if results and isinstance(results, str) and len(results) > 100:
            print("\n✅ SUCCESS: DuckDuckGo news search is working!")
        else:
            print("\n⚠️ WARNING: Results seem limited or empty")
            
    except Exception as e:
        print(f"\n❌ ERROR with news search: {e}")
        
    # Test regular search as fallback
    try:
        print("\n🔍 Testing regular DuckDuckGo search...")
        results = ddg_tools.duckduckgo_search(
            query="Middle East unrest news 2024", 
            max_results=5
        )
        
        print("\n📋 DuckDuckGo Search Results:")
        print("=" * 60)
        print(results)
        print("=" * 60)
        
        if results and isinstance(results, str) and len(results) > 100:
            print("\n✅ SUCCESS: DuckDuckGo regular search is working!")
        else:
            print("\n⚠️ WARNING: Results seem limited or empty")
            
    except Exception as e:
        print(f"\n❌ ERROR with regular search: {e}")


@pytest.mark.asyncio
async def main():
    """Run the test asynchronously."""
    await test_direct_duckduckgo()


if __name__ == "__main__":
    asyncio.run(main())
