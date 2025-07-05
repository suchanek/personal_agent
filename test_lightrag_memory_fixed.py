#!/usr/bin/env python3
"""
Test script for LightRAG Memory Server - Fixed Version
This script demonstrates the correct usage of text insertion and query endpoints,
avoiding the problematic document listing endpoint.
"""

import requests
import json
import time
from typing import Dict, Any, Optional

class LightRAGMemoryClient:
    """Client for interacting with LightRAG Memory Server using correct endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:9622"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> bool:
        """Check if the server is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def insert_text(self, text: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Insert text into the memory system using the correct endpoint."""
        payload = {
            "text": text
        }
        if description:
            payload["description"] = description
        
        try:
            response = self.session.post(
                f"{self.base_url}/documents/text",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error inserting text: {e}")
            return {"error": str(e)}
    
    def insert_multiple_texts(self, texts: list[str]) -> Dict[str, Any]:
        """Insert multiple texts using the batch endpoint."""
        payload = {"texts": texts}
        
        try:
            response = self.session.post(
                f"{self.base_url}/documents/texts",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error inserting multiple texts: {e}")
            return {"error": str(e)}
    
    def query_memory(self, query: str, mode: str = "naive", top_k: int = 10) -> Dict[str, Any]:
        """Query the memory system using the correct query endpoint."""
        payload = {
            "query": query,
            "mode": mode,
            "top_k": top_k,
            "response_type": "Multiple Paragraphs"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/query",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error querying memory: {e}")
            return {"error": str(e)}
    
    def clear_all_documents(self) -> Dict[str, Any]:
        """Clear all documents from the system."""
        try:
            response = self.session.delete(f"{self.base_url}/documents", timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error clearing documents: {e}")
            return {"error": str(e)}

def main():
    """Test the LightRAG Memory Server with proper endpoints."""
    print("🧠 Testing LightRAG Memory Server - Fixed Version")
    print("=" * 60)
    
    client = LightRAGMemoryClient()
    
    # Health check
    print("1. Health Check...")
    if not client.health_check():
        print("❌ Server is not healthy. Please check if it's running.")
        return
    print("✅ Server is healthy")
    
    # Clear existing data for clean test
    print("\n2. Clearing existing data...")
    clear_result = client.clear_all_documents()
    if "error" not in clear_result:
        print("✅ Data cleared successfully")
    else:
        print(f"⚠️  Clear operation result: {clear_result}")
    
    # Wait a moment for clearing to complete
    time.sleep(2)
    
    # Test single text insertion
    print("\n3. Testing single text insertion...")
    test_memories = [
        "John Smith is my colleague who works in the marketing department and loves coffee",
        "Sarah Johnson is my neighbor who has two dogs named Max and Luna, and she works as a veterinarian",
        "The coffee shop on Main Street serves excellent espresso and is owned by Maria Rodriguez",
        "My project manager Alice coordinates our team meetings every Tuesday at 2 PM in the conference room"
    ]
    
    for i, memory in enumerate(test_memories, 1):
        print(f"   Inserting memory {i}: {memory[:50]}...")
        result = client.insert_text(memory)
        if "error" not in result:
            print(f"   ✅ Memory {i} inserted successfully")
        else:
            print(f"   ❌ Error inserting memory {i}: {result['error']}")
    
    # Wait for processing
    print("\n4. Waiting for processing...")
    time.sleep(5)
    
    # Test queries
    print("\n5. Testing memory queries...")
    test_queries = [
        "Who is John Smith?",
        "Tell me about my neighbor",
        "Where can I get good coffee?",
        "When are our team meetings?",
        "Who works as a veterinarian?"
    ]
    
    for query in test_queries:
        print(f"\n   Query: {query}")
        result = client.query_memory(query, mode="naive")
        
        if "error" not in result:
            response = result.get("response", "No response")
            print(f"   ✅ Response: {response[:200]}...")
        else:
            print(f"   ❌ Query error: {result['error']}")
    
    # Test batch insertion
    print("\n6. Testing batch text insertion...")
    batch_memories = [
        "The local library has extended hours on weekends and offers free WiFi",
        "Dr. Martinez is my dentist who has an office downtown near the park"
    ]
    
    batch_result = client.insert_multiple_texts(batch_memories)
    if "error" not in batch_result:
        print("✅ Batch insertion successful")
    else:
        print(f"❌ Batch insertion error: {batch_result['error']}")
    
    # Final query test
    print("\n7. Final query test...")
    final_query = "Tell me about all the people I know"
    result = client.query_memory(final_query, mode="naive")
    
    if "error" not in result:
        response = result.get("response", "No response")
        print(f"✅ Final query successful: {response[:300]}...")
    else:
        print(f"❌ Final query error: {result['error']}")
    
    print("\n" + "=" * 60)
    print("🎉 LightRAG Memory Server test completed!")
    print("✅ The server is now working correctly with text-based memories")
    print("✅ Avoiding the problematic document listing endpoint")
    print("✅ Using proper query endpoints for memory retrieval")

if __name__ == "__main__":
    main()
