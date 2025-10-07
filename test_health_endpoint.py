#!/usr/bin/env python3
"""
Test script to verify the health endpoint is working properly.
"""

import requests
import json
import sys
import time

def test_health_endpoint(host="localhost", port=8001):
    """Test the health endpoint on the REST API."""
    url = f"http://{host}:{port}/api/v1/health"
    
    print(f"Testing health endpoint: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working!")
            print(f"Status: {data.get('status', 'unknown')}")
            print(f"Service: {data.get('service', 'unknown')}")
            print(f"User: {data.get('user', 'unknown')}")
            print(f"Model: {data.get('model', 'unknown')}")
            print(f"Timestamp: {data.get('timestamp', 'unknown')}")
            
            if 'checks' in data:
                print("\nSystem Checks:")
                for check, status in data['checks'].items():
                    status_icon = "✅" if status else "❌"
                    print(f"  {status_icon} {check}: {status}")
                    
            return True
            
        elif response.status_code == 503:
            data = response.json()
            print("❌ Health endpoint returned unhealthy status:")
            print(f"Error: {data.get('error', 'unknown')}")
            return False
            
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused - is the REST API server running?")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
        
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False

def test_discovery_endpoint(host="localhost", port=8001):
    """Test the discovery endpoint to find the actual API port."""
    url = f"http://{host}:{port}/api/v1/discovery"
    
    print(f"Testing discovery endpoint: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Discovery endpoint working!")
            actual_port = data.get('port', port)
            print(f"Actual API port: {actual_port}")
            return actual_port
        else:
            print(f"❌ Discovery endpoint failed: {response.status_code}")
            return port
            
    except Exception as e:
        print(f"❌ Discovery endpoint error: {e}")
        return port

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the Personal Agent REST API health endpoint")
    parser.add_argument("--host", default="localhost", help="API host")
    parser.add_argument("--port", type=int, default=8001, help="API port")
    parser.add_argument("--discover", action="store_true", help="Use discovery to find actual port")
    
    args = parser.parse_args()
    
    port = args.port
    
    if args.discover:
        print("🔍 Discovering actual API port...")
        port = test_discovery_endpoint(args.host, args.port)
        print()
    
    success = test_health_endpoint(args.host, port)
    
    sys.exit(0 if success else 1)
