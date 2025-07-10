import asyncio
import os
import shutil
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# Add project root to the Python path to allow for module imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

from src.personal_agent.core.agno_agent import AgnoPersonalAgent, create_agno_agent
from src.personal_agent.core.semantic_memory_manager import SemanticMemoryManager


async def main():
    """
    A standalone script to verify the user fact restatement functionality.

    This script will:
    1. Initialize the agent in a clean test environment.
    2. Store several facts using the agent's memory system.
    3. Verify that the facts are stored literally in the local semantic memory.
    4. Verify that the facts are correctly restated before being sent to the graph memory.
    """
    user_id = "test_user_123"
    test_data_dir = "./test_data"
    print(f"--- Testing Fact Restatement for user: {user_id} ---")

    # Ensure a clean environment for the test
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)
    os.makedirs(test_data_dir)
    os.environ["DATA_DIR"] = test_data_dir

    # We patch `store_graph_memory` directly on the class prototype.
    # This is the cleanest way to intercept the call for this specific test.
    with patch(
        "personal_agent.core.agno_agent.AgnoPersonalAgent.store_graph_memory",
        new_callable=AsyncMock,
    ) as mock_store_graph_memory:
        # Configure the mock to avoid breaking the `store_user_memory` method
        mock_store_graph_memory.return_value = "✅ Mocked graph memory success"

        # 1. Initialize the agent
        print("\n[1] Initializing agent...")
        agent: AgnoPersonalAgent = await create_agno_agent(
            user_id=user_id, enable_mcp=False, recreate=True
        )
        print("✅ Agent initialized successfully.")

        # The `store_user_memory` method calls the `store_graph_memory` tool,
        # but our patch intercepts the original `store_graph_memory` method on the agent instance.
        # To make this test work, we need to manually replace the tool function
        # with our mock after the agent is initialized.
        for i, tool in enumerate(agent.agent.tools):
            if getattr(tool, "__name__", "") == "store_graph_memory":
                agent.agent.tools[i] = mock_store_graph_memory
                break

        # 2. Define facts and store them
        facts = [
            "I have a PhD in computer science.",
            "My favorite hobby is hiking.",
            "I'm learning to play the guitar.",
            "I live in New York.",
            "My cat's name is Luna.",
        ]
        print(f"\n[2] Storing {len(facts)} facts...")
        for fact in facts:
            print(f"  - Storing: '{fact}'")
            await agent.store_user_memory(content=fact)
        print("✅ Facts stored.")

        # 3. Verify Semantic (Local) Memory
        print("\n[3] Verifying Semantic (Local) Memory...")
        memory_manager: SemanticMemoryManager = agent.agno_memory.memory_manager
        all_memories = memory_manager.get_memories_by_topic(
            db=agent.agno_memory.db, user_id=user_id
        )
        stored_semantic_facts = sorted([mem.memory for mem in all_memories])

        print("   Facts stored in Semantic Memory (should be literal):")
        for i, fact in enumerate(stored_semantic_facts):
            print(f"     - [{i+1}] {fact}")

        assert stored_semantic_facts == sorted(facts), "Semantic memory mismatch!"
        print("   ✅ SUCCESS: Semantic memory contains the correct, literal facts.")

        # 4. Verify Graph Memory Input
        print("\n[4] Verifying Graph Memory Input (should be restated)...")

        # Check that our mock was called for each fact
        assert mock_store_graph_memory.call_count == len(
            facts
        ), "Graph store was not called for each fact."

        print("   Calls to store_graph_memory contain restated facts:")
        graph_call_args = [
            call.args[0] for call in mock_store_graph_memory.call_args_list
        ]

        for fact in facts:
            original = fact
            restated = agent._restate_user_fact(original)
            print(f"     - Original: '{original}'")
            print(f"     - Restated: '{restated}'")
            assert (
                restated in graph_call_args
            ), f"Restated fact '{restated}' not found in graph calls."

        print("   ✅ SUCCESS: All facts were correctly restated for the graph.")
        print("\n--- Test Complete ---")

    # Clean up the test data directory
    shutil.rmtree(test_data_dir)


if __name__ == "__main__":
    asyncio.run(main())