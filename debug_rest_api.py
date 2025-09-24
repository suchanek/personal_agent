#!/usr/bin/env python3
"""
REST API Debug Script
====================

This script helps diagnose issues with the Personal Agent REST API
by checking system status and testing basic connectivity.

Usage:
    python debug_rest_api.py [--host HOST] [--port PORT]
"""

import argparse
import json
import requests
import sys
from datetime import datetime


def check_api_health(base_url):
    """Check API health endpoint."""
    print(f"🔍 Checking API health at {base_url}")
    
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API is {data['status']}")
            print(f"   Service: {data['service']} v{data['version']}")
            return True
        else:
            print(f"   ❌ Health check failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection failed: {str(e)}")
        return False


def check_system_status(base_url):
    """Check system status endpoint."""
    print(f"\n📊 Checking system status at {base_url}")
    
    try:
        response = requests.get(f"{base_url}/api/v1/status", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ System status: {data['status']}")
            print(f"   Streamlit connected: {data['streamlit_connected']}")
            print(f"   Agent available: {data.get('agent_available', False)}")
            print(f"   Team available: {data.get('team_available', False)}")
            print(f"   Memory available: {data.get('memory_available', False)}")
            print(f"   Knowledge available: {data.get('knowledge_available', False)}")
            
            # Check if memory/knowledge systems are available
            if not data.get('memory_available', False):
                print("   ⚠️  Memory system not available - this will cause 503 errors")
            if not data.get('knowledge_available', False):
                print("   ⚠️  Knowledge system not available - this will cause 503 errors")
                
            return data
        else:
            print(f"   ❌ Status check failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection failed: {str(e)}")
        return None


def test_simple_memory_store(base_url):
    """Test a simple memory store operation."""
    print(f"\n💾 Testing memory store at {base_url}")
    
    test_data = {
        "content": "xxxThis is a test memory from the debug script",
        "topics": ["debug", "test"]
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/memory/store",
            json=test_data,
            timeout=30
        )
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"   ✅ Memory stored successfully")
                print(f"   Memory ID: {data.get('memory_id')}")
                print(f"   Topics: {data.get('topics')}")
                return True
            else:
                print(f"   ❌ Memory store failed: {data.get('error')}")
                return False
        else:
            print(f"   ❌ Memory store failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection failed: {str(e)}")
        return False


def main():
    """Main diagnostic function."""
    parser = argparse.ArgumentParser(description="Debug Personal Agent REST API")
    parser.add_argument("--host", default="localhost", help="API host (default: localhost)")
    parser.add_argument("--port", type=int, default=8001, help="API port (default: 8001)")
    
    args = parser.parse_args()
    base_url = f"http://{args.host}:{args.port}"
    
    print("Personal Agent REST API Debug Script")
    print("=" * 50)
    print(f"Target URL: {base_url}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Check API health
    health_ok = check_api_health(base_url)
    
    if not health_ok:
        print("\n❌ API health check failed. Make sure:")
        print("   1. Streamlit app is running")
        print("   2. REST API server started (check for green indicator in UI)")
        print("   3. Port 8001 is not blocked")
        sys.exit(1)
    
    # Step 2: Check system status
    status_data = check_system_status(base_url)
    
    if not status_data:
        print("\n❌ System status check failed")
        sys.exit(1)
    
    # Step 3: Check if systems are available
    memory_available = status_data.get('memory_available', False)
    knowledge_available = status_data.get('knowledge_available', False)
    
    if not memory_available and not knowledge_available:
        print("\n❌ Neither memory nor knowledge systems are available")
        print("   This explains the 503 errors in the test script")
        print("   Wait for agent/team initialization to complete")
        sys.exit(1)
    
    # Step 4: Test memory store if available
    if memory_available:
        memory_ok = test_simple_memory_store(base_url)
        if not memory_ok:
            print("\n⚠️  Memory system reports as available but store operation failed")
    else:
        print("\n⚠️  Memory system not available - skipping memory test")
    
    # Summary
    print("\n" + "=" * 50)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if health_ok and status_data:
        if memory_available or knowledge_available:
            print("✅ API is accessible and at least one system is available")
            if not memory_available:
                print("⚠️  Memory system not available")
            if not knowledge_available:
                print("⚠️  Knowledge system not available")
            print("\nRecommendations:")
            print("1. Wait for full system initialization")
            print("2. Check Streamlit UI for any error messages")
            print("3. Restart Streamlit app if issues persist")
        else:
            print("❌ API is accessible but no systems are available")
            print("\nRecommendations:")
            print("1. Wait for agent/team initialization")
            print("2. Check Streamlit logs for errors")
            print("3. Restart the application")
    else:
        print("❌ API is not accessible")
        print("\nRecommendations:")
        print("1. Start the Streamlit application")
        print("2. Check that REST API server started")
        print("3. Verify port 8001 is available")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
