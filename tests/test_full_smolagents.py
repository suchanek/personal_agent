#!/usr/bin/env python3
"""Test full smolagents integration with all tools."""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))


def test_full_smolagents():
    """Test complete smolagents setup with all tools."""
    try:
        from personal_agent.config import USE_WEAVIATE, get_mcp_servers
        from personal_agent.core.mcp_client import SimpleMCPClient
        from personal_agent.core.smol_agent import create_smolagents_executor
        from personal_agent.utils.cleanup import setup_logging

        logger = setup_logging()
        logger.info("🚀 Testing full smolagents integration")

        # Initialize MCP client
        mcp_servers = get_mcp_servers()
        mcp_client = SimpleMCPClient(mcp_servers)
        logger.info("📡 Initialized MCP client with %d servers", len(mcp_servers))

        # Start MCP servers
        if not mcp_client.start_servers():
            logger.error("❌ Failed to start MCP servers")
            return False
        logger.info("✅ Started MCP servers successfully")

        # Initialize memory components if available
        weaviate_client = None
        vector_store = None
        if USE_WEAVIATE:
            try:
                from personal_agent.core.memory import vector_store, weaviate_client

                logger.info("🧠 Loaded Weaviate memory components")
            except ImportError as e:
                logger.warning("⚠️  Could not load Weaviate components: %s", e)

        # Create smolagents agent with all dependencies
        agent = create_smolagents_executor(
            mcp_client=mcp_client,
            weaviate_client=weaviate_client,
            vector_store=vector_store,
        )
        logger.info("🤖 Created smolagents agent with complete tool set")

        # Test comprehensive functionality
        test_queries = [
            "List the contents of the current directory",
            "Search for 'smolagents' on the web",
            "Search GitHub repositories for 'langchain alternative'",
        ]

        for i, query in enumerate(test_queries, 1):
            logger.info(f"🔍 Test {i}/3: {query}")
            try:
                result = agent.run(query)
                logger.info(f"✅ Test {i} completed")
                logger.info(f"📊 Result preview: {str(result)[:200]}...")
                print(f"\n=== Test {i} Result ===")
                print(result)
                print("=" * 50)
            except Exception as e:
                logger.error(f"❌ Test {i} failed: {e}")
                continue

        logger.info("🎉 Full smolagents testing completed")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        # Cleanup
        try:
            if "mcp_client" in locals():
                mcp_client.cleanup()
                print("🧹 Cleaned up MCP client")
        except:
            pass


if __name__ == "__main__":
    success = test_full_smolagents()
    sys.exit(0 if success else 1)
