#!/usr/bin/env python3
"""
Test inserting text with various parameters to find the right way to set file_path
"""

import requests
import json

def test_insert_variations():
    """Test different ways to insert text with file_path"""
    base_url = "http://localhost:9622"
    
    # Test 1: Basic insertion (current method)
    print("Test 1: Basic insertion")
    payload1 = {
        "text": "Test memory 1 - basic insertion"
    }
    
    try:
        response = requests.post(f"{base_url}/documents/text", json=payload1, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "-" * 50 + "\n")
    
    # Test 2: With file_path parameter
    print("Test 2: With file_path parameter")
    payload2 = {
        "text": "Test memory 2 - with file_path",
        "file_path": "memory_text"
    }
    
    try:
        response = requests.post(f"{base_url}/documents/text", json=payload2, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "-" * 50 + "\n")
    
    # Test 3: With description parameter
    print("Test 3: With description parameter")
    payload3 = {
        "text": "Test memory 3 - with description",
        "description": "A test memory with description"
    }
    
    try:
        response = requests.post(f"{base_url}/documents/text", json=payload3, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "-" * 50 + "\n")
    
    # Test 4: With both file_path and description
    print("Test 4: With both file_path and description")
    payload4 = {
        "text": "Test memory 4 - with both parameters",
        "file_path": "memory_text",
        "description": "A test memory with both parameters"
    }
    
    try:
        response = requests.post(f"{base_url}/documents/text", json=payload4, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "-" * 50 + "\n")
    
    # Test 5: With source parameter
    print("Test 5: With source parameter")
    payload5 = {
        "text": "Test memory 5 - with source",
        "source": "memory_text"
    }
    
    try:
        response = requests.post(f"{base_url}/documents/text", json=payload5, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing LightRAG Text Insertion Parameters")
    print("=" * 60)
    test_insert_variations()
    print("\n" + "=" * 60)
    print("🎉 Parameter testing completed!")
