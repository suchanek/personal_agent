#!/usr/bin/env python3
"""
Diagnostic script to test gpt-oss:20b model and capture detailed error information.
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
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gpt_oss_diagnostic.log')
    ]
)

logger = logging.getLogger(__name__)

async def test_gpt_oss_model():
    """Test the gpt-oss:20b model with diagnostic logging."""
    
    logger.info("🔍 Starting diagnostic test for gpt-oss:20b model")
    
    try:
        # Create agent with gpt-oss:20b model
        logger.info("🔍 Creating AgnoPersonalAgent with gpt-oss:20b")
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name="gpt-oss:20b",
            enable_memory=True,
            enable_mcp=False,  # Disable MCP to simplify
            debug=True,  # Enable debug mode
            ollama_base_url=OLLAMA_URL,
            user_id=get_userid(),
            alltools=True,  # Enable all tools to reproduce the issue
        )
        
        logger.info("🔍 Agent created successfully")
        
        # Test with a simple query that should trigger tool usage
        test_query = "What is 2 + 2?"
        logger.info(f"🔍 Testing with query: {test_query}")
        
        # This should trigger the error - using native Agent methods
        response = await agent.run(test_query)
        
        logger.info(f"🔍 Response received: {response[:100]}...")
        logger.info("🔍 Test completed successfully - no error occurred!")
        
        return True
        
    except Exception as e:
        logger.error("🔍 ERROR CAUGHT IN TEST:")
        logger.error(f"🔍 Error type: {type(e)}")
        logger.error(f"🔍 Error message: {str(e)}")
        logger.error("🔍 Full traceback:", exc_info=True)
        
        # Additional diagnostic information
        if hasattr(agent, 'model_name'):
            logger.error(f"🔍 Model name: {agent.model_name}")
        if hasattr(agent, 'tools'):
            logger.error(f"🔍 Number of tools: {len(agent.tools) if agent.tools else 0}")
            if agent.tools:
                tool_names = []
                for tool in agent.tools:
                    tool_name = getattr(tool, 'name', type(tool).__name__)
                    tool_names.append(tool_name)
                logger.error(f"🔍 Tool names: {tool_names}")
        
        return False

async def test_working_model():
    """Test with a known working model for comparison."""
    
    logger.info("🔍 Testing with known working model (qwen3:8b) for comparison")
    
    try:
        # Create agent with working model
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name="qwen3:8b",
            enable_memory=True,
            enable_mcp=False,
            debug=True,
            ollama_base_url=OLLAMA_URL,
            user_id=get_userid(),
            alltools=True,
        )
        
        # Test with same query
        test_query = "What is 2 + 2?"
        response = await agent.run(test_query)
        
        logger.info(f"🔍 Working model response: {response[:100]}...")
        logger.info("🔍 Working model test completed successfully")
        
        return True
        
    except Exception as e:
        logger.error("🔍 ERROR with working model:")
        logger.error(f"🔍 Error: {str(e)}")
        return False

async def main():
    """Main test function."""
    
    logger.info("🔍 Starting comprehensive diagnostic test")
    
    # Test 1: Try the problematic model
    logger.info("=" * 60)
    logger.info("TEST 1: gpt-oss:20b model")
    logger.info("=" * 60)
    
    gpt_oss_success = await test_gpt_oss_model()
    
    # Test 2: Try a working model for comparison
    logger.info("=" * 60)
    logger.info("TEST 2: qwen3:8b model (control)")
    logger.info("=" * 60)
    
    qwen_success = await test_working_model()
    
    # Summary
    logger.info("=" * 60)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("=" * 60)
    logger.info(f"gpt-oss:20b test: {'SUCCESS' if gpt_oss_success else 'FAILED'}")
    logger.info(f"qwen3:8b test: {'SUCCESS' if qwen_success else 'FAILED'}")
    
    if not gpt_oss_success and qwen_success:
        logger.info("🔍 CONCLUSION: Issue is specific to gpt-oss:20b model")
    elif not gpt_oss_success and not qwen_success:
        logger.info("🔍 CONCLUSION: Issue affects multiple models - likely framework problem")
    elif gpt_oss_success:
        logger.info("🔍 CONCLUSION: gpt-oss:20b is working - issue may be intermittent")

if __name__ == "__main__":
    asyncio.run(main())
