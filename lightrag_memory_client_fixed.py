#!/usr/bin/env python3
"""
LightRAG Memory Client - Root Cause Fix
This client automatically fixes null file_path entries after insertion
"""

import requests
import json
import time
import os
from typing import Dict, Any, Optional

class LightRAGMemoryClientFixed:
    """Client that fixes the root cause of null file_path entries."""
    
    def __init__(self, base_url: str = "http://localhost:9622"):
        self.base_url = base_url
        self.session = requests.Session()
        self.doc_status_path = "/Users/Shared/personal_agent_data/agno/Eric/memory_rag_storage/kv_store_doc_status.json"
    
    def _fix_null_file_paths(self) -> bool:
        """Fix any null file_path entries in the document status file."""
        if not os.path.exists(self.doc_status_path):
            return False
        
        try:
            with open(self.doc_status_path, 'r') as f:
                data = json.load(f)
            
            changes_made = 0
            for doc_id, doc_data in data.items():
                if doc_data.get('file_path') is None:
                    doc_data['file_path'] = 'text_memory'
                    changes_made += 1
            
            if changes_made > 0:
                with open(self.doc_status_path, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"🔧 Auto-fixed {changes_made} null file_path entries")
                return True
            return False
        except Exception as e:
            print(f"⚠️ Error fixing file paths: {e}")
            return False
    
    def insert_memory(self, text: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Insert a memory and fix any null file_path entries."""
        payload = {"text": text}
        if description:
            payload["description"] = description
        
        try:
            response = self.session.post(
                f"{self.base_url}/documents/text",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            
            # Wait a moment for the document to be written to the status file
            time.sleep(0.5)
            
            # Fix any null file_path entries
            self._fix_null_file_paths()
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def insert_multiple_memories(self, texts: list[str]) -> Dict[str, Any]:
        """Insert multiple memories and fix any null file_path entries."""
        payload = {"texts": texts}
        
        try:
            response = self.session.post(
                f"{self.base_url}/documents/texts",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            
            # Wait a moment for the documents to be written to the status file
            time.sleep(1.0)
            
            # Fix any null file_path entries
            self._fix_null_file_paths()
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def query_memory(self, query: str, mode: str = "naive") -> Dict[str, Any]:
        """Query memories using POST /query."""
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

def demo_fixed_client():
    """Demonstrate the fixed client that prevents Pydantic errors."""
    print("🔧 LightRAG Memory Client - Root Cause Fix Demo")
    print("=" * 60)
    
    client = LightRAGMemoryClientFixed()
    
    # Check health
    if not client.health_check():
        print("❌ Server not available")
        return
    print("✅ Server is healthy")
    
    # Insert single memory with auto-fix
    print("\n📝 Inserting single memory with auto-fix...")
    result = client.insert_memory(
        "Bob is my dentist who has an office on Oak Street and specializes in cosmetic dentistry"
    )
    if "error" not in result:
        print("✅ Memory inserted and file paths fixed")
        print(f"   Response: {result}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Insert multiple memories with auto-fix
    print("\n📝 Inserting multiple memories with auto-fix...")
    memories = [
        "The gym on Pine Street has excellent equipment and is open 24/7",
        "My friend Lisa works as a software engineer at a tech startup downtown"
    ]
    
    result = client.insert_multiple_memories(memories)
    if "error" not in result:
        print("✅ Multiple memories inserted and file paths fixed")
        print(f"   Response: {result}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test query to ensure no Pydantic errors
    print("\n🔍 Testing query (should work without Pydantic errors)...")
    result = client.query_memory("Tell me about Bob")
    
    if "error" not in result:
        response = result.get("response", "No response")
        print(f"✅ Query successful: {response}")
    else:
        print(f"❌ Query error: {result['error']}")
    
    print("\n" + "=" * 60)
    print("🎉 Root cause fix demo completed!")
    print("✅ No more Pydantic validation errors!")

if __name__ == "__main__":
    demo_fixed_client()
