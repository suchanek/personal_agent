import asyncio
import os
import pytest
import time
from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.config.settings import LIGHTRAG_MEMORY_URL, USER_ID

# Assuming a test user ID for isolated testing
TEST_USER_ID = "test_user_kg_relationships"

@pytest.fixture(scope="module")
async def agent():
    """Fixture to initialize and clean up the AgnoPersonalAgent for testing."""
    # Ensure LightRAG memory server is running
    # In a real CI/CD, this would be handled by a service dependency
    print(f"\nAttempting to connect to LightRAG Memory Server at {LIGHTRAG_MEMORY_URL}...")
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{LIGHTRAG_MEMORY_URL}/health", timeout=10) as resp:
                resp.raise_for_status()
        print("LightRAG Memory Server is healthy.")
    except Exception as e:
        pytest.fail(f"LightRAG Memory Server not accessible at {LIGHTRAG_MEMORY_URL}: {e}. Please ensure it is running.")

    # Initialize agent with a specific test user ID
    test_agent = AgnoPersonalAgent(user_id=TEST_USER_ID, debug=True, recreate=True)
    await test_agent.initialize(recreate=True) # Ensure a clean slate for tests
    yield test_agent
    
    # Teardown: Clear memories for the test user
    print(f"\nCleaning up memories for {TEST_USER_ID}...")
    try:
        # Assuming clear_memories tool is available and works
        # If not, you might need a direct call to SemanticMemoryManager or LightRAG API
        clear_memories_tool = None
        for tool in test_agent.agent.tools:
            if getattr(tool, "__name__", "") == "clear_memories":
                clear_memories_tool = tool
                break
        if clear_memories_tool:
            result = await clear_memories_tool()
            print(f"Cleanup result: {result}")
        else:
            print("Clear memories tool not found, manual cleanup might be needed.")
    except Exception as e:
        print(f"Error during cleanup: {e}")

@pytest.mark.asyncio
async def test_store_and_query_relationships(agent: AgnoPersonalAgent):
    """
    Test storing a memory and explicitly querying for extracted entities and relationships
    in the LightRAG knowledge graph.
    """
    print("\n--- Running test_store_and_query_relationships ---")
    memory_content = "Eric works at Google. He lives in Mountain View."
    
    # Store the memory
    print(f"Storing memory: '{memory_content}'")
    store_result = await agent.store_user_memory(content=memory_content, topics=["work", "personal"])
    print(f"Store result: {store_result}")
    assert "Successfully stored graph memory" in store_result
    
    # Give LightRAG some time to process (if async processing is involved)
    time.sleep(5) 
    
    # Query LightRAG directly for graph labels to see if entities/relations are there
    print("\nQuerying LightRAG for graph labels...")
    get_labels_tool = None
    for tool in agent.agent.tools:
        if getattr(tool, "__name__", "") == "get_memory_graph_labels":
            get_labels_tool = tool
            break
    assert get_labels_tool is not None, "get_memory_graph_labels tool not found"
    
    labels_result = await get_labels_tool()
    print(f"Graph labels result: {labels_result}")
    assert "Eric" in labels_result
    assert "Google" in labels_result
    assert "Mountain View" in labels_result
    assert "works at" in labels_result or "WORKS_AT" in labels_result # Depending on how LightRAG normalizes
    assert "lives in" in labels_result or "LIVES_IN" in labels_result
    
    # Query the graph for specific relationships
    print("\nQuerying graph memory for relationships...")
    query_graph_tool = None
    for tool in agent.agent.tools:
        if getattr(tool, "__name__", "") == "query_graph_memory":
            query_graph_tool = tool
            break
    assert query_graph_tool is not None, "query_graph_memory tool not found"
    
    # Test 1: Who works at Google?
    query1 = "Who works at Google?"
    query1_result = await query_graph_tool(query=query1, mode="mix")
    print(f"Query '{query1}' result: {query1_result}")
    assert "Eric" in str(query1_result)
    assert "Google" in str(query1_result)
    
    # Test 2: Where does Eric live?
    query2 = "Where does Eric live?"
    query2_result = await query_graph_tool(query=query2, mode="mix")
    print(f"Query '{query2}' result: {query2_result}")
    assert "Eric" in str(query2_result)
    assert "Mountain View" in str(query2_result)

@pytest.mark.asyncio
async def test_multiple_relationships(agent: AgnoPersonalAgent):
    """
    Test storing multiple memories with different relationships and verifying them.
    """
    print("\n--- Running test_multiple_relationships ---")
    memories = [
        "Emma is a yoga instructor. She teaches classes on Tuesdays.",
        "Max is Emma's dog. Max loves to play fetch.",
        "The bookstore on Main Street sells science fiction novels."
    ]

    for i, memory_content in enumerate(memories):
        print(f"Storing memory {i+1}: '{memory_content}'")
        store_result = await agent.store_user_memory(content=memory_content)
        print(f"Store result: {store_result}")
        assert "Successfully stored graph memory" in store_result
        time.sleep(3) # Give LightRAG some time

    time.sleep(5) # Final wait for all processing

    # Verify entities and relationships
    print("\nQuerying LightRAG for graph labels after multiple memories...")
    get_labels_tool = None
    for tool in agent.agent.tools:
        if getattr(tool, "__name__", "") == "get_memory_graph_labels":
            get_labels_tool = tool
            break
    labels_result = await get_labels_tool()
    print(f"Graph labels result: {labels_result}")
    assert "Emma" in labels_result
    assert "yoga instructor" in labels_result or "YOGA_INSTRUCTOR" in labels_result
    assert "Max" in labels_result
    assert "dog" in labels_result
    assert "bookstore" in labels_result
    assert "Main Street" in labels_result
    assert "sells" in labels_result or "SELLS" in labels_result
    assert "science fiction novels" in labels_result

    query_graph_tool = None
    for tool in agent.agent.tools:
        if getattr(tool, "__name__", "") == "query_graph_memory":
            query_graph_tool = tool
            break

    # Test 1: What is Emma's profession?
    query1 = "What is Emma's profession?"
    query1_result = await query_graph_tool(query=query1, mode="mix")
    print(f"Query '{query1}' result: {query1_result}")
    assert "yoga instructor" in str(query1_result) or "YOGA_INSTRUCTOR" in str(query1_result)

    # Test 2: Who is Max's owner?
    query2 = "Who is Max's owner?"
    query2_result = await query_graph_tool(query=query2, mode="mix")
    print(f"Query '{query2}' result: {query2_result}")
    assert "Emma" in str(query2_result)
    assert "Max" in str(query2_result)

    # Test 3: What does the bookstore sell?
    query3 = "What does the bookstore sell?"
    query3_result = await query_graph_tool(query=query3, mode="mix")
    print(f"Query '{query3}' result: {query3_result}")
    assert "bookstore" in str(query3_result)
    assert "science fiction novels" in str(query3_result)
