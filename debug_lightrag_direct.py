#!/usr/bin/env python3
"""
Debug script to test LightRAG knowledge base directly.
This script sends a query directly to the LightRAG server and shows the raw response.
"""

import asyncio
import json
import aiohttp
import sys
from datetime import datetime


async def test_lightrag_direct(query: str = "proteusPy", base_url: str = "http://localhost:9621"):
    """Test LightRAG knowledge base directly."""
    
    print(f"🔍 Testing LightRAG Knowledge Base")
    print(f"📍 Server: {base_url}")
    print(f"❓ Query: '{query}'")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test 1: Check if server is running
    print("\n1️⃣ Testing server connectivity...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/health", timeout=10) as resp:
                if resp.status == 200:
                    print("✅ Server is running")
                else:
                    print(f"⚠️ Server responded with status {resp.status}")
    except Exception as e:
        print(f"❌ Server connection failed: {e}")
        return
    
    # Test 2: Check documents
    print("\n2️⃣ Checking available documents...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/documents", timeout=30) as resp:
                if resp.status == 200:
                    docs_result = await resp.json()
                    print(f"📄 Documents response type: {type(docs_result)}")
                    
                    if isinstance(docs_result, dict) and "statuses" in docs_result:
                        processed_docs = docs_result["statuses"].get("processed", [])
                        print(f"📚 Found {len(processed_docs)} processed documents:")
                        for i, doc in enumerate(processed_docs[:3], 1):  # Show first 3
                            print(f"   {i}. {doc.get('file_path', 'Unknown')} ({doc.get('chunks_count', 0)} chunks)")
                        if len(processed_docs) > 3:
                            print(f"   ... and {len(processed_docs) - 3} more documents")
                    else:
                        print(f"📄 Raw documents response: {json.dumps(docs_result, indent=2)[:500]}...")
                else:
                    print(f"❌ Documents check failed with status {resp.status}")
    except Exception as e:
        print(f"❌ Documents check failed: {e}")
    
    # Test 3: Test different query modes
    modes = ["hybrid", "naive", "local", "global"]
    
    for mode in modes:
        print(f"\n3️⃣ Testing query with mode: '{mode}'")
        print("-" * 40)
        
        try:
            url = f"{base_url}/query"
            payload = {"query": query, "mode": mode}
            
            print(f"🔗 URL: {url}")
            print(f"📦 Payload: {json.dumps(payload, indent=2)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=120) as resp:
                    print(f"📊 Response status: {resp.status}")
                    print(f"📋 Response headers: {dict(resp.headers)}")
                    
                    if resp.status == 200:
                        result = await resp.json()
                        print(f"📄 Response type: {type(result)}")
                        print(f"📄 Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                        
                        # Extract response content
                        if isinstance(result, dict) and "response" in result:
                            response_content = result["response"]
                            print(f"📝 Response content length: {len(response_content)} characters")
                            print(f"📝 Response preview (first 200 chars):")
                            print(f"   {response_content[:200]}...")
                            
                            # Check for think tags
                            if "<think>" in response_content:
                                print("🧠 Contains <think> tags - AI reasoning detected")
                                if "</think>" in response_content:
                                    parts = response_content.split("</think>", 1)
                                    if len(parts) > 1:
                                        after_think = parts[1].strip()
                                        print(f"📝 Content after </think> ({len(after_think)} chars):")
                                        print(f"   {after_think[:200]}...")
                            else:
                                print("📝 No <think> tags found")
                            
                            # Check for specific content
                            if "proteusPy" in response_content:
                                print("✅ Contains 'proteusPy'")
                            if "Eric G. Suchanek" in response_content:
                                print("✅ Contains 'Eric G. Suchanek'")
                            if "DisulfideLoader" in response_content:
                                print("✅ Contains 'DisulfideLoader'")
                            if "[KG]" in response_content or "[DC]" in response_content:
                                print("✅ Contains document references")
                            
                        else:
                            print(f"❌ No 'response' field found")
                            print(f"📄 Full result: {json.dumps(result, indent=2)[:500]}...")
                    else:
                        error_text = await resp.text()
                        print(f"❌ Query failed with status {resp.status}")
                        print(f"📄 Error response: {error_text[:500]}...")
                        
        except Exception as e:
            print(f"❌ Query failed for mode '{mode}': {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Debug test completed!")


async def main():
    """Main function."""
    query = "proteusPy"
    base_url = "http://localhost:9621"
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        query = sys.argv[1]
    if len(sys.argv) > 2:
        base_url = sys.argv[2]
    
    await test_lightrag_direct(query, base_url)


if __name__ == "__main__":
    asyncio.run(main())
