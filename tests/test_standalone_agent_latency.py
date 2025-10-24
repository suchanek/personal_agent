import asyncio
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from langfuse import Langfuse, observe

from src.personal_agent.core.agent_instruction_manager import InstructionLevel
from src.personal_agent.core.agno_agent import AgnoPersonalAgent

# Debug: Print environment variables to validate they're loaded
print("=== LANGFUSE ENVIRONMENT VARIABLES DEBUG ===")
print(f"LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST', 'NOT SET')}")
print(f"LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY', 'NOT SET')}")
print(
    f"LANGFUSE_SECRET_KEY: {'SET' if os.getenv('LANGFUSE_SECRET_KEY') else 'NOT SET'}"
)
print("=" * 50)

# Initialize Langfuse client using environment variables
langfuse = Langfuse()  # Will automatically use LANGFUSE_* environment variables

# Debug: Print Langfuse client configuration
print("=== LANGFUSE CLIENT CONFIGURATION DEBUG ===")
print(f"Langfuse client host: {getattr(langfuse, 'base_url', 'UNKNOWN')}")
print(f"Langfuse client public key: {getattr(langfuse, 'public_key', 'UNKNOWN')}")
print("=" * 50)


@observe(name="Agent Initialization", as_type="generation")
async def initialize_agent():
    """Initialize the agent with tracing"""
    agent = await AgnoPersonalAgent.create_with_init(
        # Using default parameters which should be sufficient for the test
        # Ensure memory is enabled to get a realistic performance measure
        enable_memory=True,
        debug=True,  # Keep debug off to not pollute output and affect performance
        # model_name="qwen3:1.7b",
        instruction_level=InstructionLevel.EXPLICIT,
        alltools=True,
    )
    return agent


@observe(name="Agent Query", as_type="generation")
async def run_agent_query(agent, query):
    """Run a single agent query with tracing"""
    response = await agent.run(query)
    
    # Handle streaming response - collect all chunks
    if hasattr(response, '__aiter__'):
        content_chunks = []
        async for chunk in response:
            if hasattr(chunk, 'content') and chunk.content:
                content_chunks.append(chunk.content)
        return ''.join(content_chunks)
    elif hasattr(response, 'content'):
        return response.content
    else:
        return str(response)


@observe(name="Standalone Agent Latency Test")
async def main():
    """
    Initializes the standalone agent, runs a series of queries,
    and measures the latency for each.
    """
    print("--- Standalone Agent Latency Test ---")
    print("Initializing agent...")

    # Record initialization time
    init_start_time = time.perf_counter()

    # Use the async factory to create and initialize the agent
    # This ensures all components are loaded before we start querying
    try:
        agent = await initialize_agent()
    except Exception as e:
        print(f"Error during agent initialization: {e}")
        return

    init_end_time = time.perf_counter()
    init_latency = init_end_time - init_start_time
    print(f"Agent initialized in {init_latency:.2f} seconds.\n")

    queries = [
        "Hello, who are you?",
        "Hello, who are you?",
        "What is the capital of France?",
        "list all memories. do not interpret, just list them",
        "search the web for the most popular person in the world. list them. do not interpret, just list them",
        "Calculate the square root of 256.",
        "write a poem about love and friendship.",
    ]

    latencies = []

    for i, query in enumerate(queries):
        print(f"--- Query {i+1}/{len(queries)} ---")
        print(f"Query: {query}")

        start_time = time.perf_counter()

        try:
            response = await run_agent_query(agent, query)
        except Exception as e:
            print(f"Error running query: {e}")
            response = "Error"

        end_time = time.perf_counter()
        latency = end_time - start_time
        latencies.append(latency)

        print(f"Response: {response}")
        print(f"Latency: {latency:.2f} seconds\n")
        # A small delay to prevent overwhelming the server, though likely not necessary for local Ollama
        await asyncio.sleep(1)

    if latencies:
        average_latency = sum(latencies) / len(latencies)
        print("--- Test Summary ---")
        print(f"Average query latency: {average_latency:.2f} seconds")
        print(f"Total queries: {len(latencies)}")
        print(
            f"Total time (including delays): {sum(latencies) + len(latencies) -1:.2f} seconds"
        )
        print("--------------------")
    else:
        print("No queries were successfully executed.")


if __name__ == "__main__":
    # This allows running the script directly
    # Ensure you have the necessary environment variables and services (like Ollama) running
    try:
        asyncio.run(main())

        # Debug: Test Langfuse connection before flushing
        print("\n🔍 LANGFUSE INTEGRATION STATUS:")
        print("Latency test completed with Langfuse tracing enabled.")
        print("To view traces and performance metrics:")
        print("1. Go to http://localhost:3000 → Traces")
        print("2. Look for 'Standalone Agent Latency Test' traces")
        print("3. Analyze initialization and query performance")
        print("\nCurrent Langfuse configuration:")
        print(f"  LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST', 'NOT SET')}")
        print(f"  LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY', 'NOT SET')}")
        print(
            f"  LANGFUSE_SECRET_KEY: {'SET' if os.getenv('LANGFUSE_SECRET_KEY') else 'NOT SET'}"
        )
        print("=" * 50)

        # Flush to ensure data is sent
        print("Flushing traces to Langfuse...")
        langfuse.flush()
        print("Traces flushed to Langfuse server.")
        print(
            "Check Langfuse at http://localhost:3000 for detailed performance traces."
        )

        time.sleep(2)  # Wait for flush to complete

    except KeyboardInterrupt:
        print("\nTest cancelled by user.")
        # Still try to flush any collected traces
        try:
            langfuse.flush()
        except:
            pass
    except Exception as e:
        print(f"Error during test execution: {e}")
        # Still try to flush any collected traces
        try:
            langfuse.flush()
        except:
            pass
