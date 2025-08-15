#!/usr/bin/env python3
"""
Test script to verify the knowledge ingestion consolidation works correctly.

This script tests:
1. KnowledgeTools class has all expected methods
2. Both LightRAG and semantic KB ingestion methods work
3. Dual KB support functions properly
4. Semantic KB recreation works
5. Agent initialization with consolidated tools
"""

import asyncio
import os
import tempfile
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import create_agno_agent
from personal_agent.tools.knowledge_tools import KnowledgeTools
from personal_agent.core.knowledge_manager import KnowledgeManager
from personal_agent.config.settings import get_userid


def test_knowledge_tools_methods():
    """Test that KnowledgeTools has all expected methods."""
    print("🧪 Testing KnowledgeTools methods...")
    
    # Create a dummy knowledge manager for testing
    km = KnowledgeManager(user_id=get_userid())
    kt = KnowledgeTools(km, agno_knowledge=None)
    
    # Test LightRAG methods exist
    lightrag_methods = [
        'ingest_knowledge_file',
        'ingest_knowledge_text', 
        'ingest_knowledge_from_url',
        'batch_ingest_directory',
        'query_knowledge_base',
        'query_lightrag_knowledge_direct'
    ]
    
    # Test semantic KB methods exist
    semantic_methods = [
        'ingest_semantic_file',
        'ingest_semantic_text',
        'ingest_semantic_from_url', 
        'batch_ingest_semantic_directory',
        'query_semantic_knowledge',
        'recreate_semantic_kb'
    ]
    
    all_methods = lightrag_methods + semantic_methods
    missing_methods = []
    
    for method in all_methods:
        if not hasattr(kt, method):
            missing_methods.append(method)
        else:
            print(f"  ✅ {method}")
    
    if missing_methods:
        print(f"  ❌ Missing methods: {missing_methods}")
        return False
    
    print("  ✅ All expected methods found in KnowledgeTools")
    return True


def test_text_ingestion():
    """Test text ingestion to both knowledge bases."""
    print("\n🧪 Testing text ingestion...")
    
    try:
        km = KnowledgeManager(user_id=get_userid())
        kt = KnowledgeTools(km, agno_knowledge=None)
        
        # Test LightRAG text ingestion
        test_content = "This is a test document for knowledge ingestion consolidation testing."
        test_title = "Test Document"
        
        print("  Testing LightRAG text ingestion...")
        result = kt.ingest_knowledge_text(test_content, test_title)
        print(f"  LightRAG result: {result[:100]}...")
        
        # Test semantic KB text ingestion  
        print("  Testing semantic KB text ingestion...")
        result = kt.ingest_semantic_text(test_content, test_title)
        print(f"  Semantic KB result: {result[:100]}...")
        
        print("  ✅ Text ingestion tests completed")
        return True
        
    except Exception as e:
        print(f"  ❌ Text ingestion test failed: {e}")
        return False


def test_file_ingestion():
    """Test file ingestion with a temporary file."""
    print("\n🧪 Testing file ingestion...")
    
    try:
        km = KnowledgeManager(user_id=get_userid())
        kt = KnowledgeTools(km, agno_knowledge=None)
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test file for knowledge ingestion consolidation.\n")
            f.write("It contains multiple lines of test content.\n")
            f.write("This helps verify file ingestion works correctly.")
            temp_file = f.name
        
        try:
            # Test LightRAG file ingestion
            print("  Testing LightRAG file ingestion...")
            result = kt.ingest_knowledge_file(temp_file, "Test File")
            print(f"  LightRAG result: {result[:100]}...")
            
            # Test semantic KB file ingestion
            print("  Testing semantic KB file ingestion...")
            result = kt.ingest_semantic_file(temp_file, "Test File Semantic")
            print(f"  Semantic KB result: {result[:100]}...")
            
            print("  ✅ File ingestion tests completed")
            return True
            
        finally:
            # Clean up temp file
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"  ❌ File ingestion test failed: {e}")
        return False


def test_semantic_kb_recreation():
    """Test semantic KB recreation functionality."""
    print("\n🧪 Testing semantic KB recreation...")
    
    try:
        km = KnowledgeManager(user_id=get_userid())
        kt = KnowledgeTools(km, agno_knowledge=None)
        
        # Test recreation method exists and can be called
        result = kt.recreate_semantic_kb()
        print(f"  Recreation result: {result[:100]}...")
        
        print("  ✅ Semantic KB recreation test completed")
        return True
        
    except Exception as e:
        print(f"  ❌ Semantic KB recreation test failed: {e}")
        return False


async def test_agent_initialization():
    """Test that agent initializes correctly with consolidated tools."""
    print("\n🧪 Testing agent initialization with consolidated tools...")
    
    try:
        # Create agent with memory enabled
        agent = await create_agno_agent(
            model_provider="ollama",
            model_name="llama3.2:3b",
            enable_memory=True,
            debug=True,
            recreate=False
        )
        
        print("  ✅ Agent created successfully")
        
        # Check that knowledge_tools exists and has expected methods
        if hasattr(agent, 'knowledge_tools') and agent.knowledge_tools:
            kt = agent.knowledge_tools
            
            # Test a few key methods exist
            key_methods = ['ingest_knowledge_file', 'ingest_semantic_file', 'recreate_semantic_kb']
            for method in key_methods:
                if hasattr(kt, method):
                    print(f"  ✅ Agent has {method}")
                else:
                    print(f"  ❌ Agent missing {method}")
                    return False
        else:
            print("  ❌ Agent missing knowledge_tools")
            return False
        
        # Check tool count
        if hasattr(agent, 'tools') and agent.tools:
            print(f"  ✅ Agent has {len(agent.tools)} tools loaded")
            
            # Look for KnowledgeTools in the tools list
            knowledge_tool_found = False
            for tool in agent.tools:
                if 'KnowledgeTools' in str(type(tool).__name__):
                    knowledge_tool_found = True
                    print(f"  ✅ Found KnowledgeTools in agent tools")
                    break
            
            if not knowledge_tool_found:
                print("  ⚠️  KnowledgeTools not found in agent tools list")
        
        print("  ✅ Agent initialization test completed")
        return True
        
    except Exception as e:
        print(f"  ❌ Agent initialization test failed: {e}")
        return False


async def test_agent_query():
    """Test a simple agent query to ensure everything works end-to-end."""
    print("\n🧪 Testing agent query functionality...")
    
    try:
        # Create agent
        agent = await create_agno_agent(
            model_provider="ollama", 
            model_name="llama3.2:3b",
            enable_memory=True,
            debug=False,
            recreate=False
        )
        
        # Test a simple query
        print("  Running test query...")
        response = await agent.run("Hello, can you tell me about your knowledge capabilities?")
        
        if response and len(response.strip()) > 0:
            print(f"  ✅ Agent responded: {response[:100]}...")
            return True
        else:
            print("  ❌ Agent returned empty response")
            return False
            
    except Exception as e:
        print(f"  ❌ Agent query test failed: {e}")
        return False


def test_import_cleanup():
    """Test that deleted classes can't be imported."""
    print("\n🧪 Testing import cleanup...")
    
    # Test that deleted classes raise ImportError
    try:
        from personal_agent.tools.knowledge_ingestion_tools import KnowledgeIngestionTools
        print("  ❌ KnowledgeIngestionTools should not be importable")
        return False
    except ImportError:
        print("  ✅ KnowledgeIngestionTools correctly not importable")
    
    try:
        from personal_agent.tools.semantic_knowledge_ingestion_tools import SemanticKnowledgeIngestionTools
        print("  ❌ SemanticKnowledgeIngestionTools should not be importable")
        return False
    except ImportError:
        print("  ✅ SemanticKnowledgeIngestionTools correctly not importable")
    
    # Test that KnowledgeTools can still be imported
    try:
        from personal_agent.tools.knowledge_tools import KnowledgeTools
        print("  ✅ KnowledgeTools correctly importable")
        return True
    except ImportError as e:
        print(f"  ❌ KnowledgeTools should be importable: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Knowledge Ingestion Consolidation Tests\n")
    
    tests = [
        ("Import Cleanup", test_import_cleanup),
        ("KnowledgeTools Methods", test_knowledge_tools_methods),
        ("Text Ingestion", test_text_ingestion),
        ("File Ingestion", test_file_ingestion),
        ("Semantic KB Recreation", test_semantic_kb_recreation),
        ("Agent Initialization", test_agent_initialization),
        ("Agent Query", test_agent_query),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Knowledge ingestion consolidation is working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the consolidation.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
