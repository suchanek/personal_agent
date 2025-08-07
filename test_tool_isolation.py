#!/usr/bin/env python3
"""
Tool isolation test to identify which specific tool causes the gpt-oss:20b template error.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the path for imports
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.config.settings import get_userid, OLLAMA_URL

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def test_with_specific_tools(tool_names, model_name="gpt-oss:20b"):
    """Test the model with specific tools enabled."""
    
    logger.info(f"🔍 Testing {model_name} with tools: {tool_names}")
    
    try:
        # Create agent with specific tools
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=model_name,
            enable_memory=False,  # Disable memory to isolate tool issues
            enable_mcp=False,
            debug=True,
            ollama_base_url=OLLAMA_URL,
            user_id=get_userid(),
            alltools=True,  # We'll manually filter tools
        )
        
        # Initialize the agent
        await agent._ensure_initialized()
        
        # Filter tools to only include the ones we want to test
        if tool_names:
            filtered_tools = []
            for tool in agent.tools:
                tool_class_name = type(tool).__name__
                if any(name.lower() in tool_class_name.lower() for name in tool_names):
                    filtered_tools.append(tool)
            agent.tools = filtered_tools
            logger.info(f"🔍 Filtered to {len(filtered_tools)} tools: {[type(t).__name__ for t in filtered_tools]}")
        else:
            agent.tools = []
            logger.info("🔍 Testing with NO tools")
        
        # Test with a simple query
        test_query = "What is 2 + 2?"
        response = await agent.run(test_query)
        
        logger.info(f"✅ SUCCESS with tools {tool_names}: {response[:50]}...")
        return True
        
    except Exception as e:
        logger.error(f"❌ FAILED with tools {tool_names}: {str(e)}")
        return False

async def main():
    """Main test function to isolate problematic tools."""
    
    logger.info("🔍 Starting tool isolation test for gpt-oss:20b")
    
    # Test 1: No tools at all
    logger.info("=" * 60)
    logger.info("TEST 1: No tools")
    logger.info("=" * 60)
    no_tools_success = await test_with_specific_tools([])
    
    if not no_tools_success:
        logger.error("❌ Even with no tools, the model fails. This is a deeper issue.")
        return
    
    # Test 2: Individual tool categories
    tool_categories = [
        ["GoogleSearch"],
        ["Calculator"],
        ["YFinance"],
        ["Python"],
        ["Shell"],
        ["PersonalAgent"],
    ]
    
    results = {}
    
    for tools in tool_categories:
        logger.info("=" * 60)
        logger.info(f"TEST: {tools}")
        logger.info("=" * 60)
        success = await test_with_specific_tools(tools)
        results[str(tools)] = success
        
        if not success:
            logger.error(f"❌ Found problematic tool category: {tools}")
            break
    
    # Summary
    logger.info("=" * 60)
    logger.info("TOOL ISOLATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"No tools: {'SUCCESS' if no_tools_success else 'FAILED'}")
    
    for tools, success in results.items():
        logger.info(f"{tools}: {'SUCCESS' if success else 'FAILED'}")
    
    # Find the first failing tool
    failing_tools = [tools for tools, success in results.items() if not success]
    if failing_tools:
        logger.info(f"🔍 CONCLUSION: First failing tool category: {failing_tools[0]}")
    else:
        logger.info("🔍 CONCLUSION: All individual tool categories work - issue may be with combinations")

if __name__ == "__main__":
    asyncio.run(main())
