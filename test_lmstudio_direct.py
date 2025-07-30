#!/usr/bin/env python3
"""
Direct LMStudio API Test Script

This script tests the LMStudio server directly using the same configuration
as the AgentModelManager, helping to diagnose the 'developer' role issue.
"""

import json
import requests
import sys
from typing import Dict, Any, Optional

# Import configuration
try:
    from test_config import LMSTUDIO_BASE_URL, MODEL_NAME, JSON_SCHEMA, TEST_QUERIES
except ImportError:
    # Fallback configuration if test_config.py is not available
    LMSTUDIO_BASE_URL = "http://localhost:1234"
    MODEL_NAME = "your-model-name"
    JSON_SCHEMA = {
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "reasoning": {"type": "string"}
        },
        "required": ["content"],
        "additionalProperties": True
    }
    TEST_QUERIES = [
        "What is the capital of France?",
        "Explain the concept of machine learning in simple terms.",
        "Write a short poem about artificial intelligence.",
        "What are the main differences between Python and JavaScript?"
    ]

LMSTUDIO_ENDPOINT = f"{LMSTUDIO_BASE_URL}/v1/chat/completions"

def create_request_payload(messages: list, use_structured_output: bool = True) -> Dict[str, Any]:
    """Create the request payload for LMStudio API."""
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }
    
    if use_structured_output:
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "structured_response",
                "schema": JSON_SCHEMA
            }
        }
    
    return payload

def send_query(query: str, use_structured_output: bool = True) -> Optional[Dict[str, Any]]:
    """Send a query to LMStudio and return the response."""
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant. Respond with clear, accurate information."},
        {"role": "user", "content": query}
    ]
    
    payload = create_request_payload(messages, use_structured_output)
    
    print(f"\n🔄 Sending query: {query}")
    print(f"📤 Request payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(
            LMSTUDIO_ENDPOINT,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer lm-studio"  # LMStudio doesn't require real auth
            },
            timeout=30
        )
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ Raw response:")
            print(json.dumps(response_data, indent=2))
            
            # Extract the actual content
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0]["message"]["content"]
                print(f"\n📝 Content: {content}")
                
                # Try to parse as JSON if structured output was requested
                if use_structured_output:
                    try:
                        parsed_content = json.loads(content)
                        print(f"🎯 Parsed structured response:")
                        print(json.dumps(parsed_content, indent=2))
                        return parsed_content
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Failed to parse JSON response: {e}")
                        return {"content": content, "parsing_error": str(e)}
                else:
                    return {"content": content}
            else:
                print("❌ No choices in response")
                return None
                
        else:
            print(f"❌ Error response:")
            print(response.text)
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_role_validation():
    """Test different message roles to identify the 'developer' role issue."""
    print("\n" + "="*60)
    print("🧪 TESTING MESSAGE ROLES")
    print("="*60)
    
    # Test valid roles
    valid_roles = ["system", "user", "assistant"]
    
    for role in valid_roles:
        print(f"\n🔍 Testing role: {role}")
        messages = [
            {"role": role, "content": "What is 2+2?"}
        ]
        
        payload = create_request_payload(messages, use_structured_output=False)
        
        try:
            response = requests.post(
                LMSTUDIO_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Role '{role}' accepted")
            else:
                print(f"❌ Role '{role}' rejected: {response.status_code}")
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing role '{role}': {e}")
    
    # Test invalid role (like 'developer')
    print(f"\n🔍 Testing invalid role: developer")
    messages = [
        {"role": "developer", "content": "What is 2+2?"}
    ]
    
    payload = create_request_payload(messages, use_structured_output=False)
    
    try:
        response = requests.post(
            LMSTUDIO_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Role 'developer' unexpectedly accepted")
        else:
            print(f"❌ Role 'developer' rejected (expected): {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing role 'developer': {e}")

def main():
    """Main test function."""
    print("🚀 LMStudio Direct API Test")
    print("="*60)
    
    # Test server connectivity
    try:
        response = requests.get(f"{LMSTUDIO_BASE_URL}/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ LMStudio server is running")
            print(f"📋 Available models: {[m.get('id', 'unknown') for m in models.get('data', [])]}")
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to LMStudio server: {e}")
        print(f"Make sure LMStudio is running on {LMSTUDIO_BASE_URL}")
        return

    print("\n" + "="*60)
    print("🧪 TESTING STRUCTURED OUTPUT")
    print("="*60)
    
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n--- Test {i}/{len(TEST_QUERIES)} ---")
        result = send_query(query, use_structured_output=True)
        
        if result:
            print("✅ Query successful")
        else:
            print("❌ Query failed")
    
    print("\n" + "="*60)
    print("🧪 TESTING REGULAR OUTPUT")
    print("="*60)
    
    # Test one query without structured output
    result = send_query("What is 2+2?", use_structured_output=False)
    if result:
        print("✅ Regular query successful")
    else:
        print("❌ Regular query failed")
    
    # Test role validation
    test_role_validation()
    
    print("\n" + "="*60)
    print("✅ Test completed!")
    print("="*60)

if __name__ == "__main__":
    main()
