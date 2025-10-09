#!/usr/bin/env python3
"""
Test script for the PAGA restart endpoint.

This script tests the /api/v1/paga/restart endpoint that re-initializes
the agent/team in the paga_streamlit_agno application.
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8001"
RESTART_ENDPOINT = f"{API_BASE_URL}/api/v1/paga/restart"

def test_paga_restart(restart_lightrag=True):
    """Test the PAGA restart endpoint."""
    print("=" * 60)
    print("Testing PAGA Restart Endpoint")
    print("=" * 60)
    
    # Prepare request data
    data = {
        "restart_lightrag": restart_lightrag
    }
    
    print(f"\n📡 Sending POST request to: {RESTART_ENDPOINT}")
    print(f"📦 Request data: {json.dumps(data, indent=2)}")
    
    try:
        # Send restart request
        response = requests.post(
            RESTART_ENDPOINT,
            json=data,
            timeout=60  # Longer timeout for restart operations
        )
        
        print(f"\n✅ Response Status Code: {response.status_code}")
        
        # Parse response
        try:
            result = response.json()
            print(f"\n📄 Response Body:")
            print(json.dumps(result, indent=2))
            
            # Check if restart was successful
            if result.get("success") == "True":
                print("\n✅ PAGA system restarted successfully!")
                print(f"   Mode: {result.get('mode', 'unknown')}")
                print(f"   Model: {result.get('model', 'unknown')}")
                print(f"   Message: {result.get('message', 'N/A')}")
                
                # Check LightRAG restart results
                if "lightrag_restart" in result:
                    lr_result = result["lightrag_restart"]
                    print(f"\n🔄 LightRAG Restart:")
                    print(f"   Performed: {lr_result.get('performed', False)}")
                    print(f"   Success: {lr_result.get('success', False)}")
                    if lr_result.get('services_restarted'):
                        print(f"   Services Restarted: {', '.join(lr_result['services_restarted'])}")
                    if lr_result.get('errors'):
                        print(f"   Errors: {lr_result['errors']}")
                
                return True
            else:
                print(f"\n❌ PAGA restart failed: {result.get('error', 'Unknown error')}")
                return False
                
        except json.JSONDecodeError:
            print(f"\n❌ Failed to parse JSON response")
            print(f"Raw response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error: Could not connect to {API_BASE_URL}")
        print("   Make sure the PAGA Streamlit app is running on port 8001")
        return False
    except requests.exceptions.Timeout:
        print(f"\n❌ Request Timeout: The restart operation took too long")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")
        return False

def main():
    """Main test function."""
    print("\n🧪 PAGA Restart Endpoint Test")
    print("=" * 60)
    
    # Test 1: Restart with LightRAG
    print("\n\n📋 Test 1: Restart with LightRAG services")
    print("-" * 60)
    success1 = test_paga_restart(restart_lightrag=True)
    
    if success1:
        print("\n⏳ Waiting 5 seconds before next test...")
        time.sleep(5)
    
    # Test 2: Restart without LightRAG
    print("\n\n📋 Test 2: Restart without LightRAG services")
    print("-" * 60)
    success2 = test_paga_restart(restart_lightrag=False)
    
    # Summary
    print("\n\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Test 1 (with LightRAG): {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Test 2 (without LightRAG): {'✅ PASSED' if success2 else '❌ FAILED'}")
    print("=" * 60)
    
    return success1 and success2

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
