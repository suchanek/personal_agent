"""
Test script for CLI memory commands to verify dual storage functionality.

This script tests that the CLI memory commands properly update both
the local SQLite memory system and the LightRAG graph memory system.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional, Tuple

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rich.console import Console

from src.personal_agent.core.agno_agent import AgnoPersonalAgent
from src.personal_agent.core.agno_initialization import initialize_agno_system
from src.personal_agent.cli.memory_commands import (
    clear_all_memories,
    delete_memories_by_topic_cli,
    delete_memory_by_id_cli,
    show_all_memories,
    show_memories_by_topic_cli,
    show_memory_analysis,
    show_memory_stats,
    store_immediate_memory,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class CapturingConsole(Console):
    """A Rich Console that captures output for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.captured_output = []

    def print(self, *args, **kwargs):
        """Capture print output."""
        output = " ".join(str(arg) for arg in args)
        self.captured_output.append(output)
        super().print(*args, **kwargs)

    def get_output(self) -> List[str]:
        """Get the captured output."""
        return self.captured_output

    def clear_output(self):
        """Clear the captured output."""
        self.captured_output = []


async def verify_memory_in_lightrag(agent: AgnoPersonalAgent, content: str) -> bool:
    """
    Verify that a memory exists in the LightRAG graph memory system.
    
    Args:
        agent: The AgnoPersonalAgent instance
        content: The memory content to search for
        
    Returns:
        True if the memory is found in LightRAG, False otherwise
    """
    try:
        # Find the query_graph_memory tool function
        query_graph_memory_func = None
        if agent.agent and hasattr(agent.agent, "tools"):
            for tool in agent.agent.tools:
                if getattr(tool, "__name__", "") == "query_graph_memory":
                    query_graph_memory_func = tool
                    break
        
        if not query_graph_memory_func:
            logger.warning("query_graph_memory tool function not found")
            return False
        
        # Query the LightRAG graph memory system
        result = await query_graph_memory_func(content, "mix", 5, "Multiple Paragraphs")
        
        # Check if the result contains the memory content
        if isinstance(result, dict) and "response" in result:
            return content.lower() in result["response"].lower()
        elif isinstance(result, dict) and "content" in result:
            return content.lower() in result["content"].lower()
        elif isinstance(result, str):
            return content.lower() in result.lower()
        else:
            logger.warning(f"Unexpected result format: {type(result)}")
            return False
    
    except Exception as e:
        logger.error(f"Error verifying memory in LightRAG: {e}")
        return False


async def verify_memory_in_sqlite(agent: AgnoPersonalAgent, content: str) -> bool:
    """
    Verify that a memory exists in the local SQLite memory system.
    
    Args:
        agent: The AgnoPersonalAgent instance
        content: The memory content to search for
        
    Returns:
        True if the memory is found in SQLite, False otherwise
    """
    try:
        if not agent.agno_memory:
            logger.warning("No memory system available")
            return False
        
        # Search for the memory in the local SQLite system
        results = agent.agno_memory.memory_manager.search_memories(
            query=content,
            db=agent.agno_memory.db,
            user_id=agent.user_id,
            limit=10,
            similarity_threshold=0.7,  # Higher threshold for more exact matches
            search_topics=False,
        )
        
        # Check if any result contains the memory content
        for memory, _ in results:
            if content.lower() in memory.memory.lower():
                return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error verifying memory in SQLite: {e}")
        return False


async def run_tests():
    """Run tests for CLI memory commands."""
    logger.info("Initializing agent for testing...")
    
    # Initialize the agent
    agent, _, _, _, _ = await initialize_agno_system(use_remote_ollama=False, recreate=False)
    
    # Create a capturing console for testing
    console = CapturingConsole(force_terminal=True)
    
    try:
        # Test 1: Clear all memories to start with a clean state
        logger.info("Test 1: Clearing all memories...")
        await clear_all_memories(agent, console)
        console.clear_output()
        
        # Test 2: Store a memory
        logger.info("Test 2: Storing a memory...")
        test_memory = f"This is a test memory for CLI commands testing at {asyncio.get_event_loop().time()}"
        await store_immediate_memory(agent, test_memory, console)
        
        # Verify the memory was stored in both systems
        in_sqlite = await verify_memory_in_sqlite(agent, test_memory)
        in_lightrag = await verify_memory_in_lightrag(agent, test_memory)
        
        logger.info(f"Memory in SQLite: {in_sqlite}")
        logger.info(f"Memory in LightRAG: {in_lightrag}")
        
        if in_sqlite and in_lightrag:
            logger.info("✅ Test 2 PASSED: Memory stored in both systems")
        elif in_sqlite:
            logger.warning("⚠️ Test 2 PARTIAL: Memory stored in SQLite only")
        elif in_lightrag:
            logger.warning("⚠️ Test 2 PARTIAL: Memory stored in LightRAG only")
        else:
            logger.error("❌ Test 2 FAILED: Memory not stored in either system")
        
        console.clear_output()
        
        # Test 3: Show all memories
        logger.info("Test 3: Showing all memories...")
        await show_all_memories(agent, console)
        output = console.get_output()
        
        if any(test_memory in line for line in output):
            logger.info("✅ Test 3 PASSED: Memory found in all memories")
        else:
            logger.error("❌ Test 3 FAILED: Memory not found in all memories")
            logger.debug(f"Output: {output}")
        
        console.clear_output()
        
        # Test 4: Store a memory with a topic
        logger.info("Test 4: Storing a memory with a topic...")
        test_topic = "test_topic"
        test_memory_with_topic = f"This is a test memory with topic '{test_topic}' at {asyncio.get_event_loop().time()}"
        
        # Find the store_user_memory tool function
        store_memory_func = None
        if agent.agent and hasattr(agent.agent, "tools"):
            for tool in agent.agent.tools:
                if getattr(tool, "__name__", "") == "store_user_memory":
                    store_memory_func = tool
                    break
        
        if store_memory_func:
            await store_memory_func(test_memory_with_topic, [test_topic])
            logger.info("Memory stored with topic using tool function")
        else:
            # Fallback to direct agent method
            await agent.store_user_memory(content=test_memory_with_topic, topics=[test_topic])
            logger.info("Memory stored with topic using direct agent method")
        
        # Test 5: Show memories by topic
        logger.info("Test 5: Showing memories by topic...")
        await show_memories_by_topic_cli(agent, test_topic, console)
        output = console.get_output()
        
        if any(test_memory_with_topic in line for line in output):
            logger.info("✅ Test 5 PASSED: Memory found by topic")
        else:
            logger.error("❌ Test 5 FAILED: Memory not found by topic")
            logger.debug(f"Output: {output}")
        
        console.clear_output()
        
        # Test 6: Show memory analysis
        logger.info("Test 6: Showing memory analysis...")
        await show_memory_analysis(agent, console)
        output = console.get_output()
        
        if any("Memory Analysis" in line for line in output):
            logger.info("✅ Test 6 PASSED: Memory analysis displayed")
        else:
            logger.error("❌ Test 6 FAILED: Memory analysis not displayed")
            logger.debug(f"Output: {output}")
        
        console.clear_output()
        
        # Test 7: Show memory stats
        logger.info("Test 7: Showing memory stats...")
        await show_memory_stats(agent, console)
        output = console.get_output()
        
        if any("Memory Stats" in line for line in output):
            logger.info("✅ Test 7 PASSED: Memory stats displayed")
        else:
            logger.error("❌ Test 7 FAILED: Memory stats not displayed")
            logger.debug(f"Output: {output}")
        
        console.clear_output()
        
        # Test 8: Delete memory by topic
        logger.info("Test 8: Deleting memory by topic...")
        await delete_memories_by_topic_cli(agent, test_topic, console)
        output = console.get_output()
        
        # Verify the memory was deleted from both systems
        in_sqlite = await verify_memory_in_sqlite(agent, test_memory_with_topic)
        in_lightrag = await verify_memory_in_lightrag(agent, test_memory_with_topic)
        
        if not in_sqlite and not in_lightrag:
            logger.info("✅ Test 8 PASSED: Memory deleted from both systems")
        elif not in_sqlite:
            logger.warning("⚠️ Test 8 PARTIAL: Memory deleted from SQLite only")
        elif not in_lightrag:
            logger.warning("⚠️ Test 8 PARTIAL: Memory deleted from LightRAG only")
        else:
            logger.error("❌ Test 8 FAILED: Memory not deleted from either system")
        
        console.clear_output()
        
        # Test 9: Delete memory by ID
        logger.info("Test 9: Deleting memory by ID...")
        
        # First, get the memory ID
        memory_id = None
        if agent.agno_memory:
            results = agent.agno_memory.memory_manager.search_memories(
                query=test_memory,
                db=agent.agno_memory.db,
                user_id=agent.user_id,
                limit=1,
                similarity_threshold=0.7,
                search_topics=False,
            )
            
            if results:
                memory_id = results[0][0].id
        
        if memory_id:
            await delete_memory_by_id_cli(agent, memory_id, console)
            output = console.get_output()
            
            # Verify the memory was deleted from both systems
            in_sqlite = await verify_memory_in_sqlite(agent, test_memory)
            in_lightrag = await verify_memory_in_lightrag(agent, test_memory)
            
            if not in_sqlite and not in_lightrag:
                logger.info("✅ Test 9 PASSED: Memory deleted from both systems")
            elif not in_sqlite:
                logger.warning("⚠️ Test 9 PARTIAL: Memory deleted from SQLite only")
            elif not in_lightrag:
                logger.warning("⚠️ Test 9 PARTIAL: Memory deleted from LightRAG only")
            else:
                logger.error("❌ Test 9 FAILED: Memory not deleted from either system")
        else:
            logger.warning("⚠️ Test 9 SKIPPED: Could not find memory ID")
        
        console.clear_output()
        
        # Test 10: Clear all memories
        logger.info("Test 10: Clearing all memories...")
        
        # First, store a new memory
        test_memory_final = f"Final test memory at {asyncio.get_event_loop().time()}"
        await store_immediate_memory(agent, test_memory_final, console)
        console.clear_output()
        
        # Then clear all memories
        await clear_all_memories(agent, console)
        output = console.get_output()
        
        # Verify all memories were cleared from both systems
        in_sqlite = await verify_memory_in_sqlite(agent, test_memory_final)
        in_lightrag = await verify_memory_in_lightrag(agent, test_memory_final)
        
        if not in_sqlite and not in_lightrag:
            logger.info("✅ Test 10 PASSED: All memories cleared from both systems")
        elif not in_sqlite:
            logger.warning("⚠️ Test 10 PARTIAL: Memories cleared from SQLite only")
        elif not in_lightrag:
            logger.warning("⚠️ Test 10 PARTIAL: Memories cleared from LightRAG only")
        else:
            logger.error("❌ Test 10 FAILED: Memories not cleared from either system")
        
        logger.info("All tests completed!")
    
    finally:
        # Clean up
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(run_tests())