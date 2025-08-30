#!/usr/bin/env python3
"""
Debug script to compare streaming vs non-streaming team responses for image creation.
This will help us understand why the final response might not be displayed properly.
"""

import asyncio
import logging
from pathlib import Path
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.team.reasoning_team import create_team
from rich.console import Console

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

console = Console()

async def test_streaming_vs_nonstreaming():
    """Compare streaming vs non-streaming responses for image creation."""
    
    console.print("🔍 [bold blue]Testing Streaming vs Non-Streaming Team Responses[/bold blue]")
    console.print("=" * 70)
    
    try:
        # Create the team
        console.print("Creating team...")
        team = await create_team(use_remote=False)
        
        test_query = "create an image of a robot with a balloon"
        
        # Test 1: Non-streaming response (arun)
        console.print(f"\n🚀 [bold yellow]TEST 1: Non-streaming (arun)[/bold yellow]")
        console.print(f"Query: '{test_query}'")
        console.print("-" * 50)
        
        response = await team.arun(test_query)
        console.print(f"\n📝 [bold green]Non-streaming Response Content:[/bold green]")
        console.print(response.content if hasattr(response, 'content') else str(response))
        
        # Check for image markdown in non-streaming response
        response_text = response.content if hasattr(response, 'content') else str(response)
        if "![" in response_text and "](" in response_text:
            console.print("\n✅ [bold green]Image markdown found in non-streaming response![/bold green]")
            import re
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            matches = re.findall(image_pattern, response_text)
            for alt_text, url in matches:
                console.print(f"  - Alt text: '{alt_text}'")
                console.print(f"  - URL: '{url[:100]}...'")
        else:
            console.print("\n❌ [bold red]No image markdown in non-streaming response[/bold red]")
        
        # Test 2: Streaming response (aprint_response with capture)
        console.print(f"\n🌊 [bold yellow]TEST 2: Streaming (aprint_response)[/bold yellow]")
        console.print(f"Query: '{test_query}'")
        console.print("-" * 50)
        
        # Create a new team instance to avoid state issues
        team2 = await create_team(use_remote=False)
        
        # Capture streaming output
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        
        # Note: aprint_response doesn't return the content, it prints it
        # So we need to capture what it prints
        console.print("🔍 [bold cyan]Streaming response (this will be printed directly):[/bold cyan]")
        
        # Use aprint_response with stream=True (this is what the CLI uses)
        await team2.aprint_response(test_query, stream=True)
        
        console.print("\n🔍 [bold cyan]End of streaming response[/bold cyan]")
        
        # Test 3: Check if the issue is in the CLI's usage
        console.print(f"\n🖥️ [bold yellow]TEST 3: CLI-style usage analysis[/bold yellow]")
        console.print("-" * 50)
        
        # This is how the CLI calls it in reasoning_team.py line 1416
        console.print("The CLI uses: await team.aprint_response(user_input, stream=True)")
        console.print("This method prints directly to console and doesn't return the response content.")
        console.print("The issue might be that aprint_response with streaming doesn't show the final aggregated response.")
        
    except Exception as e:
        console.print(f"\n❌ [bold red]Error during testing:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())

async def main():
    """Main diagnostic function."""
    await test_streaming_vs_nonstreaming()

if __name__ == "__main__":
    asyncio.run(main())