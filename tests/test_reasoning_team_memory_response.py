#!/usr/bin/env python3
"""
Test script to properly initialize the reasoning team and capture full response
for the query "list all memories". This script helps diagnose response streaming
issues where the memory agent output might be getting lost.

Author: Personal Agent Team
Version: 1.0.0
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

# Add the src directory to the path so we can import personal_agent modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from rich.console import Console
from rich.panel import Panel
from rich.json import JSON
from rich.table import Table

# Import the reasoning team module
from personal_agent.team.reasoning_team import create_team, cleanup_team
from personal_agent.config.settings import PROVIDER, LLM_MODEL
from personal_agent.utils import setup_logging

# Configure logging for detailed diagnostics
logger = setup_logging(__name__, level=logging.DEBUG)

class ResponseCapture:
    """Captures and analyzes team responses for debugging."""
    
    def __init__(self):
        self.responses = []
        self.tool_calls = []
        self.member_responses = []
        self.streaming_data = []
        
    def capture_response(self, response_type: str, content: str, metadata: dict = None):
        """Capture a response with metadata."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": response_type,
            "content": content,
            "metadata": metadata or {}
        }
        self.responses.append(entry)
        logger.debug(f"📝 Captured {response_type}: {content[:100]}...")
        
    def capture_tool_call(self, agent_name: str, tool_name: str, args: dict, result: str):
        """Capture tool call details."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "tool": tool_name,
            "arguments": args,
            "result": result
        }
        self.tool_calls.append(entry)
        logger.debug(f"🔧 Captured tool call: {agent_name} -> {tool_name}")
        
    def capture_member_response(self, member_name: str, response: str):
        """Capture individual member responses."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "member": member_name,
            "response": response
        }
        self.member_responses.append(entry)
        logger.debug(f"👤 Captured member response: {member_name}")
        
    def get_summary(self) -> dict:
        """Get a summary of all captured data."""
        return {
            "total_responses": len(self.responses),
            "total_tool_calls": len(self.tool_calls),
            "total_member_responses": len(self.member_responses),
            "response_types": list(set(r["type"] for r in self.responses)),
            "agents_involved": list(set(t["agent"] for t in self.tool_calls)),
            "tools_used": list(set(t["tool"] for t in self.tool_calls))
        }


async def test_team_initialization(console: Console, use_remote: bool = False) -> Optional[object]:
    """Test team initialization and return the team object."""
    console.print("🚀 [bold blue]Testing Team Initialization[/bold blue]")
    
    try:
        console.print(f"📋 Configuration:")
        console.print(f"   - Provider: {PROVIDER}")
        console.print(f"   - Model: {LLM_MODEL}")
        console.print(f"   - Remote: {use_remote}")
        
        # Create the team
        console.print("🔄 Creating team...")
        team = await create_team(use_remote=use_remote)
        
        console.print("✅ [bold green]Team created successfully![/bold green]")
        
        # Display team members
        console.print("\n👥 [bold cyan]Team Members:[/bold cyan]")
        if hasattr(team, 'members') and team.members:
            for i, member in enumerate(team.members, 1):
                member_name = getattr(member, 'name', f'Member-{i}')
                member_role = getattr(member, 'role', 'Unknown role')
                console.print(f"   {i}. {member_name}: {member_role}")
        
        return team
        
    except Exception as e:
        console.print(f"❌ [bold red]Team initialization failed:[/bold red] {str(e)}")
        logger.exception("Team initialization error")
        return None


async def test_memory_agent_direct(team, console: Console, capture: ResponseCapture):
    """Test the memory agent directly to see if it works in isolation."""
    console.print("\n🧠 [bold blue]Testing Memory Agent Directly[/bold blue]")
    
    try:
        # Find the memory agent
        memory_agent = None
        if hasattr(team, 'members') and team.members:
            for member in team.members:
                member_name = getattr(member, 'name', '')
                if 'Personal AI Agent' in member_name or 'Memory' in member_name:
                    memory_agent = member
                    break
        
        if not memory_agent:
            console.print("❌ Memory agent not found in team")
            return
            
        console.print(f"✅ Found memory agent: {getattr(memory_agent, 'name', 'Unknown')}")
        
        # Test direct memory agent call
        console.print("🔍 Testing direct memory agent call...")
        
        # Try to call the memory agent directly
        if hasattr(memory_agent, 'arun'):
            response = await memory_agent.arun("list all memories")
            capture.capture_member_response("Memory Agent Direct", str(response))
            console.print("📝 [bold green]Direct Memory Agent Response:[/bold green]")
            console.print(Panel(str(response), title="Memory Agent Direct Response"))
        elif hasattr(memory_agent, 'run'):
            response = memory_agent.run("list all memories")
            capture.capture_member_response("Memory Agent Direct", str(response))
            console.print("📝 [bold green]Direct Memory Agent Response:[/bold green]")
            console.print(Panel(str(response), title="Memory Agent Direct Response"))
        else:
            console.print("❌ Memory agent doesn't have run/arun method")
            
    except Exception as e:
        console.print(f"❌ [bold red]Direct memory agent test failed:[/bold red] {str(e)}")
        logger.exception("Direct memory agent test error")


async def test_team_response_streaming(team, console: Console, capture: ResponseCapture):
    """Test team response with streaming to capture all data."""
    console.print("\n🌊 [bold blue]Testing Team Response with Streaming[/bold blue]")
    
    query = "list all memories"
    console.print(f"📤 Query: '{query}'")
    
    try:
        # Method 1: Using aprint_response with streaming
        console.print("\n🔄 Method 1: aprint_response with streaming")
        
        # Capture the printed output by redirecting stdout temporarily
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        
        with redirect_stdout(captured_output):
            await team.aprint_response(query, stream=True, show_full_reasoning=True)
        
        streaming_response = captured_output.getvalue()
        capture.capture_response("streaming_aprint", streaming_response)
        
        console.print("📝 [bold green]Streaming Response Captured:[/bold green]")
        console.print(Panel(streaming_response, title="Streaming Response"))
        
    except Exception as e:
        console.print(f"❌ [bold red]Streaming test failed:[/bold red] {str(e)}")
        logger.exception("Streaming test error")


async def test_team_response_non_streaming(team, console: Console, capture: ResponseCapture):
    """Test team response without streaming to get structured data."""
    console.print("\n📋 [bold blue]Testing Team Response Non-Streaming[/bold blue]")
    
    query = "list all memories"
    console.print(f"📤 Query: '{query}'")
    
    try:
        # Method 2: Using arun to get structured response
        console.print("\n🔄 Method 2: arun for structured response")
        
        response = await team.arun(query)
        capture.capture_response("non_streaming_arun", str(response))
        
        console.print("📝 [bold green]Non-Streaming Response:[/bold green]")
        console.print(Panel(str(response), title="Non-Streaming Response"))
        
        # Try to extract more details from the response object
        if hasattr(response, '__dict__'):
            console.print("\n🔍 [bold cyan]Response Object Details:[/bold cyan]")
            response_details = {}
            for key, value in response.__dict__.items():
                if not key.startswith('_'):
                    response_details[key] = str(value)[:200] + "..." if len(str(value)) > 200 else str(value)
            
            console.print(JSON(json.dumps(response_details, indent=2)))
            capture.capture_response("response_object_details", json.dumps(response_details, indent=2))
        
    except Exception as e:
        console.print(f"❌ [bold red]Non-streaming test failed:[/bold red] {str(e)}")
        logger.exception("Non-streaming test error")


async def test_team_member_interactions(team, console: Console, capture: ResponseCapture):
    """Test individual team member interactions to see delegation."""
    console.print("\n🤝 [bold blue]Testing Team Member Interactions[/bold blue]")
    
    try:
        # Check if team has member interaction tracking
        if hasattr(team, 'share_member_interactions'):
            console.print(f"📊 Member interaction sharing: {team.share_member_interactions}")
        
        if hasattr(team, 'members') and team.members:
            console.print(f"👥 Team has {len(team.members)} members")
            
            # Try to access member responses if available
            for i, member in enumerate(team.members):
                member_name = getattr(member, 'name', f'Member-{i}')
                console.print(f"   - {member_name}")
                
                # Check if member has recent responses or memory
                if hasattr(member, 'memory') and member.memory:
                    console.print(f"     ✅ Has memory system")
                if hasattr(member, 'tools') and member.tools:
                    console.print(f"     🔧 Has {len(member.tools)} tools")
        
    except Exception as e:
        console.print(f"❌ [bold red]Member interaction test failed:[/bold red] {str(e)}")
        logger.exception("Member interaction test error")


async def analyze_response_patterns(capture: ResponseCapture, console: Console):
    """Analyze captured responses to identify patterns and issues."""
    console.print("\n🔍 [bold blue]Analyzing Response Patterns[/bold blue]")
    
    summary = capture.get_summary()
    
    # Create summary table
    table = Table(title="Response Analysis Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    for key, value in summary.items():
        table.add_row(key.replace('_', ' ').title(), str(value))
    
    console.print(table)
    
    # Look for specific patterns
    console.print("\n🔍 [bold cyan]Pattern Analysis:[/bold cyan]")
    
    # Check for "task is complete" messages
    task_complete_count = 0
    memory_output_count = 0
    
    for response in capture.responses:
        content = response["content"].lower()
        if "task is complete" in content or "task complete" in content:
            task_complete_count += 1
            console.print(f"⚠️  Found 'task complete' in {response['type']}")
        
        if "memory" in content and ("stored" in content or "retrieved" in content or "list" in content):
            memory_output_count += 1
            console.print(f"✅ Found memory-related content in {response['type']}")
    
    console.print(f"\n📊 Pattern Summary:")
    console.print(f"   - 'Task complete' messages: {task_complete_count}")
    console.print(f"   - Memory-related content: {memory_output_count}")
    
    # Show detailed responses if they're short enough
    console.print("\n📝 [bold cyan]Detailed Response Contents:[/bold cyan]")
    for i, response in enumerate(capture.responses, 1):
        console.print(f"\n{i}. {response['type']} ({response['timestamp']}):")
        content = response['content']
        if len(content) > 500:
            console.print(f"   {content[:500]}... [truncated, {len(content)} total chars]")
        else:
            console.print(f"   {content}")


async def save_diagnostic_report(capture: ResponseCapture, console: Console):
    """Save a detailed diagnostic report to file."""
    console.print("\n💾 [bold blue]Saving Diagnostic Report[/bold blue]")
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"memory_response_diagnostic_{timestamp}.json"
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": capture.get_summary(),
            "responses": capture.responses,
            "tool_calls": capture.tool_calls,
            "member_responses": capture.member_responses
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        console.print(f"✅ Diagnostic report saved to: {report_file}")
        
    except Exception as e:
        console.print(f"❌ [bold red]Failed to save diagnostic report:[/bold red] {str(e)}")
        logger.exception("Diagnostic report save error")


async def main():
    """Main test function."""
    console = Console(force_terminal=True)
    
    console.print("🧪 [bold blue]Reasoning Team Memory Response Test[/bold blue]")
    console.print("=" * 60)
    
    # Initialize response capture
    capture = ResponseCapture()
    
    # Test with both local and remote if needed
    use_remote = False  # Change to True to test remote
    
    try:
        # Step 1: Initialize team
        team = await test_team_initialization(console, use_remote=use_remote)
        if not team:
            console.print("❌ Cannot proceed without team initialization")
            return
        
        # Step 2: Test memory agent directly
        await test_memory_agent_direct(team, console, capture)
        
        # Step 3: Test team response with streaming
        await test_team_response_streaming(team, console, capture)
        
        # Step 4: Test team response without streaming
        await test_team_response_non_streaming(team, console, capture)
        
        # Step 5: Test team member interactions
        await test_team_member_interactions(team, console, capture)
        
        # Step 6: Analyze patterns
        await analyze_response_patterns(capture, console)
        
        # Step 7: Save diagnostic report
        await save_diagnostic_report(capture, console)
        
        console.print("\n✅ [bold green]All tests completed![/bold green]")
        console.print("\n🔍 [bold cyan]Key Findings:[/bold cyan]")
        console.print("Check the diagnostic report for detailed analysis of where")
        console.print("the memory agent output might be getting lost in the response stream.")
        
    except Exception as e:
        console.print(f"❌ [bold red]Test execution failed:[/bold red] {str(e)}")
        logger.exception("Main test execution error")
        
    finally:
        # Cleanup
        if 'team' in locals() and team:
            console.print("\n🧹 Cleaning up team resources...")
            await cleanup_team(team)
            console.print("✅ Cleanup completed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test reasoning team memory response capture"
    )
    parser.add_argument(
        "--remote", 
        action="store_true", 
        help="Use remote Ollama server"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="list all memories",
        help="Query to test (default: 'list all memories')"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Update the main function to accept parameters
    async def main_with_args():
        """Main test function with command line arguments."""
        console = Console(force_terminal=True)
        
        console.print("🧪 [bold blue]Reasoning Team Memory Response Test[/bold blue]")
        console.print("=" * 60)
        console.print(f"🔍 Testing query: '{args.query}'")
        console.print(f"🌐 Remote mode: {args.remote}")
        
        # Initialize response capture
        capture = ResponseCapture()
        
        try:
            # Step 1: Initialize team
            team = await test_team_initialization(console, use_remote=args.remote)
            if not team:
                console.print("❌ Cannot proceed without team initialization")
                return
            
            # Step 2: Test memory agent directly
            await test_memory_agent_direct(team, console, capture)
            
            # Step 3: Test team response with streaming
            await test_team_response_streaming(team, console, capture)
            
            # Step 4: Test team response without streaming  
            await test_team_response_non_streaming(team, console, capture)
            
            # Step 5: Test team member interactions
            await test_team_member_interactions(team, console, capture)
            
            # Step 6: Analyze patterns
            await analyze_response_patterns(capture, console)
            
            # Step 7: Save diagnostic report
            await save_diagnostic_report(capture, console)
            
            console.print("\n✅ [bold green]All tests completed![/bold green]")
            console.print("\n🔍 [bold cyan]Key Findings:[/bold cyan]")
            console.print("Check the diagnostic report for detailed analysis of where")
            console.print("the memory agent output might be getting lost in the response stream.")
            
        except Exception as e:
            console.print(f"❌ [bold red]Test execution failed:[/bold red] {str(e)}")
            logger.exception("Main test execution error")
            
        finally:
            # Cleanup
            if 'team' in locals() and team:
                console.print("\n🧹 Cleaning up team resources...")
                await cleanup_team(team)
                console.print("✅ Cleanup completed")
    
    # Run the test with arguments
    asyncio.run(main_with_args())
