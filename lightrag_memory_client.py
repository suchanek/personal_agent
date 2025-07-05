#!/usr/bin/env python3
"""
LightRAG Memory Client - Correct Implementation
Uses POST /documents/text for inserting memories and POST /query for retrieval
"""

import requests
import json
from typing import Dict, Any, Optional

class LightRAGMemoryClient:
    """Client for LightRAG Memory Server using correct API endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:9622"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def insert_memory(self, text: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Insert a memory using POST /documents/text
        
        Args:
            text: The memory text to insert
            description: Optional description for the memory
            
        Returns:
            Response from the server
        """
        payload = {
            "text": text,
            "file_path": "text_memory"  # Always include file_path to prevent null values
        }
        if description:
            payload["description"] = description
        
        try:
            response = self.session.post(
                f"{self.base_url}/documents/text",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def insert_multiple_memories(self, texts: list[str]) -> Dict[str, Any]:
        """
        Insert multiple memories using POST /documents/texts
        
        Args:
            texts: List of memory texts to insert
            
        Returns:
            Response from the server
        """
        payload = {
            "texts": texts,
            "file_path": "text_memory"  # Always include file_path to prevent null values
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/documents/texts",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def query_memory(self, query: str, mode: str = "naive") -> Dict[str, Any]:
        """
        Query memories using POST /query
        
        Args:
            query: The question to ask
            mode: Query mode (naive, local, global, hybrid, mix, bypass)
            
        Returns:
            Response from the server
        """
        payload = {
            "query": query,
            "mode": mode,
            "response_type": "Multiple Paragraphs"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/query",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def health_check(self) -> bool:
        """Check if the server is healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except:
            return False

def demo_usage():
    """Demonstrate correct usage of the LightRAG Memory Client."""
    print("🧠 LightRAG Memory Client Demo")
    print("=" * 50)
    
    client = LightRAGMemoryClient()
    
    # Check health
    if not client.health_check():
        print("❌ Server not available")
        return
    print("✅ Server is healthy")
    
    # Insert single memory
    print("\n📝 Inserting single memory...")
    result = client.insert_memory(
        "Alice is my project manager who schedules our team meetings every Tuesday at 2 PM"
    )
    if "error" not in result:
        print("✅ Memory inserted successfully")
        print(f"   Response: {result}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Insert multiple memories
    print("\n📝 Inserting multiple memories...")
    memories = [
        "John works in marketing and loves coffee",
        "Sarah is my neighbor who has two dogs named Max and Luna",
        "The coffee shop on Main Street has excellent espresso"
    ]
    
    result = client.insert_multiple_memories(memories)
    if "error" not in result:
        print("✅ Multiple memories inserted successfully")
        print(f"   Response: {result}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Query memories
    print("\n🔍 Querying memories...")
    queries = [
        "Who is Alice?",
        "Tell me about my neighbor",
        "Where can I get good coffee?"
    ]
    
    for query in queries:
        print(f"\n   Query: {query}")
        result = client.query_memory(query)
        
        if "error" not in result:
            response = result.get("response", "No response")
            print(f"   Response: {response}")
        else:
            print(f"   Error: {result['error']}")
    
    print("\n" + "=" * 50)
    print("✅ Demo completed!")

if __name__ == "__main__":
    demo_usage()
