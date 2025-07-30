#!/usr/bin/env python3
"""
Debug script to test the query_knowledge_base function and compare with web interface.
"""

import json
import requests
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config.settings import LIGHTRAG_URL, USER_ID

def test_direct_api_call(query: str, mode: str = "hybrid"):
    """Test direct API call to LightRAG server."""
    print(f"\n🔍 Testing direct API call for query: '{query}'")
    print(f"📍 LightRAG URL: {LIGHTRAG_URL}")
    print(f"👤 User ID: {USER_ID}")
    
    url = f"{LIGHTRAG_URL}/query"
    
    # Test with the exact parameters from the tool
    params = {
        "query": query.strip(),
        "mode": mode,
        "top_k": 10,
        "response_type": "Multiple Paragraphs",
    }
    
    print(f"📤 Sending parameters: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.post(url, json=params, timeout=60)
        print(f"📊 Response status: {response.status_code}")
        print(f"📋 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Response type: {type(result)}")
            print(f"📄 Response content preview:")
            
            if isinstance(result, dict):
                content = result.get("response", result.get("content", str(result)))
                print(f"   Content: {content[:200]}...")
                if len(content) > 200:
                    print(f"   (truncated, full length: {len(content)} chars)")
            else:
                content = str(result)
                print(f"   Content: {content[:200]}...")
                if len(content) > 200:
                    print(f"   (truncated, full length: {len(content)} chars)")
                    
            return True, content
        else:
            print(f"❌ Error response: {response.text}")
            return False, response.text
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False, str(e)

def test_with_different_params(query: str):
    """Test with different parameter combinations."""
    print(f"\n🧪 Testing different parameter combinations for: '{query}'")
    
    test_cases = [
        {"mode": "hybrid", "response_type": "Multiple Paragraphs", "top_k": 10},
        {"mode": "hybrid", "response_type": "Bullet Points", "top_k": 10},
        {"mode": "global", "response_type": "Multiple Paragraphs", "top_k": 10},
        {"mode": "naive", "response_type": "Multiple Paragraphs", "top_k": 10},
        {"mode": "hybrid", "response_type": "Multiple Paragraphs", "top_k": 5},
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        params["query"] = query
        
        url = f"{LIGHTRAG_URL}/query"
        try:
            response = requests.post(url, json=params, timeout=60)
            print(f"Parameters: {params}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict):
                    content = result.get("response", result.get("content", str(result)))
                else:
                    content = str(result)
                    
                if content and content.strip():
                    print(f"✅ SUCCESS - Got content ({len(content)} chars)")
                    print(f"Preview: {content[:100]}...")
                else:
                    print(f"⚠️  Empty response")
            else:
                print(f"❌ Failed: {response.text[:100]}...")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

def test_knowledge_tool():
    """Test the actual knowledge ingestion tool."""
    print(f"\n🔧 Testing the actual KnowledgeIngestionTools.query_knowledge_base method")
    
    try:
        from personal_agent.tools.knowledge_ingestion_tools import KnowledgeIngestionTools
        
        tools = KnowledgeIngestionTools()
        
        test_queries = ["Lucy", "Schroeder"]
        
        for query in test_queries:
            print(f"\n--- Testing tool with query: '{query}' ---")
            result = tools.query_knowledge_base(query, mode="hybrid", limit=10)
            print(f"Tool result: {result[:200]}...")
            if len(result) > 200:
                print(f"(truncated, full length: {len(result)} chars)")
                
    except Exception as e:
        print(f"❌ Error testing tool: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🚀 Starting LightRAG Query Debug Session")
    print("=" * 60)
    
    # Test queries that work in web interface
    test_queries = ["Lucy", "Schroeder"]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🎯 TESTING QUERY: '{query}'")
        print(f"{'='*60}")
        
        # Test direct API call
        success, content = test_direct_api_call(query)
        
        if not success:
            print(f"❌ Direct API call failed for '{query}', trying different parameters...")
            test_with_different_params(query)
        else:
            print(f"✅ Direct API call succeeded for '{query}'")
    
    # Test the actual tool
    test_knowledge_tool()
    
    print(f"\n{'='*60}")
    print("🏁 Debug session complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
