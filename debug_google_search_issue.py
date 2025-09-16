#!/usr/bin/env python3
"""
Debug script to identify and fix GoogleSearchTools issues.

This script focuses on diagnosing why GoogleSearchTools might not be returning results
in the reasoning team and provides solutions.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import create_agno_agent
from personal_agent.config.settings import LLM_MODEL, PROVIDER, OLLAMA_URL
from personal_agent.utils import setup_logging
from rich.console import Console
from rich.panel import Panel

# Configure logging
logger = setup_logging(__name__, level=logging.DEBUG)
console = Console()


async def test_googlesearch_tools_directly():
    """Test GoogleSearchTools directly to see if it works."""
    console.print("\n🔍 [bold blue]Testing GoogleSearchTools directly...[/bold blue]")
    
    try:
        from agno.tools.googlesearch import GoogleSearchTools
        
        # Create instance
        search_tools = GoogleSearchTools()
        console.print("✅ GoogleSearchTools instance created")
        
        # Check available methods
        methods = [method for method in dir(search_tools) if not method.startswith('_')]
        console.print(f"Available methods: {methods}")
        
        # Try to find the search method
        search_method = None
        for method_name in ['search_google', 'google_search', 'search']:
            if hasattr(search_tools, method_name):
                search_method = getattr(search_tools, method_name)
                console.print(f"Found search method: {method_name}")
                break
        
        if not search_method:
            console.print("❌ No search method found")
            return False
        
        # Test the search
        query = "Python programming"
        console.print(f"🔍 Testing search with query: '{query}'")
        
        try:
            result = search_method(query)
            console.print(f"✅ Search completed. Result type: {type(result)}")
            
            if result:
                result_str = str(result)
                console.print(f"Result length: {len(result_str)}")
                console.print(Panel(result_str[:300] + "..." if len(result_str) > 300 else result_str, 
                                  title="Search Results", border_style="green"))
                return True
            else:
                console.print("❌ Search returned empty result")
                return False
                
        except Exception as e:
            console.print(f"❌ Search failed: {e}")
            logger.error(f"Search error: {e}", exc_info=True)
            return False
            
    except ImportError as e:
        console.print(f"❌ Failed to import GoogleSearchTools: {e}")
        return False
    except Exception as e:
        console.print(f"❌ Error: {e}")
        logger.error(f"GoogleSearchTools test error: {e}", exc_info=True)
        return False


async def test_agent_with_async_run():
    """Test agent using arun() instead of run() to handle async tools."""
    console.print("\n🤖 [bold blue]Testing agent with async run (arun)...[/bold blue]")
    
    try:
        # Create agent with memory disabled to avoid async tool issues
        agent = await create_agno_agent(
            model_provider=PROVIDER,
            model_name=LLM_MODEL,
            enable_memory=False,  # Disable memory to avoid async tools
            enable_mcp=False,
            debug=True,
            ollama_base_url=OLLAMA_URL,
            alltools=True,
            recreate=False
        )
        
        console.print("✅ Agent created (memory disabled)")
        
        # Check tools
        google_tool = None
        for tool in agent.tools:
            tool_name = str(type(tool).__name__)
            if 'GoogleSearch' in tool_name:
                google_tool = tool
                console.print(f"✅ Found GoogleSearchTools: {tool_name}")
                break
        
        if not google_tool:
            console.print("❌ GoogleSearchTools not found")
            return False
        
        # Test with explicit search query using arun()
        query = "Search Google for information about artificial intelligence"
        console.print(f"🔍 Query: '{query}'")
        
        # Use arun() for async compatibility
        console.print("🚀 Running agent query with arun()...")
        response = await agent.arun(query)
        
        console.print("✅ Agent response received")
        console.print(f"Response type: {type(response)}")
        
        if response:
            response_str = str(response)
            console.print(f"Response length: {len(response_str)}")
            console.print(Panel(response_str, title="Agent Response", border_style="green"))
            
            # Check for search indicators
            search_indicators = ['search', 'found', 'results', 'according to', 'source']
            has_search = any(indicator in response_str.lower() for indicator in search_indicators)
            
            if has_search:
                console.print("✅ Response contains search results")
                return True
            else:
                console.print("⚠️ Response doesn't appear to contain search results")
                return False
        else:
            console.print("❌ No response from agent")
            return False
            
    except Exception as e:
        console.print(f"❌ Error testing agent: {e}")
        logger.error(f"Agent test error: {e}", exc_info=True)
        return False


async def test_reasoning_team_pattern():
    """Test the same pattern used in reasoning_team.py"""
    console.print("\n🏢 [bold blue]Testing reasoning team pattern...[/bold blue]")
    
    try:
        from agno.agent import Agent
        from agno.tools.googlesearch import GoogleSearchTools
        from personal_agent.core.agent_model_manager import AgentModelManager
        
        # Create model using the same pattern as reasoning_team.py
        model_manager = AgentModelManager(
            model_provider=PROVIDER,
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            seed=None,
        )
        model = model_manager.create_model()
        
        # Create agent with GoogleSearchTools (same as reasoning_team.py)
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
        
        console.print("✅ Web agent created (reasoning team pattern)")
        
        # Test with arun() to avoid async tool issues
        query = "Search for latest news about Python programming"
        console.print(f"🔍 Query: '{query}'")
        
        console.print("🚀 Running web agent query...")
        response = await web_agent.arun(query)
        
        console.print("✅ Web agent response received")
        console.print(f"Response type: {type(response)}")
        
        if response:
            response_str = str(response)
            console.print(f"Response length: {len(response_str)}")
            console.print(Panel(response_str, title="Web Agent Response", border_style="green"))
            
            # Check for search content
            search_indicators = ['search', 'found', 'results', 'according to', 'source', 'website']
            has_search = any(indicator in response_str.lower() for indicator in search_indicators)
            
            if has_search:
                console.print("✅ Web agent successfully performed search")
                return True
            else:
                console.print("⚠️ Web agent response doesn't contain search results")
                return False
        else:
            console.print("❌ No response from web agent")
            return False
            
    except Exception as e:
        console.print(f"❌ Error testing reasoning team pattern: {e}")
        logger.error(f"Reasoning team pattern error: {e}", exc_info=True)
        return False


async def create_working_google_search_agent():
    """Create a working Google search agent with proper configuration."""
    console.print("\n🛠️ [bold blue]Creating working Google search agent...[/bold blue]")
    
    try:
        from agno.agent import Agent
        from agno.tools.googlesearch import GoogleSearchTools
        from personal_agent.core.agent_model_manager import AgentModelManager
        
        # Create model
        model_manager = AgentModelManager(
            model_provider=PROVIDER,
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            seed=None,
        )
        model = model_manager.create_model()
        
        # Create simple agent with only GoogleSearchTools
        search_agent = Agent(
            name="Google Search Agent",
            role="Search Google for information and return results",
            model=model,
            tools=[GoogleSearchTools()],
            instructions=[
                "You are a web search agent.",
                "When asked to search for information, use the Google search tool.",
                "Always provide the search results you find.",
                "Include sources and links when available.",
                "If the search returns empty results, mention that no results were found."
            ],
            show_tool_calls=True,
            debug_mode=True,
            markdown=True,
        )
        
        console.print("✅ Google search agent created")
        
        # Test the agent
        query = "What is Python programming language?"
        console.print(f"🔍 Testing query: '{query}'")
        
        console.print("🚀 Running search agent...")
        response = await search_agent.arun(query)
        
        console.print("✅ Search agent completed")
        
        if response:
            response_str = str(response)
            console.print(f"Response length: {len(response_str)}")
            console.print(Panel(response_str, title="Working Google Search Agent Response", border_style="green"))
            return search_agent, True
        else:
            console.print("❌ No response from search agent")
            return search_agent, False
            
    except Exception as e:
        console.print(f"❌ Error creating working search agent: {e}")
        logger.error(f"Working search agent error: {e}", exc_info=True)
        return None, False


async def main():
    """Main debug function."""
    console.print(Panel.fit(
        "🔧 Google Search Debug Suite\n\n"
        "This script diagnoses GoogleSearchTools issues and provides solutions",
        style="bold blue"
    ))
    
    # Test results
    results = {
        "direct_google_search": False,
        "agent_async_run": False,
        "reasoning_team_pattern": False,
        "working_search_agent": False
    }
    
    # Test 1: Direct GoogleSearchTools
    results["direct_google_search"] = await test_googlesearch_tools_directly()
    
    # Test 2: Agent with async run
    results["agent_async_run"] = await test_agent_with_async_run()
    
    # Test 3: Reasoning team pattern
    results["reasoning_team_pattern"] = await test_reasoning_team_pattern()
    
    # Test 4: Create working search agent
    working_agent, success = await create_working_google_search_agent()
    results["working_search_agent"] = success
    
    # Summary
    console.print("\n" + "="*60)
    console.print("🔍 [bold blue]DIAGNOSIS SUMMARY[/bold blue]")
    console.print("="*60)
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        console.print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    console.print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    # Diagnosis and recommendations
    console.print("\n🔍 [bold blue]DIAGNOSIS:[/bold blue]")
    
    if not results["direct_google_search"]:
        console.print("❌ GoogleSearchTools returns empty results ('[]')")
        console.print("   This indicates the search API is not configured or not working")
    else:
        console.print("✅ GoogleSearchTools works directly")
    
    if results["agent_async_run"] or results["reasoning_team_pattern"]:
        console.print("✅ Agent can use GoogleSearchTools when configured properly")
    else:
        console.print("❌ Agent cannot use GoogleSearchTools effectively")
    
    console.print("\n💡 [bold blue]RECOMMENDATIONS:[/bold blue]")
    
    if not results["direct_google_search"]:
        console.print("1. 🔧 GoogleSearchTools Configuration:")
        console.print("   • Check if Google Search API key is configured")
        console.print("   • Verify Google Custom Search Engine ID is set")
        console.print("   • Ensure environment variables are properly loaded")
        console.print("   • Consider using alternative search tools if Google API is not available")
    
    console.print("\n2. 🤖 Agent Usage:")
    console.print("   • Use agent.arun() instead of agent.run() for async compatibility")
    console.print("   • Disable memory tools if not needed to avoid async conflicts")
    console.print("   • Enable debug mode and show_tool_calls to see what's happening")
    
    console.print("\n3. 🏢 Reasoning Team Fix:")
    console.print("   • Update reasoning_team.py to use arun() instead of run()")
    console.print("   • Ensure proper async handling in team coordination")
    console.print("   • Consider creating agents without memory tools for simpler search")
    
    # Show working example if available
    if working_agent and results["working_search_agent"]:
        console.print("\n✅ [bold green]WORKING EXAMPLE CREATED[/bold green]")
        console.print("The working_search_agent demonstrates proper GoogleSearchTools usage")
        console.print("Use this pattern in your reasoning team implementation")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n⚠️ Debug interrupted by user")
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error in debug: {e}", exc_info=True)
