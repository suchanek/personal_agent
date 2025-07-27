#!/usr/bin/env python3
"""
Quick validation script to test that tool calling is now working.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from examples.teams.ollama_reasoning_multi_purpose_team import create_team

async def validate_tool_calling():
    """Quick test to validate tool calling is working."""
    
    print("🔧 Validating Tool Calling Fix")
    print("=" * 50)
    
    try:
        # Create the team
        print("📝 Creating team...")
        team = await create_team()
        print("✅ Team created successfully!")
        
        # Test a simple calculation that should definitely call tools
        print("\n🧮 Testing Calculator Agent Tool Calling...")
        print("Query: Calculate 12 * 12")
        print("-" * 30)
        
        await team.aprint_response("Calculate 12 * 12", stream=True)
        
        print("\n" + "=" * 50)
        print("✅ Validation complete! Check above for tool call evidence.")
        print("Look for tool execution logs or actual calculation results.")
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(validate_tool_calling())