#!/usr/bin/env python3
"""
Test script for the new knowledge ingestion system.

This script demonstrates how to use the new knowledge ingestion tools
to easily add files and content to the personal agent's knowledge base.
"""

import asyncio
import os
import tempfile
from pathlib import Path

# Add the src directory to the Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.tools.knowledge_tools import KnowledgeTools
from personal_agent.core.knowledge_manager import KnowledgeManager
from personal_agent.config import settings


async def test_knowledge_ingestion():
    """Test the knowledge ingestion system."""
    print("🧪 Testing Knowledge Ingestion System")
    print("=" * 50)
    
    # Initialize the knowledge manager
    knowledge_manager = KnowledgeManager(
        user_id="test_user",
        knowledge_dir=settings.AGNO_KNOWLEDGE_DIR,
        lightrag_url=settings.LIGHTRAG_URL
    )
    
    # Initialize the knowledge tools
    knowledge_tools = KnowledgeTools(knowledge_manager, agno_knowledge=None)
    
    print(f"📁 Knowledge directory: {settings.AGNO_KNOWLEDGE_DIR}")
    print(f"🌐 LightRAG URL: {settings.LIGHTRAG_URL}")
    print()
    
    # Test 1: Check server status
    print("1️⃣ Testing server connectivity...")
    server_online = await knowledge_manager.check_server_status()
    print(f"   Server status: {'🟢 Online' if server_online else '🔴 Offline'}")
    
    if not server_online:
        print("❌ LightRAG server is not accessible. Please start the server first.")
        print("   Run: ./smart-restart-lightrag.sh")
        return
    
    # Test 2: Get knowledge statistics
    print("\n2️⃣ Getting knowledge base statistics...")
    stats = await knowledge_manager.get_knowledge_stats()
    print(f"   Local files: {stats.get('local_files', 0)}")
    print(f"   Server documents: {stats.get('server_documents', 0)}")
    print(f"   Pipeline status: {stats.get('pipeline_status', 'unknown')}")
    
    # Test 3: Ingest text content
    print("\n3️⃣ Testing text content ingestion...")
    test_content = """
    This is a test document for the knowledge ingestion system.
    
    Key Features:
    - Easy file ingestion through natural conversation
    - Support for multiple file formats (txt, md, pdf, docx, etc.)
    - Automatic processing via LightRAG server
    - Unified querying across knowledge base
    
    The system allows users to easily add new knowledge by simply asking
    the agent to ingest files or content.
    """
    
    result = knowledge_tools.ingest_knowledge_text(
        content=test_content,
        title="Knowledge Ingestion Test Document",
        file_type="md"
    )
    print(f"   Result: {result}")
    
    # Test 4: Create a temporary file and ingest it
    print("\n4️⃣ Testing file ingestion...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write("""
        Personal Agent Knowledge Base Test File
        =====================================
        
        This file was created to test the file ingestion capabilities
        of the personal agent's knowledge system.
        
        Topics covered:
        - File ingestion workflow
        - LightRAG integration
        - Knowledge base management
        - User experience improvements
        
        The agent can now easily ingest files through simple commands like:
        "Please ingest the file ~/Documents/research.pdf into my knowledge base"
        """)
        temp_file_path = temp_file.name
    
    try:
        result = knowledge_tools.ingest_knowledge_file(
            file_path=temp_file_path,
            title="Test File Ingestion"
        )
        print(f"   Result: {result}")
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass
    
    # Test 5: Test URL ingestion (if network is available)
    print("\n5️⃣ Testing URL content ingestion...")
    try:
        result = knowledge_tools.ingest_knowledge_from_url(
            url="https://httpbin.org/json",
            title="Test JSON Data"
        )
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Skipped (network error): {e}")
    
    # Test 6: Query the knowledge base
    print("\n6️⃣ Testing knowledge base querying...")
    result = knowledge_tools.query_knowledge_base(
        query="knowledge ingestion system",
        mode="hybrid",
        limit=3
    )
    print(f"   Query result: {result[:200]}..." if len(result) > 200 else f"   Query result: {result}")
    
    # Test 7: Get updated statistics
    print("\n7️⃣ Getting updated statistics...")
    stats = await knowledge_manager.get_knowledge_stats()
    print(f"   Local files: {stats.get('local_files', 0)}")
    print(f"   Server documents: {stats.get('server_documents', 0)}")
    print(f"   Pipeline status: {stats.get('pipeline_status', 'unknown')}")
    
    # Test 8: Validate sync status
    print("\n8️⃣ Validating knowledge sync...")
    sync_status = await knowledge_manager.validate_knowledge_sync()
    print(f"   Local files: {sync_status.get('local_files', 0)}")
    print(f"   Server documents: {sync_status.get('server_documents', 0)}")
    if sync_status.get('sync_issues'):
        print(f"   Issues: {', '.join(sync_status['sync_issues'])}")
    if sync_status.get('recommendations'):
        print(f"   Recommendations: {', '.join(sync_status['recommendations'])}")
    
    print("\n✅ Knowledge ingestion testing complete!")
    print("\nThe system is now ready for users to easily add knowledge through:")
    print("- 'Please ingest the file ~/Documents/research.pdf'")
    print("- 'Add this text to my knowledge base: [content]'")
    print("- 'Ingest content from https://example.com/article'")
    print("- 'Process all markdown files in ~/Notes/'")


async def main():
    """Main function."""
    try:
        await test_knowledge_ingestion()
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
