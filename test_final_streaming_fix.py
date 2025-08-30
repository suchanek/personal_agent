#!/usr/bin/env python3
"""
Test script to verify the final streaming fix using the proven approach from intelligent_streaming_analyzer.py
This uses the collect_streaming_response approach that we know works.
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
from agno.tools.dalle import DalleTools
from agno.utils.common import dataclass_to_dict
from rich.pretty import pprint


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

console = Console()

async def test_final_streaming_fix():
    """Test the final streaming fix using the proven chunk collection approach."""
    
    console.print("🔧 [bold blue]Testing Final Streaming Fix (Proven Approach)[/bold blue]")
    console.print("=" * 60)
    
    try:
        # Create the team
        console.print("Creating team...")
        team = await create_team(use_remote=False)
        
        # Test image creation request
        console.print(f"\n🎨 [bold yellow]Testing Image Creation[/bold yellow]")
        test_query = "create an image of a robot with a balloon"
        console.print(f"Query: '{test_query}'")
        console.print("-" * 50)
        
        # Use the same approach as the fixed reasoning_team.py
        console.print("🤖 [bold green]Team Response:[/bold green]")
        
        # This mimics the fixed logic in reasoning_team.py
        run_stream = team.run(test_query, stream=True)
        
        # Collect all chunks from streaming iterator (proven solution from intelligent_streaming_analyzer.py)
        chunks = list(run_stream)
        console.print(f"✅ Collected {len(chunks)} chunks from streaming iterator")
        
        # Get final content from the last chunk or completed chunk
        final_content = ""
        for chunk in reversed(chunks):  # Start from the end to find completed chunk
            if hasattr(chunk, 'content') and chunk.content:
                final_content = chunk.content
                break
        
        # Display the complete final response
        console.print(f"\n📝 [bold green]Final Complete Response:[/bold green]")
        console.print(final_content)
        
        # Check if the response contains the image markdown
        if "![" in str(final_content) and "](" in str(final_content):
            console.print("\n✅ [bold green]SUCCESS: Image markdown found in complete response![/bold green]")
            import re
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            matches = re.findall(image_pattern, str(final_content))
            for alt_text, url in matches:
                console.print(f"  - Alt text: '{alt_text}'")
                console.print(f"  - URL: '{url[:100]}...'")
        else:
            console.print("\n❌ [bold red]ISSUE: No image markdown found in complete response[/bold red]")
            console.print(f"Response content preview: {str(final_content)[:200]}...")
        
        console.print(f"\n🎯 [bold cyan]Fix Summary:[/bold cyan]")
        console.print("✅ Applied proven streaming chunk collection from intelligent_streaming_analyzer.py")
        console.print("✅ Using list(run_stream) to collect all chunks")
        console.print("✅ Extracting final content from completed/last chunk")
        console.print("✅ This should fix the streaming truncation issue for ALL responses")
        
    except Exception as e:
        console.print(f"\n❌ [bold red]Error during testing:[/bold red] {e}")
        import traceback
        console.print(traceback.format_exc())

async def main():
    """Main test function."""
    await test_final_streaming_fix()

if __name__ == "__main__":
    asyncio.run(main())