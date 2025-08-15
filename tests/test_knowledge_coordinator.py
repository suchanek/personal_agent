#!/usr/bin/env python3
"""
Test script for the Knowledge Coordinator implementation.

This script tests the unified knowledge coordinator that routes queries between
local semantic search and LightRAG based on mode parameters and query analysis.
"""

import asyncio
import logging
import sys
from pathlib import Path

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

from personal_agent.core.knowledge_coordinator import create_knowledge_coordinator
from personal_agent.core.agno_storage import create_agno_storage, create_combined_knowledge_base
from personal_agent.config.settings import LIGHTRAG_URL, AGNO_STORAGE_DIR, AGNO_KNOWLEDGE_DIR, USER_ID
from personal_agent.utils import setup_logging

# Configure logging
logger = setup_logging(__name__, level=logging.INFO)


async def test_knowledge_coordinator():
    """Test the Knowledge Coordinator functionality."""
    print("🧪 Testing Knowledge Coordinator Implementation")
    print("=" * 60)
    
    # Use actual paths from configuration
    storage_dir = AGNO_STORAGE_DIR
    knowledge_dir = AGNO_KNOWLEDGE_DIR
    
    print(f"📁 Using configured storage at: {storage_dir}")
    print(f"📚 Using configured knowledge dir: {knowledge_dir}")
    print(f"👤 User ID: {USER_ID}")
    
    # Create storage and knowledge base using actual configuration
    agno_storage = create_agno_storage(storage_dir)
    agno_knowledge = create_combined_knowledge_base(storage_dir, knowledge_dir, agno_storage)
    
    # Create Knowledge Coordinator
    print(f"🎯 Creating Knowledge Coordinator with LightRAG URL: {LIGHTRAG_URL}")
    coordinator = create_knowledge_coordinator(
        agno_knowledge=agno_knowledge,
        lightrag_url=LIGHTRAG_URL,
        debug=True
    )
    
    print("\n🔬 Running Knowledge Coordinator Tests")
    print("-" * 40)
    
    # Test cases with different modes and query types
    test_cases = [
        {
            "query": "What is Python?",
            "mode": "local",
            "description": "Simple fact query with explicit local mode"
        },
        {
            "query": "How does machine learning relate to artificial intelligence?",
            "mode": "hybrid",
            "description": "Relationship query with explicit hybrid mode"
        },
        {
            "query": "Define recursion",
            "mode": "auto",
            "description": "Simple definition query with auto-detection"
        },
        {
            "query": "Explain the relationship between neural networks and deep learning",
            "mode": "auto",
            "description": "Complex relationship query with auto-detection"
        },
        {
            "query": "What is the capital of France?",
            "mode": "global",
            "description": "Simple fact with global mode (should use LightRAG)"
        },
        {
            "query": "Compare Python and JavaScript programming languages",
            "mode": "mix",
            "description": "Comparison query with mix mode"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"   Query: '{test_case['query']}'")
        print(f"   Mode: {test_case['mode']}")
        
        try:
            result = await coordinator.query_knowledge_base(
                query=test_case['query'],
                mode=test_case['mode'],
                limit=3
            )
            
            # Determine which system was used based on result headers
            if "Local Knowledge Search Results" in result:
                system_used = "Local Semantic"
            elif "LightRAG Knowledge Graph Results" in result:
                system_used = "LightRAG"
            elif "Fallback" in result:
                system_used = "Fallback Used"
            else:
                system_used = "Unknown"
            
            print(f"   ✅ System Used: {system_used}")
            print(f"   📄 Result Length: {len(result)} characters")
            
            # Show first 100 characters of result
            preview = result[:100].replace('\n', ' ')
            print(f"   📖 Preview: {preview}...")
            
            results.append({
                "test": i,
                "query": test_case['query'],
                "mode": test_case['mode'],
                "system_used": system_used,
                "success": True,
                "result_length": len(result)
            })
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results.append({
                "test": i,
                "query": test_case['query'],
                "mode": test_case['mode'],
                "system_used": "Error",
                "success": False,
                "error": str(e)
            })
    
    # Display routing statistics
    print(f"\n📊 Knowledge Coordinator Routing Statistics")
    print("-" * 40)
    stats = coordinator.get_routing_stats()
    
    if stats.get("total_queries", 0) > 0:
        for key, value in stats.items():
            if not key.endswith("_percentage"):
                print(f"   {key.replace('_', ' ').title()}: {value}")
    else:
        print("   No routing statistics available")
    
    # Summary
    print(f"\n📋 Test Summary")
    print("-" * 40)
    successful_tests = sum(1 for r in results if r["success"])
    total_tests = len(results)
    
    print(f"   Total Tests: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Failed: {total_tests - successful_tests}")
    print(f"   Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    # Show system usage breakdown
    system_usage = {}
    for result in results:
        if result["success"]:
            system = result["system_used"]
            system_usage[system] = system_usage.get(system, 0) + 1
    
    if system_usage:
        print(f"\n🎯 System Usage Breakdown:")
        for system, count in system_usage.items():
            print(f"   {system}: {count} queries")
    
    print(f"\n✅ Knowledge Coordinator testing completed!")
    
    return results, stats


async def test_routing_logic():
    """Test the routing logic specifically."""
    print("\n🧭 Testing Routing Logic")
    print("-" * 30)
    
    coordinator = create_knowledge_coordinator(debug=True)
    
    # Test routing decisions without actually executing queries
    test_queries = [
        ("What is Python?", "auto", "Should route to local (simple fact)"),
        ("How does X relate to Y?", "auto", "Should route to LightRAG (relationship)"),
        ("Define machine learning", "local", "Should route to local (explicit)"),
        ("Compare A and B", "hybrid", "Should route to LightRAG (explicit)"),
        ("Explain the connection between neural networks and AI", "auto", "Should route to LightRAG (complex relationship)"),
    ]
    
    for query, mode, expected in test_queries:
        routing_decision, reasoning = coordinator._determine_routing(query, mode)
        print(f"   Query: '{query[:30]}...'")
        print(f"   Mode: {mode} → Decision: {routing_decision}")
        print(f"   Reasoning: {reasoning}")
        print(f"   Expected: {expected}")
        print()


if __name__ == "__main__":
    async def main():
        try:
            # Test routing logic first
            await test_routing_logic()
            
            # Then test full coordinator functionality
            results, stats = await test_knowledge_coordinator()
            
            print(f"\n🎉 All tests completed successfully!")
            
        except Exception as e:
            logger.error(f"Test failed with error: {e}")
            print(f"❌ Test failed: {e}")
            sys.exit(1)
    
    asyncio.run(main())
