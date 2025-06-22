#!/usr/bin/env python3
"""
Personal Agent Team Demo

This script demonstrates the new team-based approach where specialized agents
work together instead of having one large agent that does everything.

The team consists of:
- Memory Agent: Specialized in storing and retrieving personal information
- Web Research Agent: Specialized in web searches and current events
- Finance Agent: Specialized in financial data and stock analysis
- Calculator Agent: Specialized in mathematical calculations
- File Operations Agent: Specialized in file system operations

A team coordinator uses reasoning to delegate tasks to the appropriate agents.
"""

import asyncio
import sys
from pathlib import Path
from textwrap import dedent

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import LLM_MODEL, OLLAMA_URL, USER_ID, AGNO_STORAGE_DIR
from personal_agent.team.personal_agent_team import PersonalAgentTeamWrapper
from personal_agent.utils import setup_logging

# Configure logging
logger = setup_logging(__name__)


async def demo_team_capabilities():
    """Demonstrate the capabilities of the specialized agent team."""
    print("🚀 PERSONAL AGENT TEAM DEMO")
    print("=" * 60)
    print(f"Model: {LLM_MODEL}")
    print(f"User ID: {USER_ID}")
    print(f"Storage: {AGNO_STORAGE_DIR}")
    print()

    # Initialize team
    print("🤝 Initializing Personal Agent Team...")
    team = PersonalAgentTeamWrapper(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        storage_dir=AGNO_STORAGE_DIR,
        user_id=USER_ID,
        debug=True,
    )

    success = await team.initialize()
    if not success:
        print("❌ Failed to initialize team")
        return

    print("✅ Team initialized successfully!")
    
    # Show team info
    team_info = team.get_agent_info()
    print(f"📋 Team: {team_info['team_name']} ({team_info['member_count']} agents)")
    print()

    # Demo scenarios
    scenarios = [
        {
            "title": "🧠 Memory Agent Demo",
            "description": "Testing memory storage and retrieval",
            "queries": [
                "Please remember that I'm a software engineer who loves Python programming",
                "Store this information: I prefer working remotely and enjoy hiking on weekends",
                "What do you remember about my profession?",
                "What are my hobbies and preferences?",
            ]
        },
        {
            "title": "🌐 Web Research Agent Demo", 
            "description": "Testing web search capabilities",
            "queries": [
                "What are the top 3 AI news headlines today?",
                "Search for recent developments in artificial intelligence",
            ]
        },
        {
            "title": "💰 Finance Agent Demo",
            "description": "Testing financial data retrieval",
            "queries": [
                "What's the current stock price of Apple (AAPL)?",
                "Get me information about Tesla's stock performance",
            ]
        },
        {
            "title": "🔢 Calculator Agent Demo",
            "description": "Testing mathematical calculations",
            "queries": [
                "Calculate the square root of 144",
                "What's 15% of 250?",
                "Calculate compound interest: $1000 at 5% for 3 years",
            ]
        },
        {
            "title": "🤝 Team Coordination Demo",
            "description": "Testing multi-agent coordination",
            "queries": [
                "Remember that I'm interested in Tesla stock, then get me its current price",
                "Store my preference for AI news, then find me the latest AI headlines",
                "What do you know about me, and can you search for news related to my interests?",
            ]
        }
    ]

    for scenario in scenarios:
        print(f"\n{scenario['title']}")
        print(f"📝 {scenario['description']}")
        print("-" * 50)

        for i, query in enumerate(scenario['queries'], 1):
            print(f"\n🔍 Query {i}: {query}")
            try:
                response = await team.run(query)
                print(f"✅ Response: {response[:300]}...")
                if len(response) > 300:
                    print("   (truncated)")
                
                # Show which tools were used
                tool_info = team.get_last_tool_calls()
                if tool_info["has_tool_calls"]:
                    print(f"🛠️ Tools used: {tool_info['tool_calls_count']} calls")
                    
            except Exception as e:
                print(f"❌ Error: {e}")

            print()

    # Cleanup
    await team.cleanup()
    print("🎉 Demo completed successfully!")


async def interactive_demo():
    """Run an interactive demo where users can chat with the team."""
    print("🎯 INTERACTIVE TEAM DEMO")
    print("=" * 60)
    print("Chat with the Personal Agent Team!")
    print("Type 'quit' to exit")
    print()

    # Initialize team
    team = PersonalAgentTeamWrapper(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        storage_dir=AGNO_STORAGE_DIR,
        user_id=USER_ID,
        debug=False,  # Less verbose for interactive mode
    )

    success = await team.initialize()
    if not success:
        print("❌ Failed to initialize team")
        return

    print("✅ Team ready! Try these examples:")
    print("  • 'What do you remember about me?'")
    print("  • 'What's the latest AI news?'")
    print("  • 'What's Apple's stock price?'")
    print("  • 'Calculate 25% of 400'")
    print("  • 'Remember that I love coffee, then search for coffee news'")
    print()

    while True:
        try:
            query = input("💬 You: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
                
            if not query:
                continue

            print("🤖 Team: ", end="", flush=True)
            response = await team.run(query)
            print(response)
            print()

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

    await team.cleanup()
    print("\n👋 Thanks for trying the Personal Agent Team!")


async def main():
    """Main demo function."""
    print("🤖 PERSONAL AGENT TEAM DEMONSTRATION")
    print()
    print("This demo showcases the new team-based approach where specialized")
    print("agents work together instead of having one large monolithic agent.")
    print()
    print("Choose demo mode:")
    print("1. Automated demo (shows all capabilities)")
    print("2. Interactive demo (chat with the team)")
    print("3. Both")

    try:
        choice = input("\nEnter choice (1/2/3): ").strip()

        if choice == "1":
            await demo_team_capabilities()
        elif choice == "2":
            await interactive_demo()
        elif choice == "3":
            await demo_team_capabilities()
            print("\n" + "=" * 60)
            await interactive_demo()
        else:
            print("Invalid choice. Running automated demo.")
            await demo_team_capabilities()

    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("💡 Make sure Ollama is running before starting the demo")
    print("💡 This demonstrates the new specialized agent team approach")
    print()
    
    asyncio.run(main())
