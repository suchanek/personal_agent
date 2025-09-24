#!/usr/bin/env python3
"""
Personal Agent REST API Usage Examples
=====================================

This script demonstrates practical usage of the Personal Agent REST API
with real-world examples for memory and knowledge storage.

Usage:
    python example_rest_api_usage.py [--host HOST] [--port PORT]

Requirements:
    - Personal Agent Streamlit app must be running
    - REST API server must be accessible (default: http://localhost:8001)

Author: Personal Agent Development Team
Version: v1.0.0
Last Revision: 2025-01-24
"""

import argparse
import json
import requests
import time
from datetime import datetime


class PersonalAgentAPIClient:
    """Simple client for Personal Agent REST API."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def make_request(self, method: str, endpoint: str, **kwargs):
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
            return None
    
    def check_health(self):
        """Check API health status."""
        print("🔍 Checking API health...")
        result = self.make_request("GET", "/api/v1/health")
        if result:
            print(f"✅ API is {result['status']} - Service: {result['service']} v{result['version']}")
            return True
        return False
    
    def get_system_status(self):
        """Get system status information."""
        print("📊 Getting system status...")
        result = self.make_request("GET", "/api/v1/status")
        if result:
            print(f"✅ System status: {result['status']}")
            print(f"   Streamlit connected: {result['streamlit_connected']}")
            print(f"   Agent available: {result.get('agent_available', False)}")
            print(f"   Team available: {result.get('team_available', False)}")
            print(f"   Memory available: {result.get('memory_available', False)}")
            print(f"   Knowledge available: {result.get('knowledge_available', False)}")
            return True
        return False
    
    def store_personal_memory(self, content: str, topics: list = None):
        """Store personal memory with topics."""
        print(f"💾 Storing memory: {content[:50]}...")
        
        data = {"content": content}
        if topics:
            data["topics"] = topics
        
        result = self.make_request("POST", "/api/v1/memory/store", json=data)
        if result and result.get("success"):
            print(f"✅ Memory stored with ID: {result.get('memory_id')}")
            if result.get("topics"):
                print(f"   Topics: {', '.join(result['topics'])}")
            return result.get("memory_id")
        else:
            print(f"❌ Failed to store memory: {result.get('error') if result else 'Unknown error'}")
        return None
    
    def store_memory_from_url(self, url: str, title: str = None, topics: list = None):
        """Store memory from URL content."""
        print(f"🌐 Storing memory from URL: {url}")
        
        data = {"url": url}
        if title:
            data["title"] = title
        if topics:
            data["topics"] = topics
        
        result = self.make_request("POST", "/api/v1/memory/store-url", json=data)
        if result and result.get("success"):
            print(f"✅ Memory from URL stored with ID: {result.get('memory_id')}")
            print(f"   Title: {result.get('extracted_title')}")
            print(f"   Content length: {result.get('content_length')} characters")
            return result.get("memory_id")
        else:
            print(f"❌ Failed to store memory from URL: {result.get('error') if result else 'Unknown error'}")
        return None
    
    def search_memories(self, query: str, limit: int = 5):
        """Search memories by query."""
        print(f"🔍 Searching memories for: '{query}'")
        
        params = {"q": query, "limit": limit}
        result = self.make_request("GET", "/api/v1/memory/search", params=params)
        
        if result and result.get("success"):
            results = result.get("results", [])
            print(f"✅ Found {len(results)} matching memories:")
            
            for i, memory in enumerate(results, 1):
                print(f"   {i}. Score: {memory['similarity_score']:.3f}")
                print(f"      Content: {memory['content'][:100]}...")
                if memory.get('topics'):
                    print(f"      Topics: {', '.join(memory['topics'])}")
                print()
            
            return results
        else:
            print(f"❌ Failed to search memories: {result.get('error') if result else 'Unknown error'}")
        return []
    
    def get_memory_stats(self):
        """Get memory statistics."""
        print("📈 Getting memory statistics...")
        
        result = self.make_request("GET", "/api/v1/memory/stats")
        if result and result.get("success"):
            stats = result.get("stats", {})
            print("✅ Memory Statistics:")
            print(f"   Total memories: {stats.get('total_memories', 0)}")
            print(f"   Recent (24h): {stats.get('recent_memories_24h', 0)}")
            print(f"   Average length: {stats.get('average_memory_length', 0):.1f} characters")
            
            topic_dist = stats.get('topic_distribution', {})
            if topic_dist:
                print("   Topic distribution:")
                for topic, count in sorted(topic_dist.items(), key=lambda x: x[1], reverse=True):
                    print(f"     - {topic}: {count}")
            
            return stats
        else:
            print(f"❌ Failed to get memory stats: {result.get('error') if result else 'Unknown error'}")
        return {}
    
    def store_knowledge_text(self, content: str, title: str, file_type: str = "txt"):
        """Store text content in knowledge base."""
        print(f"📚 Storing knowledge: {title}")
        
        data = {
            "content": content,
            "title": title,
            "file_type": file_type
        }
        
        result = self.make_request("POST", "/api/v1/knowledge/store-text", json=data)
        if result and result.get("success"):
            print(f"✅ Knowledge stored: {title}")
            print(f"   Content length: {result.get('content_length')} characters")
            return True
        else:
            print(f"❌ Failed to store knowledge: {result.get('error') if result else 'Unknown error'}")
        return False
    
    def store_knowledge_from_url(self, url: str, title: str = None):
        """Store knowledge from URL content."""
        print(f"🌐 Storing knowledge from URL: {url}")
        
        data = {"url": url}
        if title:
            data["title"] = title
        
        result = self.make_request("POST", "/api/v1/knowledge/store-url", json=data)
        if result and result.get("success"):
            print(f"✅ Knowledge from URL stored: {result.get('title')}")
            return True
        else:
            print(f"❌ Failed to store knowledge from URL: {result.get('error') if result else 'Unknown error'}")
        return False
    
    def search_knowledge(self, query: str, mode: str = "auto", limit: int = 5):
        """Search knowledge base."""
        print(f"🔍 Searching knowledge for: '{query}'")
        
        params = {"q": query, "mode": mode, "limit": limit}
        result = self.make_request("GET", "/api/v1/knowledge/search", params=params)
        
        if result and result.get("success"):
            search_result = result.get("result", "")
            print(f"✅ Knowledge search result ({len(str(search_result))} characters):")
            print(f"   {str(search_result)[:300]}...")
            return search_result
        else:
            print(f"❌ Failed to search knowledge: {result.get('error') if result else 'Unknown error'}")
        return ""


def run_memory_examples(client):
    """Run memory storage and search examples."""
    print("\n" + "="*60)
    print("MEMORY EXAMPLES")
    print("="*60)
    
    # Store some personal memories
    memories = [
        {
            "content": "I work as a software engineer at TechCorp, specializing in Python and machine learning.",
            "topics": ["work", "career", "technology"]
        },
        {
            "content": "My favorite programming languages are Python, JavaScript, and Go. I enjoy building web applications.",
            "topics": ["programming", "preferences", "technology"]
        },
        {
            "content": "I live in San Francisco and love hiking in the nearby mountains on weekends.",
            "topics": ["personal", "location", "hobbies"]
        },
        {
            "content": "I'm currently learning about large language models and their applications in software development.",
            "topics": ["learning", "ai", "technology"]
        }
    ]
    
    # Store memories
    stored_ids = []
    for memory in memories:
        memory_id = client.store_personal_memory(memory["content"], memory["topics"])
        if memory_id:
            stored_ids.append(memory_id)
        time.sleep(0.5)  # Small delay between requests
    
    print(f"\n📊 Stored {len(stored_ids)} memories")
    
    # Wait for indexing
    time.sleep(2)
    
    # Search for memories
    search_queries = [
        "work and career",
        "programming languages",
        "San Francisco",
        "machine learning"
    ]
    
    for query in search_queries:
        client.search_memories(query, limit=3)
        time.sleep(0.5)
    
    # Get memory statistics
    client.get_memory_stats()
    
    # Try storing memory from URL (example with a reliable URL)
    client.store_memory_from_url(
        "https://httpbin.org/json",
        title="Test JSON Data",
        topics=["testing", "json", "api"]
    )


def run_knowledge_examples(client):
    """Run knowledge storage and search examples."""
    print("\n" + "="*60)
    print("KNOWLEDGE EXAMPLES")
    print("="*60)
    
    # Store some knowledge content
    knowledge_items = [
        {
            "title": "Python Best Practices",
            "content": """
            Python Best Practices for Software Development:
            
            1. Code Style and Formatting:
            - Follow PEP 8 style guidelines
            - Use meaningful variable and function names
            - Keep functions small and focused
            - Use type hints for better code documentation
            
            2. Error Handling:
            - Use specific exception types
            - Implement proper logging
            - Handle exceptions gracefully
            - Use context managers for resource management
            
            3. Testing:
            - Write unit tests for all functions
            - Use pytest for testing framework
            - Aim for high test coverage
            - Test edge cases and error conditions
            
            4. Documentation:
            - Write clear docstrings
            - Use meaningful comments
            - Keep README files updated
            - Document API endpoints
            """,
            "file_type": "md"
        },
        {
            "title": "REST API Design Guidelines",
            "content": """
            REST API Design Best Practices:
            
            1. Resource Naming:
            - Use nouns for resource names
            - Use plural forms for collections
            - Use hierarchical structure for nested resources
            - Keep URLs simple and intuitive
            
            2. HTTP Methods:
            - GET for retrieving data
            - POST for creating new resources
            - PUT for updating entire resources
            - PATCH for partial updates
            - DELETE for removing resources
            
            3. Status Codes:
            - 200 OK for successful GET requests
            - 201 Created for successful POST requests
            - 400 Bad Request for client errors
            - 401 Unauthorized for authentication errors
            - 404 Not Found for missing resources
            - 500 Internal Server Error for server errors
            
            4. Response Format:
            - Use consistent JSON structure
            - Include metadata in responses
            - Provide clear error messages
            - Use pagination for large datasets
            """,
            "file_type": "md"
        }
    ]
    
    # Store knowledge items
    for item in knowledge_items:
        client.store_knowledge_text(
            item["content"],
            item["title"],
            item["file_type"]
        )
        time.sleep(0.5)
    
    # Wait for indexing
    time.sleep(2)
    
    # Search knowledge base
    search_queries = [
        "Python testing best practices",
        "REST API status codes",
        "error handling",
        "documentation guidelines"
    ]
    
    for query in search_queries:
        client.search_knowledge(query, mode="auto", limit=3)
        time.sleep(0.5)
    
    # Try storing knowledge from URL
    client.store_knowledge_from_url(
        "https://httpbin.org/json",
        title="HTTPBin JSON Example"
    )


def main():
    """Main function to run examples."""
    parser = argparse.ArgumentParser(description="Personal Agent REST API Examples")
    parser.add_argument("--host", default="localhost", help="API host (default: localhost)")
    parser.add_argument("--port", type=int, default=8001, help="API port (default: 8001)")
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    
    print("Personal Agent REST API Usage Examples")
    print("=" * 60)
    print(f"API URL: {base_url}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create client
    client = PersonalAgentAPIClient(base_url=base_url)
    
    # Check API health
    if not client.check_health():
        print("❌ API is not accessible. Make sure the Personal Agent Streamlit app is running.")
        return
    
    # Get system status
    if not client.get_system_status():
        print("❌ Could not get system status.")
        return
    
    try:
        # Run memory examples
        run_memory_examples(client)
        
        # Run knowledge examples
        run_knowledge_examples(client)
        
        print("\n" + "="*60)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nYou can now:")
        print("1. Check the Streamlit UI to see the stored memories and knowledge")
        print("2. Use the search functionality in the UI to find the stored content")
        print("3. Explore the API endpoints with your own data")
        print("\nFor more advanced usage, check the test_rest_api.py script.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Examples interrupted by user.")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
