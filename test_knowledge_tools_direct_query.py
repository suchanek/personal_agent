#!/usr/bin/env python3
"""
Test script to verify the new query_lightrag_knowledge_direct functionality in KnowledgeTools.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.personal_agent.core.agent_knowledge_manager import AgentKnowledgeManager
from src.personal_agent.tools.knowledge_tools import KnowledgeTools
from src.personal_agent.config.settings import (
    LIGHTRAG_URL,
    LIGHTRAG_MEMORY_URL,
    AGNO_STORAGE_DIR,
    USER_ID,
)


async def test_direct_query():
    """Test the new query_lightrag_knowledge_direct method."""
    
    print("🧪 Testing KnowledgeTools.query_lightrag_knowledge_direct()")
    print("=" * 60)
    
    try:
        # Initialize the knowledge manager
        knowledge_manager = AgentKnowledgeManager(
            user_id=USER_ID,
            storage_dir=AGNO_STORAGE_DIR,
            lightrag_url=LIGHTRAG_URL,
            lightrag_memory_url=LIGHTRAG_MEMORY_URL,
        )
        
        # Create KnowledgeTools instance
        knowledge_tools = KnowledgeTools(knowledge_manager)
        
        # Test 1: Basic direct query
        print("\n📋 Test 1: Basic direct query")
        print("-" * 30)
        
        query = "What is artificial intelligence?"
        result = await knowledge_tools.query_lightrag_knowledge_direct(query)
        
        print(f"Query: {query}")
        print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")
        
        # Test 2: Direct query with custom parameters
        print("\n📋 Test 2: Direct query with custom parameters")
        print("-" * 30)
        
        query = "machine learning"
        params = {
            "mode": "local",
            "response_type": "Single Paragraph",
            "top_k": 3
        }
        
        result = await knowledge_tools.query_lightrag_knowledge_direct(query, params)
        
        print(f"Query: {query}")
        print(f"Params: {params}")
        print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")
        
        # Test 3: Compare with regular query_knowledge_base
        print("\n📋 Test 3: Compare with regular query_knowledge_base")
        print("-" * 30)
        
        query = "programming"
        
        # Regular query
        regular_result = knowledge_tools.query_knowledge_base(query, mode="global", limit=3)
        print(f"Regular query result: {regular_result[:150]}..." if len(regular_result) > 150 else f"Regular query result: {regular_result}")
        
        # Direct query
        direct_result = await knowledge_tools.query_lightrag_knowledge_direct(
            query, 
            {"mode": "global", "top_k": 3}
        )
        print(f"Direct query result: {direct_result[:150]}..." if len(direct_result) > 150 else f"Direct query result: {direct_result}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function to run the tests."""
    print("🚀 Starting KnowledgeTools Direct Query Test")
    print(f"LightRAG URL: {LIGHTRAG_URL}")
    print(f"User ID: {USER_ID}")
    
    # Run the async test
    asyncio.run(test_direct_query())


if __name__ == "__main__":
    main()
