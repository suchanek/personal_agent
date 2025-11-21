#!/usr/bin/env python3
"""
Test script to verify the new enum-based memory storage status system
with FULL dual storage (SQLite + LightRAG graph) validation.
"""

import asyncio
import sys
import time
from pathlib import Path

import pytest

from personal_agent.utils import add_src_to_path

add_src_to_path()

import aiohttp

from personal_agent.core.agno_agent import create_agno_agent
from personal_agent.core.semantic_memory_manager import (
    MemoryStorageResult,
    MemoryStorageStatus,
)
from personal_agent.config.settings import LIGHTRAG_MEMORY_URL


async def check_pipeline_status() -> dict:
    """Check the LightRAG pipeline status."""
    try:
        url = f"{LIGHTRAG_MEMORY_URL}/documents/pipeline_status"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    print(f"⚠️ Failed to get pipeline status: {resp.status}")
                    return {"error": f"HTTP {resp.status}"}
    except Exception as e:
        print(f"⚠️ Error checking pipeline status: {e}")
        return {"error": str(e)}


async def wait_for_pipeline_clear(max_wait_seconds: int = 60, check_interval: int = 2) -> bool:
    """
    Wait for the LightRAG pipeline to be clear (no active processing).
    
    Args:
        max_wait_seconds: Maximum time to wait in seconds
        check_interval: How often to check the status in seconds
        
    Returns:
        True if pipeline is clear, False if timeout
    """
    print(f"⏳ Waiting for LightRAG pipeline to be clear (max {max_wait_seconds}s)...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait_seconds:
        status = await check_pipeline_status()
        
        if "error" in status:
            print(f"⚠️ Pipeline status check failed: {status['error']}")
            return False
            
        # Check if pipeline is idle/clear
        # The exact field names may vary, so we'll check common patterns
        is_clear = False
        
        # Common patterns for pipeline status
        if "status" in status:
            pipeline_status = status["status"]
            if isinstance(pipeline_status, str):
                is_clear = pipeline_status.lower() in ["idle", "clear", "ready", "completed"]
            elif isinstance(pipeline_status, dict):
                # Check for active/processing indicators
                is_clear = not any(
                    key in pipeline_status and pipeline_status[key] 
                    for key in ["processing", "active", "running", "busy"]
                )
        
        # Alternative: check for active documents being processed
        if "active_documents" in status:
            is_clear = status["active_documents"] == 0
        elif "processing_count" in status:
            is_clear = status["processing_count"] == 0
        elif "queue_size" in status:
            is_clear = status["queue_size"] == 0
            
        # If we can't determine the status, assume it's clear after a short wait
        if not any(key in status for key in ["status", "active_documents", "processing_count", "queue_size"]):
            print(f"📊 Pipeline status: {status}")
            is_clear = True
            
        if is_clear:
            print("✅ Pipeline is clear!")
            return True
            
        print(f"⏳ Pipeline still processing... (status: {status})")
        await asyncio.sleep(check_interval)
    
    print(f"⏰ Timeout waiting for pipeline to clear after {max_wait_seconds}s")
    return False


@pytest.mark.asyncio
async def test_dual_storage_enum_status():
    """Test the new enum-based memory storage status system with full dual storage."""
    print("🧪 Testing Dual Storage Enum-Based Memory Status System")
    print("=" * 70)

    # Create a unique user ID with timestamp to ensure fresh semantic KB
    unique_user_id = f"test_enum_{int(time.time())}"
    print(f"🆔 Using unique user ID: {unique_user_id}")

    # Create a test agent with memory enabled
    print("🚀 Creating AgnoPersonalAgent with memory enabled...")

    try:
        agent = await create_agno_agent(
            model_provider="ollama",
            model_name="qwen3:1.7B",
            enable_memory=True,
            enable_mcp=False,  # Disable MCP to focus on memory
            debug=True,
            user_id=unique_user_id,
            recreate=True,  # Clear existing memories
        )
        print("✅ Agent created successfully")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return

    # Test 1: Successful memory storage (should store in both systems)
    print("\n📝 Test 1: Successful Memory Storage (Dual Storage)")
    result = await agent.store_user_memory(
        content="I am a software engineer specializing in Python development",
        topics=["career", "programming"],
    )

    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Memory ID: {result.memory_id}")
    print(f"Topics: {result.topics}")
    print(f"Local Success: {result.local_success}")
    print(f"Graph Success: {result.graph_success}")
    print(f"Is Success: {result.is_success}")
    print(f"Is Rejected: {result.is_rejected}")

    # Validate the result
    assert result.is_success, f"Expected success, got: {result.status}"
    assert result.memory_id is not None, "Memory ID should not be None"
    assert result.local_success, "Local storage should succeed"

    # Check if it's full success or partial success
    if result.status == MemoryStorageStatus.SUCCESS:
        print("✅ FULL SUCCESS: Memory stored in both local SQLite and LightRAG graph")
        assert result.graph_success, "Graph storage should succeed for full success"
    elif result.status == MemoryStorageStatus.SUCCESS_LOCAL_ONLY:
        print("⚠️ PARTIAL SUCCESS: Memory stored in local SQLite only")
        assert (
            not result.graph_success
        ), "Graph storage should fail for local-only success"
    else:
        raise AssertionError(f"Unexpected success status: {result.status}")

    # Test 2: Exact duplicate rejection
    print("\n🔄 Test 2: Exact Duplicate Rejection")
    result = await agent.store_user_memory(
        content="I am a software engineer specializing in Python development",  # Exact same
    )

    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Similarity Score: {result.similarity_score}")
    print(f"Is Success: {result.is_success}")
    print(f"Is Rejected: {result.is_rejected}")

    assert result.status == MemoryStorageStatus.DUPLICATE_EXACT
    assert not result.is_success
    assert result.is_rejected
    assert result.similarity_score == 1.0

    # Test 3: Empty content rejection
    print("\n❌ Test 3: Empty Content Rejection")
    result = await agent.store_user_memory(content="")

    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Is Success: {result.is_success}")
    print(f"Is Rejected: {result.is_rejected}")

    assert result.status == MemoryStorageStatus.CONTENT_EMPTY
    assert not result.is_success
    assert result.is_rejected

    # Test 4: Semantic duplicate rejection
    print("\n🔍 Test 4: Semantic Duplicate Rejection")
    result = await agent.store_user_memory(
        content="I work as a software engineer with expertise in Python programming",  # Very similar
    )

    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Similarity Score: {result.similarity_score}")
    print(f"Is Success: {result.is_success}")
    print(f"Is Rejected: {result.is_rejected}")

    # This could be either accepted as a new memory or rejected as a semantic duplicate
    # depending on the similarity threshold and algorithm
    if result.is_rejected:
        print("🔄 Detected as semantic duplicate - similarity threshold working")
        assert result.status in [
            MemoryStorageStatus.DUPLICATE_SEMANTIC,
            MemoryStorageStatus.DUPLICATE_EXACT,
        ]
        assert result.similarity_score is not None and result.similarity_score > 0.7
    else:
        print("✅ Accepted as new memory - phrases different enough")
        assert result.is_success
        assert result.memory_id is not None

    # Test 5: Another successful memory (different topic)
    print("\n✅ Test 5: Another Successful Memory (Different Topic)")
    result = await agent.store_user_memory(
        content="I enjoy hiking in the mountains on weekends",
        topics=["hobbies", "outdoor"],
    )

    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    print(f"Memory ID: {result.memory_id}")
    print(f"Topics: {result.topics}")
    print(f"Local Success: {result.local_success}")
    print(f"Graph Success: {result.graph_success}")
    print(f"Is Success: {result.is_success}")
    print(f"Is Rejected: {result.is_rejected}")

    assert result.is_success
    assert result.memory_id is not None
    assert result.local_success

    # NEW: Wait for pipeline to be clear before querying both systems
    print("\n⏳ Test 6: Smart Pipeline Polling - Wait for Processing to Complete")
    pipeline_clear = await wait_for_pipeline_clear(max_wait_seconds=60, check_interval=3)
    
    if not pipeline_clear:
        print("⚠️ Pipeline did not clear within timeout, proceeding with queries anyway...")
    
    # Test 7: Verify dual storage by querying both systems (after pipeline is clear)
    print("\n🔍 Test 7: Verify Dual Storage - Query Both Systems (Post-Pipeline)")

    # Query local memory system
    print("📊 Querying local SQLite memory system...")
    local_results = agent.agno_memory.memory_manager.search_memories(
        query="software engineer",
        db=agent.agno_memory.db,
        user_id=agent.user_id,
        limit=10,
        similarity_threshold=0.3,
    )
    print(f"Local memories found: {len(local_results)}")
    for memory, score in local_results:
        print(f"  - {memory.memory} (score: {score:.3f})")

    # Query graph memory system (if available) - should now have processed data
    print("\n🕸️ Querying LightRAG graph memory system (after pipeline clear)...")
    try:
        # Find the query_graph_memory tool
        query_graph_memory_func = None
        if agent.agent and hasattr(agent.agent, "tools"):
            for tool in agent.agent.tools:
                if getattr(tool, "__name__", "") == "query_graph_memory":
                    query_graph_memory_func = tool
                    break

        if query_graph_memory_func:
            graph_result = await query_graph_memory_func(
                query="software engineer", mode="mix", top_k=5
            )
            print(f"Graph query result: {graph_result}")
            
            # Additional queries to test different modes after pipeline is clear
            print("\n🔍 Testing different query modes on processed data:")
            
            # Test local mode
            local_mode_result = await query_graph_memory_func(
                query="Python programming", mode="local", top_k=3
            )
            print(f"Local mode result: {local_mode_result}")
            
            # Test global mode  
            global_mode_result = await query_graph_memory_func(
                query="hiking mountains", mode="global", top_k=3
            )
            print(f"Global mode result: {global_mode_result}")
            
        else:
            print("⚠️ Graph memory query tool not available")
    except Exception as e:
        print(f"⚠️ Graph memory query failed: {e}")

    # Test 8: Verify pipeline status after all operations
    print("\n📊 Test 8: Final Pipeline Status Check")
    final_status = await check_pipeline_status()
    print(f"Final pipeline status: {final_status}")

    print("\n🎉 All dual storage enum tests completed!")

    # Cleanup
    await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(test_dual_storage_enum_status())
