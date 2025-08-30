#!/usr/bin/env python3
"""
Debug script to analyze team response parsing for image URLs.
This will help us understand why image URLs aren't being extracted from member responses.
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

# Configure logging to see all debug information
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

console = Console()

async def test_image_response_parsing():
    """Test how the team handles image creation responses."""
    
    console.print("🔍 [bold blue]Testing Team Response Parsing for Image URLs[/bold blue]")
    console.print("=" * 60)
    
    try:
        # Create the team
        console.print("Creating team...")
        team = await create_team(use_remote=False)
        
        # Test image creation request
        test_query = "create an image of a robot with a balloon"
        console.print(f"\n🤖 Testing query: '{test_query}'")
        
        # DIAGNOSTIC: Let's examine the team's arun method to see how it processes responses
        console.print("\n🔍 [bold yellow]DIAGNOSTIC: Examining team response processing...[/bold yellow]")
        
        # Use arun instead of aprint_response to get the actual response object
        response = await team.arun(test_query)
        
        console.print(f"\n📝 [bold green]Raw Response Type:[/bold green] {type(response)}")
        console.print(f"📝 [bold green]Raw Response Content:[/bold green]")
        console.print(response)
        
        # Check if response contains image markdown
        if isinstance(response, str):
            if "![" in response and "](" in response:
                console.print("\n✅ [bold green]Image markdown found in response![/bold green]")
                # Extract image URLs
                import re
                image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
                matches = re.findall(image_pattern, response)
                for alt_text, url in matches:
                    console.print(f"  - Alt text: '{alt_text}'")
                    console.print(f"  - URL: '{url}'")
            else:
                console.print("\n❌ [bold red]No image markdown found in response[/bold red]")
                console.print("This indicates the team is not properly extracting image URLs from member responses")
        
        # Let's also examine the team's members and their responses
        console.print(f"\n🔍 [bold yellow]Team Members:[/bold yellow]")
        for i, member in enumerate(team.members):
            console.print(f"  {i+1}. {member.name}")
        
        # Check if the team has any response history or member interactions
        if hasattr(team, 'memory') and team.memory:
            console.print(f"\n🔍 [bold yellow]Team Memory:[/bold yellow] {type(team.memory)}")
        
        if hasattr(team, '_member_interactions'):
            console.print(f"\n🔍 [bold yellow]Member Interactions:[/bold yellow] {len(team._member_interactions) if team._member_interactions else 0}")
        
    except Exception as e:
        console.print(f"\n❌ [bold red]Error during testing:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())

async def test_direct_image_agent():
    """Test the image agent directly to see its response format."""
    
    console.print("\n🎨 [bold blue]Testing Image Agent Directly[/bold blue]")
    console.print("=" * 40)
    
    try:
        from personal_agent.team.reasoning_team import create_image_agent
        
        # Create image agent directly
        image_agent = create_image_agent(use_remote=False)
        
        # Test image creation
        test_query = "create an image of a robot with a balloon"
        console.print(f"🤖 Testing direct image agent with: '{test_query}'")
        
        response = await image_agent.arun(test_query)
        
        console.print(f"\n📝 [bold green]Direct Image Agent Response:[/bold green]")
        console.print(response)
        
        # Check for image markdown in direct response
        if isinstance(response, str):
            if "![" in response and "](" in response:
                console.print("\n✅ [bold green]Image markdown found in direct agent response![/bold green]")
                import re
                image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
                matches = re.findall(image_pattern, response)
                for alt_text, url in matches:
                    console.print(f"  - Alt text: '{alt_text}'")
                    console.print(f"  - URL: '{url}'")
            else:
                console.print("\n❌ [bold red]No image markdown in direct agent response[/bold red]")
        
    except Exception as e:
        console.print(f"\n❌ [bold red]Error testing direct image agent:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())

async def main():
    """Main diagnostic function."""
    await test_direct_image_agent()
    await test_image_response_parsing()

if __name__ == "__main__":
    asyncio.run(main())