#!/usr/bin/env python3
"""
Simple test for LightRAG Memory Server - One request at a time
"""

import requests
import json
import time

def test_health():
    """Test server health"""
    try:
        response = requests.get("http://localhost:9622/health", timeout=10)
        print(f"Health check: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_insert_single_text():
    """Test inserting a single text"""
    payload = {
        "text": "John Smith is my colleague who works in marketing"
    }
    
    try:
        response = requests.post(
            "http://localhost:9622/documents/text",
            json=payload,
            timeout=60
        )
        print(f"Insert response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Insert result: {result}")
            return True
        else:
            print(f"Insert failed: {response.text}")
            return False
    except Exception as e:
        print(f"Insert error: {e}")
        return False

def test_simple_query():
    """Test a simple query"""
    payload = {
        "query": "Who is John Smith?",
        "mode": "naive",
        "top_k": 5
    }
    
    try:
        response = requests.post(
            "http://localhost:9622/query",
            json=payload,
            timeout=60
        )
        print(f"Query response status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Query result: {result}")
            return True
        else:
            print(f"Query failed: {response.text}")
            return False
    except Exception as e:
        print(f"Query error: {e}")
        return False

def main():
    print("🔍 Simple LightRAG Memory Server Test")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health...")
    if not test_health():
        print("❌ Server not healthy, stopping test")
        return
    print("✅ Server is healthy")
    
    # Test 2: Insert text
    print("\n2. Testing text insertion...")
    if test_insert_single_text():
        print("✅ Text inserted successfully")
    else:
        print("❌ Text insertion failed")
        return
    
    # Wait for processing
    print("\n3. Waiting 10 seconds for processing...")
    time.sleep(10)
    
    # Test 3: Query
    print("\n4. Testing query...")
    if test_simple_query():
        print("✅ Query completed")
    else:
        print("❌ Query failed")
    
    print("\n" + "=" * 50)
    print("🎉 Simple test completed!")

if __name__ == "__main__":
    main()
