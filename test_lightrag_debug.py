#!/usr/bin/env python3
"""
Debug test for LightRAG Memory Server - Check processing status
"""

import requests
import json
import time

def test_ollama_connection():
    """Test if Ollama is accessible from the container"""
    try:
        # Test the Ollama endpoint that the container should be using
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        print(f"Ollama connection: {response.status_code}")
        if response.status_code == 200:
            models = response.json()
            print(f"Available models: {[model['name'] for model in models.get('models', [])]}")
            return True
        return False
    except Exception as e:
        print(f"Ollama connection failed: {e}")
        return False

def test_pipeline_status():
    """Check the processing pipeline status"""
    try:
        response = requests.get("http://localhost:9622/documents/pipeline_status", timeout=10)
        print(f"Pipeline status response: {response.status_code}")
        if response.status_code == 200:
            status = response.json()
            print(f"Pipeline status: {json.dumps(status, indent=2)}")
            return status
        else:
            print(f"Pipeline status failed: {response.text}")
            return None
    except Exception as e:
        print(f"Pipeline status error: {e}")
        return None

def test_clear_cache():
    """Clear the cache to ensure fresh processing"""
    try:
        response = requests.post("http://localhost:9622/documents/clear_cache", timeout=30)
        print(f"Clear cache response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Cache cleared: {result}")
            return True
        else:
            print(f"Clear cache failed: {response.text}")
            return False
    except Exception as e:
        print(f"Clear cache error: {e}")
        return False

def insert_and_wait_for_processing():
    """Insert text and monitor processing"""
    payload = {
        "text": "Alice is my project manager who schedules team meetings every Tuesday"
    }
    
    try:
        # Insert text
        response = requests.post(
            "http://localhost:9622/documents/text",
            json=payload,
            timeout=60
        )
        print(f"Insert response: {response.status_code}")
        if response.status_code != 200:
            print(f"Insert failed: {response.text}")
            return False
        
        result = response.json()
        print(f"Insert result: {result}")
        
        # Monitor processing for up to 2 minutes
        for i in range(12):  # 12 * 10 seconds = 2 minutes
            print(f"Checking processing status (attempt {i+1}/12)...")
            status = test_pipeline_status()
            
            if status and status.get('processing_complete', False):
                print("✅ Processing completed!")
                return True
            
            time.sleep(10)
        
        print("⚠️ Processing did not complete within 2 minutes")
        return False
        
    except Exception as e:
        print(f"Insert and wait error: {e}")
        return False

def test_query_with_different_modes():
    """Test queries with different modes"""
    query = "Who is Alice?"
    modes = ["naive", "local", "global", "hybrid"]
    
    for mode in modes:
        print(f"\nTesting query with mode: {mode}")
        payload = {
            "query": query,
            "mode": mode,
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
                response_text = result.get("response", "No response")
                print(f"Response: {response_text[:100]}...")
                
                if "[no-context]" not in response_text:
                    print(f"✅ Success with mode: {mode}")
                    return True
            else:
                print(f"Query failed: {response.text}")
        except Exception as e:
            print(f"Query error with mode {mode}: {e}")
    
    return False

def main():
    print("🔧 LightRAG Memory Server Debug Test")
    print("=" * 60)
    
    # Test 1: Ollama connection
    print("\n1. Testing Ollama connection...")
    if test_ollama_connection():
        print("✅ Ollama is accessible")
    else:
        print("❌ Ollama connection issues - this might be the problem!")
    
    # Test 2: Clear cache
    print("\n2. Clearing cache...")
    if test_clear_cache():
        print("✅ Cache cleared")
    else:
        print("⚠️ Cache clear failed")
    
    # Test 3: Pipeline status
    print("\n3. Checking initial pipeline status...")
    test_pipeline_status()
    
    # Test 4: Insert and monitor processing
    print("\n4. Inserting text and monitoring processing...")
    if insert_and_wait_for_processing():
        print("✅ Text processed successfully")
    else:
        print("❌ Text processing failed or incomplete")
    
    # Test 5: Try different query modes
    print("\n5. Testing queries with different modes...")
    if test_query_with_different_modes():
        print("✅ Found working query mode")
    else:
        print("❌ All query modes failed")
    
    print("\n" + "=" * 60)
    print("🎉 Debug test completed!")

if __name__ == "__main__":
    main()
