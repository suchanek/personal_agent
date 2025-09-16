#!/usr/bin/env python3
"""
Test script to initialize AgnoPersonalAgent properly and test GoogleSearchTools functionality.

This script creates a properly initialized AgnoPersonalAgent with GoogleSearchTools
and performs a test search to verify the tools are working correctly.

Usage:
    python test_google_search_agent.py
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
from rich.table import Table

# Configure logging
logger = setup_logging(__name__, level=logging.DEBUG)
console = Console()


async def test_google_search_direct():
    """Test GoogleSearchTools directly without agent."""
    console.print("\n🔍 [bold blue]Testing GoogleSearchTools directly...[/bold blue]")
    
    try:
        from agno.tools.googlesearch import GoogleSearchTools
        
        # Create GoogleSearchTools instance
        search_tools = GoogleSearchTools()
        console.print("✅ GoogleSearchTools instance created successfully")
        
        # Test search functionality
        query = "Python programming language"
        console.print(f"🔍 Searching for: '{query}'")
        
        # Get the search method
        if hasattr(search_tools, 'search_google'):
            search_method = search_tools.search_google
        elif hasattr(search_tools, 'google_search'):
            search_method = search_tools.google_search
        else:
            # Try to find any search method
            search_methods = [attr for attr in dir(search_tools) if 'search' in attr.lower()]
            console.print(f"Available search methods: {search_methods}")
            if search_methods:
                search_method = getattr(search_tools, search_methods[0])
            else:
                console.print("❌ No search method found in GoogleSearchTools")
                return False
        
        # Perform the search
        try:
            result = search_method(query)
            console.print("✅ Direct GoogleSearchTools search completed")
            console.print(f"Result type: {type(result)}")
            console.print(f"Result length: {len(str(result)) if result else 0}")
            
            if result:
                console.print(Panel(str(result)[:500] + "..." if len(str(result)) > 500 else str(result), 
                                  title="Search Results", border_style="green"))
                return True
            else:
                console.print("❌ No results returned from direct search")
                return False
                
        except Exception as e:
            console.print(f"❌ Error during direct search: {e}")
            logger.error(f"Direct search error: {e}", exc_info=True)
            return False
            
    except ImportError as e:
        console.print(f"❌ Failed to import GoogleSearchTools: {e}")
        return False
    except Exception as e:
        console.print(f"❌ Error testing GoogleSearchTools directly: {e}")
        logger.error(f"Direct GoogleSearchTools test error: {e}", exc_info=True)
        return False


async def test_agent_initialization():
    """Test proper AgnoPersonalAgent initialization."""
    console.print("\n🤖 [bold blue]Testing AgnoPersonalAgent initialization...[/bold blue]")
    
    try:
        # Method 1: Using create_agno_agent function (recommended)
        console.print("📝 Creating agent using create_agno_agent()...")
        agent = await create_agno_agent(
            model_provider=PROVIDER,
            model_name=LLM_MODEL,
            enable_memory=True,
            enable_mcp=False,  # Disable MCP for simpler testing
            debug=True,
            ollama_base_url=OLLAMA_URL,
            alltools=True,  # Ensure all tools including GoogleSearchTools are enabled
            recreate=False
        )
        
        console.print("✅ Agent created successfully")
        
        # Check if agent is properly initialized
        if agent._initialized:
            console.print("✅ Agent is properly initialized")
        else:
            console.print("⚠️ Agent not initialized, forcing initialization...")
            await agent._ensure_initialized()
            console.print("✅ Agent initialization completed")
        
        # Check tools
        if hasattr(agent, 'tools') and agent.tools:
            console.print(f"✅ Agent has {len(agent.tools)} tools loaded")
            
            # Look for GoogleSearchTools
            google_tools = []
            for tool in agent.tools:
                tool_name = getattr(tool, 'name', str(type(tool).__name__))
                if 'google' in tool_name.lower() or 'search' in tool_name.lower():
                    google_tools.append(tool_name)
            
            if google_tools:
                console.print(f"✅ Found Google search tools: {google_tools}")
            else:
                console.print("⚠️ No Google search tools found in agent tools")
                # List all tools for debugging
                tool_names = [getattr(tool, 'name', str(type(tool).__name__)) for tool in agent.tools]
                console.print(f"Available tools: {tool_names}")
        else:
            console.print("❌ Agent has no tools loaded")
            return None
        
        return agent
        
    except Exception as e:
        console.print(f"❌ Failed to initialize agent: {e}")
        logger.error(f"Agent initialization error: {e}", exc_info=True)
        return None


async def test_agent_google_search(agent):
    """Test Google search through the agent."""
    console.print("\n🔍 [bold blue]Testing Google search through agent...[/bold blue]")
    
    if not agent:
        console.print("❌ No agent provided for testing")
        return False
    
    try:
        # Test query
        query = "What is the latest news about artificial intelligence?"
        console.print(f"🔍 Agent query: '{query}'")
        
        # Run the query through the agent
        console.print("🚀 Running agent query...")
        response = await agent.run(query, stream=False)
        
        console.print("✅ Agent query completed")
        console.print(f"Response type: {type(response)}")
        console.print(f"Response length: {len(str(response)) if response else 0}")
        
        if response and str(response).strip():
            console.print(Panel(str(response), title="Agent Response", border_style="green"))
            
            # Check if the response contains search results
            response_str = str(response).lower()
            search_indicators = ['search', 'found', 'results', 'according to', 'source', 'website']
            has_search_content = any(indicator in response_str for indicator in search_indicators)
            
            if has_search_content:
                console.print("✅ Response appears to contain search results")
                return True
            else:
                console.print("⚠️ Response doesn't appear to contain search results")
                return False
        else:
            console.print("❌ No response or empty response from agent")
            return False
            
    except Exception as e:
        console.print(f"❌ Error during agent search test: {e}")
        logger.error(f"Agent search test error: {e}", exc_info=True)
        return False


async def test_agent_tool_calls(agent):
    """Test and display tool calls from the agent."""
    console.print("\n🛠️ [bold blue]Testing agent tool calls...[/bold blue]")
    
    if not agent:
        console.print("❌ No agent provided for testing")
        return False
    
    try:
        # Simple query that should trigger Google search
        query = "Search for information about Python programming"
        console.print(f"🔍 Tool call test query: '{query}'")
        
        # Run the query
        response = await agent.run(query, stream=False)
        
        # Get tool calls from the last run
        tool_calls = agent.get_last_tool_calls()
        
        if tool_calls:
            console.print(f"✅ Found {len(tool_calls)} tool calls")
            
            # Display tool calls in a table
            table = Table(title="Tool Calls", show_header=True, header_style="bold magenta")
            table.add_column("Tool", style="cyan")
            table.add_column("Function", style="yellow")
            table.add_column("Arguments", style="green")
            
            for i, tool_call in enumerate(tool_calls):
                tool_name = getattr(tool_call, 'name', f'Tool-{i}')
                function_name = getattr(tool_call, 'function', {}).get('name', 'Unknown') if hasattr(tool_call, 'function') else 'Unknown'
                arguments = str(getattr(tool_call, 'function', {}).get('arguments', 'None') if hasattr(tool_call, 'function') else 'None')
                
                table.add_row(tool_name, function_name, arguments[:100] + "..." if len(arguments) > 100 else arguments)
            
            console.print(table)
            
            # Check for Google search tool calls
            google_calls = [tc for tc in tool_calls if 'google' in str(tc).lower() or 'search' in str(tc).lower()]
            if google_calls:
                console.print(f"✅ Found {len(google_calls)} Google search tool calls")
                return True
            else:
                console.print("⚠️ No Google search tool calls found")
                return False
        else:
            console.print("❌ No tool calls found")
            return False
            
    except Exception as e:
        console.print(f"❌ Error testing tool calls: {e}")
        logger.error(f"Tool calls test error: {e}", exc_info=True)
        return False


async def main():
    """Main test function."""
    console.print(Panel.fit(
        "🧪 Google Search Agent Test Suite\n\n"
        "This script tests GoogleSearchTools functionality in AgnoPersonalAgent",
        style="bold blue"
    ))
    
    # Test results
    results = {
        "direct_google_search": False,
        "agent_initialization": False,
        "agent_google_search": False,
        "agent_tool_calls": False
    }
    
    # Test 1: Direct GoogleSearchTools test
    results["direct_google_search"] = await test_google_search_direct()
    
    # Test 2: Agent initialization
    agent = await test_agent_initialization()
    results["agent_initialization"] = agent is not None
    
    if agent:
        # Test 3: Google search through agent
        results["agent_google_search"] = await test_agent_google_search(agent)
        
        # Test 4: Tool calls analysis
        results["agent_tool_calls"] = await test_agent_tool_calls(agent)
        
        # Print agent info for debugging
        console.print("\n📊 [bold blue]Agent Information:[/bold blue]")
        agent.print_agent_info(console)
        
        # Cleanup
        try:
            await agent.cleanup()
            console.print("✅ Agent cleanup completed")
        except Exception as e:
            console.print(f"⚠️ Agent cleanup warning: {e}")
    
    # Summary
    console.print("\n" + "="*60)
    console.print("📋 [bold blue]TEST RESULTS SUMMARY[/bold blue]")
    console.print("="*60)
    
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Test", style="cyan")
    summary_table.add_column("Status", style="green")
    summary_table.add_column("Result", style="yellow")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        result = "Success" if passed else "Failed"
        summary_table.add_row(test_name.replace("_", " ").title(), status, result)
    
    console.print(summary_table)
    
    # Overall result
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    if passed_tests == total_tests:
        console.print(f"\n🎉 [bold green]ALL TESTS PASSED ({passed_tests}/{total_tests})[/bold green]")
        console.print("GoogleSearchTools is working correctly!")
    elif passed_tests > 0:
        console.print(f"\n⚠️ [bold yellow]PARTIAL SUCCESS ({passed_tests}/{total_tests})[/bold yellow]")
        console.print("Some tests passed, but there may be issues with GoogleSearchTools")
    else:
        console.print(f"\n❌ [bold red]ALL TESTS FAILED ({passed_tests}/{total_tests})[/bold red]")
        console.print("GoogleSearchTools is not working correctly")
    
    # Recommendations
    console.print("\n💡 [bold blue]RECOMMENDATIONS:[/bold blue]")
    if not results["direct_google_search"]:
        console.print("• Check if GoogleSearchTools is properly installed and configured")
        console.print("• Verify Google Search API credentials if required")
    
    if not results["agent_initialization"]:
        console.print("• Check agent configuration and dependencies")
        console.print("• Verify Ollama/OpenAI model availability")
    
    if not results["agent_google_search"]:
        console.print("• Check if GoogleSearchTools is included in agent tools")
        console.print("• Verify agent instructions include search capabilities")
    
    if not results["agent_tool_calls"]:
        console.print("• Enable debug mode to see tool call details")
        console.print("• Check if agent is properly configured to use tools")


if __name__ == "__main__":
    # Set up environment
    console.print("🔧 Setting up test environment...")
    
    # Check for required environment variables
    required_env_vars = []
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        console.print(f"⚠️ Missing environment variables: {missing_vars}")
        console.print("Some tests may not work properly without proper configuration")
    
    # Run the tests
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        console.print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
