#!/usr/bin/env python3
"""
LightRAG Memory Client - File Upload Approach
This client creates temporary files and uploads them to avoid null file_path issues
"""

import requests
import json
import tempfile
import os
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path

class LightRAGMemoryClientFileUpload:
    """Client that uses file uploads instead of text insertion to avoid null file_path issues."""
    
    def __init__(self, base_url: str = "http://localhost:9622"):
        self.base_url = base_url
        self.session = requests.Session()
        self.temp_dir = "/tmp/lightrag_memories"
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def _create_memory_file(self, text: str, description: Optional[str] = None) -> str:
        """Create a temporary file for the memory text."""
        # Create a meaningful filename based on content
        content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        # Extract first few words for filename
        words = text.split()[:3]
        filename_base = "_".join(word.lower().replace(" ", "") for word in words if word.isalnum())
        filename = f"memory_{filename_base}_{content_hash}.txt"
        
        filepath = os.path.join(self.temp_dir, filename)
        
        # Write the memory content to file
        with open(filepath, 'w', encoding='utf-8') as f:
            if description:
                f.write(f"# {description}\n\n")
            f.write(text)
        
        return filepath
    
    def _upload_file(self, filepath: str) -> Dict[str, Any]:
        """Upload a file to the LightRAG server."""
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (os.path.basename(filepath), f, 'text/plain')}
                response = self.session.post(
                    f"{self.base_url}/documents/upload",
                    files=files,
                    timeout=60
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            return {"error": str(e)}
        finally:
            # Clean up the temporary file
            try:
                os.remove(filepath)
            except:
                pass
    
    def insert_memory(self, text: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Insert a memory by creating a temporary file and uploading it."""
        try:
            # Create temporary file
            filepath = self._create_memory_file(text, description)
            print(f"📄 Created temporary file: {os.path.basename(filepath)}")
            
            # Upload the file
            result = self._upload_file(filepath)
            
            if "error" not in result:
                print(f"✅ Memory uploaded successfully as file")
            
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def insert_multiple_memories(self, texts: list[str]) -> Dict[str, Any]:
        """Insert multiple memories by creating and uploading individual files."""
        results = []
        errors = []
        
        for i, text in enumerate(texts, 1):
            print(f"📝 Processing memory {i}/{len(texts)}...")
            result = self.insert_memory(text)
            
            if "error" in result:
                errors.append(f"Memory {i}: {result['error']}")
            else:
                results.append(result)
        
        if errors:
            return {"error": f"Some uploads failed: {'; '.join(errors)}", "successful": len(results)}
        else:
            return {"status": "success", "message": f"Successfully uploaded {len(results)} memory files"}
    
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

def demo_file_upload_client():
    """Demonstrate the file upload approach that avoids null file_path issues."""
    print("📁 LightRAG Memory Client - File Upload Approach Demo")
    print("=" * 65)
    
    client = LightRAGMemoryClientFileUpload()
    
    # Check health
    if not client.health_check():
        print("❌ Server not available")
        return
    print("✅ Server is healthy")
    
    # Insert single memory via file upload
    print("\n📝 Inserting single memory via file upload...")
    result = client.insert_memory(
        "Emma is my yoga instructor who teaches classes at the wellness center on Maple Avenue",
        "Personal contact - yoga instructor"
    )
    if "error" not in result:
        print("✅ Memory uploaded successfully")
        print(f"   Response: {result}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Insert multiple memories via file uploads
    print("\n📝 Inserting multiple memories via file uploads...")
    memories = [
        "The bookstore on First Street has a great selection of science fiction novels",
        "My mechanic Tony runs an auto shop near the highway and is very reliable"
    ]
    
    result = client.insert_multiple_memories(memories)
    if "error" not in result:
        print("✅ Multiple memories uploaded successfully")
        print(f"   Response: {result}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test query to ensure no Pydantic errors
    print("\n🔍 Testing query (should work without Pydantic errors)...")
    result = client.query_memory("Tell me about Emma")
    
    if "error" not in result:
        response = result.get("response", "No response")
        print(f"✅ Query successful: {response}")
    else:
        print(f"❌ Query error: {result['error']}")
    
    print("\n" + "=" * 65)
    print("🎉 File upload approach demo completed!")
    print("✅ Using proper file uploads with valid file paths!")

if __name__ == "__main__":
    demo_file_upload_client()
