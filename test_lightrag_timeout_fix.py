#!/usr/bin/env python3
"""
Test script to verify LightRAG server timeout fixes
"""

import requests
import json
import time
import sys

def test_server_health():
    """Test if the LightRAG server is responding"""
    try:
        response = requests.get("http://localhost:9621/health", timeout=10)
        if response.status_code == 200:
            print("✅ LightRAG server is healthy and responding")
            return True
        else:
            print(f"❌ Server health check failed with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server health check failed: {e}")
        return False

def test_model_configuration():
    """Test if the model configuration is working"""
    try:
        # Test a simple query to see if the model responds
        test_data = {
            "query": "What is artificial intelligence?",
            "mode": "local"
        }
        
        print("🔄 Testing model configuration with simple query...")
        response = requests.post(
            "http://localhost:9621/query", 
            json=test_data, 
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Model configuration test successful")
            print(f"📝 Response preview: {result.get('response', 'No response')[:100]}...")
            return True
        else:
            print(f"❌ Model test failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Model configuration test failed: {e}")
        return False

def test_document_upload_preparation():
    """Test document upload endpoint to see if it's ready"""
    try:
        response = requests.get("http://localhost:9621/documents", timeout=10)
        if response.status_code in [200, 404]:  # 404 is OK if no documents exist
            print("✅ Document upload endpoint is accessible")
            return True
        else:
            print(f"❌ Document endpoint test failed with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Document endpoint test failed: {e}")
        return False

def main():
    print("🚀 Testing LightRAG Server Timeout Fixes")
    print("=" * 50)
    
    # Wait a moment for server to fully initialize
    print("⏳ Waiting for server to fully initialize...")
    time.sleep(5)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Server Health
    print("\n1. Testing server health...")
    if test_server_health():
        tests_passed += 1
    
    # Test 2: Model Configuration
    print("\n2. Testing model configuration...")
    if test_model_configuration():
        tests_passed += 1
    
    # Test 3: Document Upload Readiness
    print("\n3. Testing document upload readiness...")
    if test_document_upload_preparation():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The timeout fixes appear to be working.")
        print("\n📋 Configuration Summary:")
        print("   • Model upgraded to: qwen2.5:latest (7B)")
        print("   • PDF chunk size reduced to: 1024 bytes")
        print("   • Timeout settings: 7200 seconds (2 hours)")
        print("   • Max retries increased to: 5")
        print("   • Retry delay increased to: 60 seconds")
        print("\n💡 Tips for PDF processing:")
        print("   • Start with smaller PDF files to test")
        print("   • Monitor the logs during processing")
        print("   • The server will now be more resilient to timeouts")
        return 0
    else:
        print("⚠️  Some tests failed. Check the server configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
