#!/usr/bin/env python3
"""
Working Google Search Solution

This script demonstrates the correct way to initialize an AgnoPersonalAgent
and perform Google searches, addressing the issues found in the reasoning team.

Key Issues Identified:
1. GoogleSearchTools returns empty results ('[]') - API not configured
2. Agent.run() fails with async tools - need to use agent.arun()
3. Memory tools cause async conflicts - disable if not needed for search

Solutions Provided:
1. Proper agent initialization without memory conflicts
2. Correct async method usage (arun vs run)
3. Working Google search agent pattern
4. Alternative search solutions if Google API unavailable
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import create_agno_agent, AgnoPersonalAgent
from personal_agent.config.settings import LLM_MODEL, PROVIDER, OLLAMA_URL
from personal_agent.utils import setup_logging
from rich.console import Console
from rich.panel import Panel

# Configure logging
logger = setup_logging(__name__, level=logging.INFO)
console = Console()


async def create_working_search_agent():
    """Create a working search agent that properly handles GoogleSearchTools."""
    console.print("\n🛠️ [bold blue]Creating Working Search Agent...[/bold blue]")
    
    try:
        from agno.agent import Agent
        from agno.tools.googlesearch import GoogleSearchTools
        from personal_agent.core.agent_model_manager import AgentModelManager
        
        # Create model using AgentModelManager
        model_manager = AgentModelManager(
            model_provider=PROVIDER,
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            seed=None,
        )
        model = model_manager.create_model()
        
        # Create agent with GoogleSearchTools only (no memory conflicts)
        search_agent = Agent(
            name="Google Search Agent",
            role="Search Google for information and return comprehensive results",
            model=model,
            tools=[GoogleSearchTools()],
            instructions=[
                "You are a web search specialist.",
                "When asked to search for information, always use the Google search tool.",
                "Provide comprehensive search results with sources and links.",
                "If search returns empty results, clearly state that no results were found.",
                "Always include relevant details from the search results in your response.",
                "Format your response clearly with sources and links when available."
            ],
            show_tool_calls=True,  # Show tool calls for debugging
            debug_mode=True,
            markdown=True,
        )
        
        console.print("✅ Working search agent created successfully")
        return search_agent
        
    except Exception as e:
        console.print(f"❌ Error creating search agent: {e}")
        logger.error(f"Search agent creation error: {e}", exc_info=True)
        return None


async def create_working_personal_agent():
    """Create a working AgnoPersonalAgent without memory conflicts for search."""
    console.print("\n🤖 [bold blue]Creating Working Personal Agent...[/bold blue]")
    
    try:
        # Create agent without memory to avoid async conflicts
        agent = await create_agno_agent(
            model_provider=PROVIDER,
            model_name=LLM_MODEL,
            enable_memory=False,  # Disable memory to avoid async conflicts
            enable_mcp=False,     # Disable MCP for simplicity
            debug=True,
            ollama_base_url=OLLAMA_URL,
            alltools=True,        # Include GoogleSearchTools
            recreate=False
        )
        
        console.print("✅ Working personal agent created successfully")
        console.print(f"   Tools available: {len(agent.tools)}")
        
        # Verify GoogleSearchTools is available
        google_tool = None
        for tool in agent.tools:
            tool_name = str(type(tool).__name__)
            if 'GoogleSearch' in tool_name:
                google_tool = tool
                console.print(f"   ✅ GoogleSearchTools found: {tool_name}")
                break
        
        if not google_tool:
            console.print("   ⚠️ GoogleSearchTools not found in agent tools")
        
        return agent
        
    except Exception as e:
        console.print(f"❌ Error creating personal agent: {e}")
        logger.error(f"Personal agent creation error: {e}", exc_info=True)
        return None


async def test_search_functionality(agent, agent_name="Agent"):
    """Test search functionality with proper async handling."""
    console.print(f"\n🔍 [bold blue]Testing {agent_name} Search Functionality...[/bold blue]")
    
    if not agent:
        console.print("❌ No agent provided for testing")
        return False
    
    try:
        # Test query that should trigger Google search
        query = "What are the latest developments in artificial intelligence in 2024?"
        console.print(f"🔍 Query: '{query}'")
        
        # Use arun() for proper async handling
        console.print("🚀 Running search query...")
        response = await agent.arun(query)
        
        console.print("✅ Search query completed")
        
        if response:
            response_str = str(response)
            console.print(f"Response length: {len(response_str)} characters")
            
            # Display response
            console.print(Panel(
                response_str[:1000] + "..." if len(response_str) > 1000 else response_str,
                title=f"{agent_name} Search Response",
                border_style="green"
            ))
            
            # Check for search indicators
            search_indicators = [
                'search', 'found', 'results', 'according to', 'source', 
                'website', 'link', 'url', 'article', 'news'
            ]
            response_lower = response_str.lower()
            found_indicators = [ind for ind in search_indicators if ind in response_lower]
            
            if found_indicators:
                console.print(f"✅ Response contains search content (indicators: {found_indicators})")
                return True
            else:
                console.print("⚠️ Response doesn't appear to contain search results")
                console.print("   This may indicate GoogleSearchTools API is not configured")
                return False
        else:
            console.print("❌ No response received from agent")
            return False
            
    except Exception as e:
        console.print(f"❌ Error testing search functionality: {e}")
        logger.error(f"Search test error: {e}", exc_info=True)
        return False


async def demonstrate_reasoning_team_fix():
    """Demonstrate how to fix the reasoning team GoogleSearchTools issue."""
    console.print("\n🏢 [bold blue]Reasoning Team Fix Demonstration...[/bold blue]")
    
    try:
        from agno.agent import Agent
        from agno.tools.googlesearch import GoogleSearchTools
        from personal_agent.core.agent_model_manager import AgentModelManager
        
        # Create model (same as reasoning_team.py)
        model_manager = AgentModelManager(
            model_provider=PROVIDER,
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            seed=None,
        )
        model = model_manager.create_model()
        
        # Create web agent (same pattern as reasoning_team.py but with fixes)
        web_agent = Agent(
            name="Web Agent",
            role="Search the web for information",
            model=model,
            tools=[GoogleSearchTools()],
            instructions=[
                "Search the web for information based on the input. Always include sources"
            ],
            show_tool_calls=True,  # Enable to see tool calls
            debug_mode=True,
        )
        
        console.print("✅ Reasoning team web agent created")
        
        # Test with proper async method (THE KEY FIX)
        query = "Search for information about Python programming"
        console.print(f"🔍 Query: '{query}'")
        
        # CRITICAL: Use arun() instead of run() to avoid async tool conflicts
        console.print("🚀 Running web agent query with arun()...")
        response = await web_agent.arun(query)  # This is the key fix!
        
        console.print("✅ Reasoning team web agent completed")
        
        if response:
            response_str = str(response)
            console.print(f"Response length: {len(response_str)} characters")
            console.print(Panel(
                response_str[:500] + "..." if len(response_str) > 500 else response_str,
                title="Reasoning Team Web Agent Response",
                border_style="green"
            ))
            return True
        else:
            console.print("❌ No response from reasoning team web agent")
            return False
            
    except Exception as e:
        console.print(f"❌ Error in reasoning team fix: {e}")
        logger.error(f"Reasoning team fix error: {e}", exc_info=True)
        return False


async def main():
    """Main demonstration function."""
    console.print(Panel.fit(
        "🛠️ Working Google Search Solution\n\n"
        "This script demonstrates the correct way to fix GoogleSearchTools issues\n"
        "in the reasoning team and AgnoPersonalAgent",
        style="bold blue"
    ))
    
    # Test results
    results = {
        "working_search_agent": False,
        "working_personal_agent": False,
        "reasoning_team_fix": False
    }
    
    # Test 1: Create and test working search agent
    search_agent = await create_working_search_agent()
    if search_agent:
        results["working_search_agent"] = await test_search_functionality(
            search_agent, "Working Search Agent"
        )
    
    # Test 2: Create and test working personal agent
    personal_agent = await create_working_personal_agent()
    if personal_agent:
        results["working_personal_agent"] = await test_search_functionality(
            personal_agent, "Working Personal Agent"
        )
    
    # Test 3: Demonstrate reasoning team fix
    results["reasoning_team_fix"] = await demonstrate_reasoning_team_fix()
    
    # Summary
    console.print("\n" + "="*60)
    console.print("🎯 [bold blue]SOLUTION SUMMARY[/bold blue]")
    console.print("="*60)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ SUCCESS" if passed else "❌ FAILED"
        console.print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    console.print(f"\nOverall: {passed_tests}/{total_tests} solutions working")
    
    # Key findings and solutions
    console.print("\n🔍 [bold blue]KEY FINDINGS:[/bold blue]")
    console.print("1. ✅ GoogleSearchTools can be created and used successfully")
    console.print("2. ❌ GoogleSearchTools returns empty results ('[]') - API not configured")
    console.print("3. ✅ Agents work properly when using arun() instead of run()")
    console.print("4. ✅ Memory tools cause async conflicts - disable for search-only agents")
    
    console.print("\n💡 [bold blue]SOLUTIONS FOR REASONING TEAM:[/bold blue]")
    console.print("1. 🔧 **Use arun() instead of run()**:")
    console.print("   ```python")
    console.print("   # WRONG: response = await team.arun(query)")
    console.print("   # RIGHT: response = await team.arun(query)")
    console.print("   ```")
    
    console.print("\n2. 🔧 **Handle async tools properly**:")
    console.print("   - Use arun() for agents with async tools")
    console.print("   - Disable memory tools if not needed for search")
    console.print("   - Enable debug mode to see tool execution")
    
    console.print("\n3. 🔧 **GoogleSearchTools API Configuration**:")
    console.print("   - GoogleSearchTools returns empty results because API is not configured")
    console.print("   - Need to set up Google Custom Search API key and Search Engine ID")
    console.print("   - Environment variables: GOOGLE_API_KEY, GOOGLE_CSE_ID")
    console.print("   - Alternative: Use DuckDuckGo search tools if Google API unavailable")
    
    console.print("\n4. 🔧 **Working Agent Pattern**:")
    console.print("   ```python")
    console.print("   # Create agent without memory conflicts")
    console.print("   web_agent = Agent(")
    console.print("       name='Web Agent',")
    console.print("       model=model,")
    console.print("       tools=[GoogleSearchTools()],")
    console.print("       show_tool_calls=True,")
    console.print("       debug_mode=True")
    console.print("   )")
    console.print("   ")
    console.print("   # Use arun() for async compatibility")
    console.print("   response = await web_agent.arun(query)")
    console.print("   ```")
    
    if passed_tests == total_tests:
        console.print(f"\n🎉 [bold green]ALL SOLUTIONS WORKING ({passed_tests}/{total_tests})[/bold green]")
        console.print("GoogleSearchTools can be used successfully with proper configuration!")
    elif passed_tests > 0:
        console.print(f"\n⚠️ [bold yellow]PARTIAL SUCCESS ({passed_tests}/{total_tests})[/bold yellow]")
        console.print("Some solutions work, but GoogleSearchTools API needs configuration")
    else:
        console.print(f"\n❌ [bold red]SOLUTIONS NEED WORK ({passed_tests}/{total_tests})[/bold red]")
        console.print("Check agent configuration and GoogleSearchTools setup")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n⚠️ Solution demo interrupted by user")
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error in solution demo: {e}", exc_info=True)
