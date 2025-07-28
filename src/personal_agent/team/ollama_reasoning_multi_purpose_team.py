"""
Ollama-based Multi-Purpose Reasoning Team

This example demonstrates a team of agents using local Ollama models that can answer
a variety of questions with memory and knowledge capabilities.

The team consists of:
- A web agent that can search the web for information
- A finance agent that can get financial data
- A writer agent that can write content
- A calculator agent that can calculate
- A memory agent that can store and retrieve personal information and knowledge
"""

import asyncio
from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.models.ollama.tools import OllamaTools
from agno.team.team import Team
from agno.tools.calculator import CalculatorTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.python import PythonTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools
from dotenv import load_dotenv

from ..tools.knowledge_tools import KnowledgeTools
from ..tools.refactored_memory_tools import AgnoMemoryTools

# Import your personal agent components
from ..config.settings import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    LIGHTRAG_MEMORY_URL,
    LIGHTRAG_URL,
    LLM_MODEL,
    OLLAMA_URL,
    USER_ID,
)
from ..core import AgentKnowledgeManager, AgentMemoryManager, AgentModelManager
from ..core.agno_storage import (
    create_agno_memory,
    create_agno_storage,
    create_combined_knowledge_base,
    load_combined_knowledge_base,
)

# Load environment variables
load_dotenv()

cwd = Path(__file__).parent.resolve()


def create_ollama_model(model_name: str = LLM_MODEL) -> OllamaTools:
    """Create an Ollama model using your AgentModelManager."""
    model_manager = AgentModelManager(
        model_provider="ollama",
        model_name=model_name,
        ollama_base_url=OLLAMA_URL,
        seed=None,
    )
    return model_manager.create_model()


# Web search agent using Ollama
web_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    model=create_ollama_model(),
    tools=[DuckDuckGoTools(cache_results=True)],
    instructions=["Always include sources"],
    show_tool_calls=True,
)

# Finance agent using Ollama
finance_agent = Agent(
    name="Finance Agent",
    role="Get financial data",
    model=create_ollama_model(),
    tools=[
        YFinanceTools(
            stock_price=True,
            analyst_recommendations=True,
            company_info=True,
            company_news=True,
        )
    ],
    instructions=["Use tables to display data"],
    show_tool_calls=True,
)

# Writer agent using Ollama
writer_agent = Agent(
    name="Writer Agent",
    role="Write content",
    model=create_ollama_model(),
    description="You are an AI agent that can write content.",
    instructions=[
        "You are a versatile writer who can create content on any topic.",
        "When given a topic, write engaging and informative content in the requested format and style.",
        "If you receive mathematical expressions or calculations from the calculator agent, convert them into clear written text.",
        "Ensure your writing is clear, accurate and tailored to the specific request.",
        "Maintain a natural, engaging tone while being factually precise.",
        "Write something that would be good enough to be published in a newspaper like the New York Times.",
    ],
    show_tool_calls=True,
)

# Calculator agent using Ollama
calculator_agent = Agent(
    name="Calculator Agent",
    model=create_ollama_model(),
    role="Calculate",
    tools=[
        CalculatorTools(
            add=True,
            subtract=True,
            multiply=True,
            divide=True,
            exponentiate=True,
            factorial=True,
            is_prime=True,
            square_root=True,
        ),
        PythonTools(),
    ],
    show_tool_calls=True,
)


async def create_memory_agent(
    storage_dir: str = AGNO_STORAGE_DIR,
    knowledge_dir: str = AGNO_KNOWLEDGE_DIR,
    user_id: str = USER_ID,
    debug: bool = False,
) -> Agent:
    """Create a memory agent following the exact AgnoPersonalAgent initialization pattern."""

    # 1. Create Agno storage (CRITICAL: Must be done first)
    agno_storage = create_agno_storage(storage_dir)

    # 2. Create combined knowledge base (CRITICAL: Must be done before loading)
    agno_knowledge = create_combined_knowledge_base(
        storage_dir, knowledge_dir, agno_storage
    )

    # 3. Load knowledge base content (CRITICAL: Must be async)
    if agno_knowledge:
        await load_combined_knowledge_base(agno_knowledge, recreate=False)

    # 4. Create memory with SemanticMemoryManager (CRITICAL: Must be done after storage)
    agno_memory = create_agno_memory(storage_dir, debug_mode=debug)

    # 5. Initialize managers (CRITICAL: Must be done after agno_memory creation)
    memory_manager = AgentMemoryManager(
        user_id=user_id,
        storage_dir=storage_dir,
        agno_memory=agno_memory,
        lightrag_url=LIGHTRAG_URL,
        lightrag_memory_url=LIGHTRAG_MEMORY_URL,
        enable_memory=True,
    )

    # Initialize the memory manager with the created agno_memory
    memory_manager.initialize(agno_memory)

    knowledge_manager = AgentKnowledgeManager(
        user_id=user_id,
        storage_dir=storage_dir,
        lightrag_url=LIGHTRAG_URL,
        lightrag_memory_url=LIGHTRAG_MEMORY_URL,
    )

    # 6. Create tool instances (CRITICAL: Must be done after managers)
    knowledge_tools = KnowledgeTools(knowledge_manager)
    memory_tools = AgnoMemoryTools(memory_manager)

    # 7. Create the Agent (CRITICAL: Must be done last)
    agent = Agent(
        name="Memory Agent",
        role="Store and retrieve personal information and knowledge",
        model=create_ollama_model(),
        tools=[knowledge_tools, memory_tools],
        instructions=[
            """## BEHAVIOR RULES:
        1. **Memory Operations ONLY**: EXECUTE memory functions directly, don't show code
           - 'What do you remember about me?' → CALL get_recent_memories() and return results
           - 'Do you know my preferences?' → CALL query_memory('preferences') and return results
           - 'Remember that I...' → CALL store_user_memory(content, topics) and confirm
           - NEVER show function names or code tags - EXECUTE the functions
           - NEVER delegate memory tasks to team members"

            "You are a memory and knowledge agent with access to both personal memory and factual knowledge.",
            "Use memory tools for personal information about the user.",
            "Use knowledge tools for factual information and documents.",
            "Always search your memory when asked about the user.",
            "Always search your knowledge base when asked about factual information.",
            "Store new personal information in memory and new factual information in knowledge.""",
        ],
        markdown=True,
        show_tool_calls=True,
        user_id=user_id,
        enable_agentic_memory=False,  # Disable to avoid conflicts
        enable_user_memories=False,  # Use our custom tools instead
        storage=agno_storage,
        knowledge=agno_knowledge,
        memory=agno_memory,
        search_knowledge=True,
    )

    return agent


# Create the team
async def create_team():
    """Create the team with all agents including the memory agent."""

    # Create memory agent (must be async)
    memory_agent = await create_memory_agent()

    # Create the team
    agent_team = Team(
        name="Personal Agent Team",
        mode="coordinate",
        model=create_ollama_model(),
        tools=[
            ReasoningTools(add_instructions=True, add_few_shot=True),
        ],
        members=[
            memory_agent,  # Add the memory agent
            web_agent,
            finance_agent,
            writer_agent,
            calculator_agent,
        ],
        instructions=[
            "You are a team of agents using local Ollama models that can answer a variety of questions.",
            "Your primary goal is to collect user memories and factual knowledge.",
            "Use the memory agent for personal information and the knowledge agent for factual information.",
            "You can use your member agents to answer general non-user questions.",
            "You can also answer directly, you don't HAVE to forward the question to a member agent.",
            "Reason about more complex questions before delegating to a member agent.",
            "If the user is only being conversational, don't use any tools, just answer directly.",
            "The memory agent can store and retrieve both personal information and factual knowledge.",
        ],
        markdown=True,
        show_tool_calls=True,
        show_members_responses=True,
        enable_agentic_context=True,
        share_member_interactions=True,
    )

    return agent_team


async def cleanup_team(team):
    """Clean up team resources to prevent ResourceWarnings."""
    try:
        # Close any open HTTP sessions in the team and its members
        if hasattr(team, 'members'):
            for member in team.members:
                # Close any HTTP sessions in the agent's tools
                if hasattr(member, 'tools'):
                    for tool in member.tools:
                        # Close HTTP sessions in tools that have them
                        if hasattr(tool, '_session') and tool._session:
                            await tool._session.close()
                        if hasattr(tool, 'session') and tool.session:
                            await tool.session.close()
                        # Handle DuckDuckGo tools specifically
                        if hasattr(tool, 'ddgs') and hasattr(tool.ddgs, '_session'):
                            if tool.ddgs._session:
                                await tool.ddgs._session.close()
                
                # Close any HTTP sessions in the agent's model
                if hasattr(member, 'model') and hasattr(member.model, '_session'):
                    if member.model._session:
                        await member.model._session.close()
        
        # Close any HTTP sessions in the team's model
        if hasattr(team, 'model') and hasattr(team.model, '_session'):
            if team.model._session:
                await team.model._session.close()
                
        # Give a moment for cleanup to complete
        await asyncio.sleep(0.1)
        
    except Exception as e:
        # Don't let cleanup errors crash the program
        pass


# Main execution
async def main():
    """Main function to run the team with an interactive chat loop."""
    
    print("🤖 Ollama Multi-Purpose Reasoning Team")
    print("=" * 50)
    print("Initializing team with memory and knowledge capabilities...")
    print("This may take a moment on first run...")
    
    try:
        # Create the team
        team = await create_team()
        
        print("\n✅ Team initialized successfully!")
        print("\nTeam Members:")
        print("- 🧠 Memory Agent: Store and retrieve personal information and knowledge")
        print("- 🌐 Web Agent: Search the web for information")
        print("- 💰 Finance Agent: Get financial data and analysis")
        print("- ✍️  Writer Agent: Create content and written materials")
        print("- 🧮 Calculator Agent: Perform calculations and math")
        
        print("\n" + "=" * 50)
        print("💬 Interactive Chat Mode")
        print("=" * 50)
        print("Type your questions or requests below.")
        print("Commands:")
        print("  - 'quit' or 'exit' to end the session")
        print("  - 'help' to see this message again")
        print("  - 'clear' to clear the screen")
        print("  - 'examples' to see example queries")
        print("\nTip: Try asking me to remember things about you, search the web,")
        print("     get financial data, write content, or do calculations!")
        print("-" * 50)
        
        # Interactive chat loop
        while True:
            try:
                # Get user input
                user_input = input("\n🗣️  You: ").strip()
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye! Thanks for using the Personal Agent Team!")
                    # Cleanup team resources
                    await cleanup_team(team)
                    break
                    
                elif user_input.lower() == 'help':
                    print("\n📋 Available Commands:")
                    print("  - 'quit' or 'exit' to end the session")
                    print("  - 'help' to see this message")
                    print("  - 'clear' to clear the screen")
                    print("  - 'examples' to see example queries")
                    print("\n🤖 Team Capabilities:")
                    print("  - Remember personal information and preferences")
                    print("  - Search the web for current information")
                    print("  - Analyze financial data and stocks")
                    print("  - Write content, articles, and creative text")
                    print("  - Perform mathematical calculations")
                    continue
                    
                elif user_input.lower() == 'clear':
                    import os
                    os.system('clear' if os.name == 'posix' else 'cls')
                    print("🤖 Ollama Multi-Purpose Reasoning Team")
                    print("💬 Chat cleared. How can I help you?")
                    continue
                    
                elif user_input.lower() == 'examples':
                    print("\n💡 Example Queries:")
                    print("  Memory & Personal:")
                    print("    - 'Remember that I love skiing and live in Colorado'")
                    print("    - 'What do you remember about me?'")
                    print("    - 'Store this fact: I work as a software engineer'")
                    print("\n  Web Search:")
                    print("    - 'What's the latest news about AI?'")
                    print("    - 'Search for information about climate change'")
                    print("\n  Finance:")
                    print("    - 'Give me a financial analysis of NVDA'")
                    print("    - 'What's the current stock price of Apple?'")
                    print("\n  Writing:")
                    print("    - 'Write a short poem about AI agents'")
                    print("    - 'Create a summary of machine learning'")
                    print("\n  Math & Calculations:")
                    print("    - 'Calculate the square root of 144'")
                    print("    - 'What's 15% of 250?'")
                    continue
                    
                # Skip empty input
                if not user_input:
                    continue
                
                # Process the query with the team
                print(f"\n🤖 Team: ", end="", flush=True)
                await team.aprint_response(user_input, stream=True)
                
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted by user. Type 'quit' to exit gracefully.")
                continue
            except EOFError:
                print("\n\n👋 Session ended. Goodbye!")
                await cleanup_team(team)
                break
            except Exception as e:
                print(f"\n❌ Error processing your request: {str(e)}")
                print("Please try again or type 'help' for assistance.")
                continue
                
    except KeyboardInterrupt:
        print("\n\n⚠️  Initialization interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error initializing team: {str(e)}")
        print("Please check your configuration and try again.")


def cli_main():
    """Entry point for the paga_team_cli command."""
    asyncio.run(main())


if __name__ == "__main__":
    # Run the main function
    cli_main()
