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

# pylint: disable=C0415,W0212,C0301,W0718

import argparse
import asyncio
from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama.tools import OllamaTools
from agno.team.team import Team
from agno.tools.calculator import CalculatorTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.python import PythonTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools
from dotenv import load_dotenv

# Import your personal agent components
try:
    # Try relative imports first (when used as a module)
    from ..config.settings import (
        AGNO_KNOWLEDGE_DIR,
        AGNO_STORAGE_DIR,
        LLM_MODEL,
        OLLAMA_URL,
        REMOTE_OLLAMA_URL,
        USER_ID,
    )
    from ..core.agent_model_manager import AgentModelManager
except ImportError:
    # Fall back to absolute imports (when run directly)
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    from personal_agent.config.settings import (
        AGNO_KNOWLEDGE_DIR,
        AGNO_STORAGE_DIR,
        LLM_MODEL,
        OLLAMA_URL,
        REMOTE_OLLAMA_URL,
        USER_ID,
    )
    from personal_agent.core.agent_model_manager import AgentModelManager

# Load environment variables
load_dotenv()

cwd = Path(__file__).parent.resolve()

_instructions = dedent(
    """\
    Your mission is to provide comprehensive support for Agno developers. Follow these steps to ensure the best possible response:

    1. **Analyze the request**
        - Analyze the request to determine if it requires a knowledge search, creating an Agent, or both.
        - If you need to search the knowledge base, identify 1-3 key search terms related to Agno concepts.
        - If you need to create an Agent, search the knowledge base for relevant concepts and use the example code as a guide.
        - When the user asks for an Agent, they mean an Agno Agent.
        - All concepts are related to Agno, so you can search the knowledge base for relevant information

    After Analysis, always start the iterative search process. No need to wait for approval from the user.

    2. **Iterative Search Process**:
        - Use the `search_knowledge_base` tool to search for related concepts, code examples and implementation details
        - Continue searching until you have found all the information you need or you have exhausted all the search terms

    After the iterative search process, determine if you need to create an Agent.
    If you do, ask the user if they want you to create the Agent and run it.

    3. **Code Creation and Execution**
        - Create complete, working code examples that users can run. For example:
        ```python
        from agno.agent import Agent
        from agno.tools.duckduckgo import DuckDuckGoTools

        agent = Agent(tools=[DuckDuckGoTools()])

        # Perform a web search and capture the response
        response = agent.run("What's happening in France?")
        ```
        - You must remember to use agent.run() and NOT agent.print_response()
        - This way you can capture the response and return it to the user
        - Use the `save_to_file_and_run` tool to save it to a file and run.
        - Make sure to return the `response` variable that tells you the result
        - Remember to:
            * Build the complete agent implementation and test with `response = agent.run()`
            * Include all necessary imports and setup
            * Add comprehensive comments explaining the implementation
            * Test the agent with example queries
            * Ensure all dependencies are listed
            * Include error handling and best practices
            * Add type hints and documentation

    4. **Explain important concepts using audio**
        - When explaining complex concepts or important features, ask the user if they'd like to hear an audio explanation
        - Use the ElevenLabs text_to_speech tool to create clear, professional audio content
        - The voice is pre-selected, so you don't need to specify the voice.
        - Keep audio explanations concise (60-90 seconds)
        - Make your explanation really engaging with:
            * Brief concept overview and avoid jargon
            * Talk about the concept in a way that is easy to understand
            * Use practical examples and real-world scenarios
            * Include common pitfalls to avoid

    5. **Explain concepts with images**
        - You have access to the extremely powerful DALL-E 3 model.
        - Use the `create_image` tool to create extremely vivid images of your explanation.

    Key topics to cover:
    - Agent levels and capabilities
    - Knowledge base and memory management
    - Tool integration
    - Model support and configuration
    - Best practices and common patterns"""
)

_code_instructions = dedent(
    """\
    Your mission is to provide comprehensive code development support for developers. Follow these steps to ensure the best possible response:

    1. **Code Creation and Execution**
        - Create complete, working code examples that users can run. For example:
        ```python
        from agno.agent import Agent
        from agno.tools.duckduckgo import DuckDuckGoTools

        agent = Agent(tools=[DuckDuckGoTools()])

        # Perform a web search and capture the response
        response = agent.run("What's happening in France?")
        ```
        - When building agents you must remember to use agent.run() and NOT agent.print_response()
        - This way you can capture the agent response and return it to the user
        - Make sure to return the `response` variable that tells you the result
        - Use the `save_to_file_and_run` tool to save code to a file and run.
        - Remember to:
            * Build the complete agent implementation and test 
            * Include all necessary imports and setup
            * Add comprehensive comments explaining the implementation
            * Test a requested agent with example queries via with `response = agent.run()`
            * Test requested code by executing it.
            * Ensure all dependencies are listed
            * Include error handling and best practices
            * Add type hints and documentation

    4. **Explain important concepts using audio**
        - When explaining complex concepts or important features, ask the user if they'd like to hear an audio explanation
        - Use the ElevenLabs text_to_speech tool to create clear, professional audio content
        - The voice is pre-selected, so you don't need to specify the voice.
        - Keep audio explanations concise (60-90 seconds)
        - Make your explanation really engaging with:
            * Brief concept overview and avoid jargon
            * Talk about the concept in a way that is easy to understand
            * Use practical examples and real-world scenarios
            * Include common pitfalls to avoid

    5. **Explain concepts with images**
        - You have access to the extremely powerful DALL-E 3 model.
        - Use the `create_image` tool to create extremely vivid images of your explanation.

    Key topics to cover:
    - Agent levels and capabilities
    - Knowledge base and memory management
    - Tool integration
    - Model support and configuration
    - Best practices and common patterns"""
)


def create_ollama_model(
    model_name: str = LLM_MODEL, use_remote: bool = False
) -> OllamaTools:
    """Create an Ollama model using your AgentModelManager."""
    ollama_url = REMOTE_OLLAMA_URL if use_remote else OLLAMA_URL
    model_manager = AgentModelManager(
        model_provider="ollama",
        model_name=model_name,
        ollama_base_url=ollama_url,
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
    role="Calculate mathematical expressions",
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
    ],
    show_tool_calls=True,
)

python_agent = Agent(
    name="Python Agent",
    model=create_ollama_model(),
    role="Execute Python code",
    tools=[
        PythonTools(
            base_dir=cwd,  # Use current directory as base
            save_and_run=True,
            run_files=True,
            read_files=True,
        ),
    ],
    instructions=dedent(_code_instructions),
    show_tool_calls=True,
)


async def create_shared_memory_system(
    storage_dir: str = AGNO_STORAGE_DIR,
    knowledge_dir: str = AGNO_KNOWLEDGE_DIR,
    user_id: str = USER_ID,
    debug: bool = False,
    use_remote: bool = False,
):
    """Create a shared memory system that integrates with your existing managers."""
    try:
        from ..config.settings import LIGHTRAG_MEMORY_URL, LIGHTRAG_URL
        from ..core.agent_knowledge_manager import AgentKnowledgeManager
        from ..core.agent_memory_manager import AgentMemoryManager
        from ..core.agno_storage import (
            create_agno_memory,
            create_combined_knowledge_base,
            load_combined_knowledge_base,
        )
    except ImportError:
        from personal_agent.config.settings import LIGHTRAG_MEMORY_URL, LIGHTRAG_URL
        from personal_agent.core.agent_knowledge_manager import AgentKnowledgeManager
        from personal_agent.core.agent_memory_manager import AgentMemoryManager
        from personal_agent.core.agno_storage import (
            create_agno_memory,
            create_combined_knowledge_base,
            load_combined_knowledge_base,
        )

    print("🧠 Creating shared memory system...")

    try:
        # 1. Create your existing memory system with timeout
        print("  📝 Creating agno memory...")
        agno_memory = create_agno_memory(storage_dir, debug_mode=debug)

        # 2. Create your existing knowledge system with timeout
        print("  📚 Creating knowledge base...")
        agno_knowledge = create_combined_knowledge_base(storage_dir, knowledge_dir)
        if agno_knowledge:
            print("  📚 Loading knowledge base content...")
            # Add timeout for knowledge loading
            await asyncio.wait_for(
                load_combined_knowledge_base(agno_knowledge, recreate=False),
                timeout=30.0,  # 30 second timeout
            )

        # 3. Create your memory and knowledge managers
        print("  🧠 Creating memory manager...")
        memory_manager = AgentMemoryManager(
            user_id, storage_dir, agno_memory, LIGHTRAG_URL, LIGHTRAG_MEMORY_URL, True
        )
        memory_manager.initialize(agno_memory)

        print("  📖 Creating knowledge manager...")
        knowledge_manager = AgentKnowledgeManager(
            user_id, storage_dir, LIGHTRAG_URL, LIGHTRAG_MEMORY_URL
        )

        # 4. Create Agno's shared Memory object that will be used by the team
        print("  🤝 Creating shared memory...")
        memory_db = SqliteMemoryDb(
            table_name="team_shared_memory",
            db_file=f"{storage_dir}/team_shared_memory.db",
        )

        shared_memory = Memory(
            model=create_ollama_model(use_remote=use_remote), db=memory_db
        )

        print("✅ Shared memory system created successfully")
        return (
            shared_memory,
            memory_manager,
            knowledge_manager,
            agno_memory,
            agno_knowledge,
        )

    except asyncio.TimeoutError:
        print("⚠️ Knowledge loading timed out, proceeding with basic memory only")
        # Fallback: create minimal system without full knowledge loading
        agno_memory = create_agno_memory(storage_dir, debug_mode=debug)
        agno_knowledge = None

        memory_manager = AgentMemoryManager(
            user_id, storage_dir, agno_memory, LIGHTRAG_URL, LIGHTRAG_MEMORY_URL, True
        )
        memory_manager.initialize(agno_memory)

        knowledge_manager = AgentKnowledgeManager(
            user_id, storage_dir, LIGHTRAG_URL, LIGHTRAG_MEMORY_URL
        )

        memory_db = SqliteMemoryDb(
            table_name="team_shared_memory",
            db_file=f"{storage_dir}/team_shared_memory.db",
        )

        shared_memory = Memory(
            model=create_ollama_model(use_remote=use_remote), db=memory_db
        )

        print("✅ Shared memory system created (minimal mode)")
        return (
            shared_memory,
            memory_manager,
            knowledge_manager,
            agno_memory,
            agno_knowledge,
        )

    except Exception as e:
        print(f"❌ Error creating shared memory system: {e}")
        raise


async def create_memory_agent_with_shared_context(
    shared_memory: Memory,
    memory_manager: "AgentMemoryManager",
    knowledge_manager: "AgentKnowledgeManager",
    user_id: str = USER_ID,
    debug: bool = False,
    use_remote: bool = False,
) -> Agent:
    """Create a memory agent that uses the shared memory system."""
    try:
        from ..tools.knowledge_tools import KnowledgeTools
        from ..tools.refactored_memory_tools import AgnoMemoryTools
    except ImportError:
        from personal_agent.tools.knowledge_tools import KnowledgeTools
        from personal_agent.tools.refactored_memory_tools import AgnoMemoryTools

    # Create tools that use your existing managers
    memory_tools = AgnoMemoryTools(memory_manager)
    knowledge_tools = KnowledgeTools(knowledge_manager)

    # Create a standard Agno Agent with shared memory and your tools
    memory_agent = Agent(
        name="Personal AI Agent",
        role="Store and retrieve personal information and factual knowledge",
        model=create_ollama_model(use_remote=use_remote),
        memory=shared_memory,  # Use the shared memory
        tools=[memory_tools, knowledge_tools],
        instructions=[
            "You are a memory and knowledge agent with access to both personal memory and factual knowledge.",
            "CRITICAL TOOL SELECTION RULES:",
            "- Use MEMORY TOOLS (store_user_memory, query_memory) for personal information ABOUT THE USER",
            "- Use KNOWLEDGE TOOLS (ingest_knowledge_text, ingest_knowledge_file) for factual content, documents, poems, stories, articles",
            "- When user says 'store this poem' or 'save this content' -> use ingest_knowledge_text",
            "- When user says 'remember that I...' -> use store_user_memory",
            "- When user asks 'what do you remember about me?' -> use query_memory",
            "- When user asks about stored content/documents -> use query_knowledge_base",
            "EXAMPLES:",
            "- 'Store this poem: [poem text]' -> ingest_knowledge_text(content=poem, title='User Poem')",
            "- 'Remember I like skiing' -> store_user_memory('User likes skiing')",
            "- 'Save this article about AI' -> ingest_knowledge_text(content=article, title='AI Article')",
            "Always execute the tools - do not show JSON or function calls to the user.",
            "Provide natural responses based on the tool results.",
        ],
        agent_id="personal-agent",  # Use hyphen to match team expectations
        user_id=user_id,
        show_tool_calls=debug,
        markdown=True,
    )

    print("✅ Memory agent created with shared context")
    return memory_agent


# Create the team
async def create_team(use_remote: bool = False):
    """Create the team with shared memory context and your existing managers."""

    # CRITICAL: Ensure Docker and user synchronization BEFORE creating any agents
    try:
        from ..config.settings import USER_ID as SETTINGS_USER_ID
        from ..core.docker_integration import ensure_docker_user_consistency
    except ImportError:
        from personal_agent.config.settings import USER_ID as SETTINGS_USER_ID
        from personal_agent.core.docker_integration import (
            ensure_docker_user_consistency,
        )

    print("🐳 Ensuring Docker and user synchronization...")
    docker_ready, docker_message = ensure_docker_user_consistency(
        user_id=SETTINGS_USER_ID, auto_fix=True, force_restart=False
    )

    if docker_ready:
        print(f"✅ Docker synchronization successful: {docker_message}")
    else:
        print(f"⚠️ Docker synchronization failed: {docker_message}")
        print("Proceeding with team creation, but Docker services may be inconsistent")

    # Create shared memory system with your existing managers
    shared_memory, memory_manager, knowledge_manager, agno_memory, agno_knowledge = (
        await create_shared_memory_system(use_remote=use_remote)
    )

    # Create memory agent that uses shared context
    memory_agent = await create_memory_agent_with_shared_context(
        shared_memory,
        memory_manager,
        knowledge_manager,
        debug=True,
        use_remote=use_remote,
    )

    # Update other agents to use shared memory (declare as global to modify)
    global web_agent, finance_agent, writer_agent, calculator_agent
    web_agent.memory = shared_memory
    finance_agent.memory = shared_memory
    writer_agent.memory = shared_memory
    calculator_agent.memory = shared_memory

    # Create the team with shared memory
    agent_team = Team(
        name="Personal Agent Team",
        mode="coordinate",
        model=create_ollama_model(use_remote=use_remote),
        memory=shared_memory,  # CRITICAL: Team uses shared memory
        tools=[
            ReasoningTools(add_instructions=True, add_few_shot=True),
        ],
        members=[
            memory_agent,  # Memory agent with your managers
            web_agent,
            finance_agent,
            writer_agent,
            calculator_agent,
        ],
        instructions=[
            "You are a team of agents using local Ollama models that can answer a variety of questions.",
            "Your primary goal is to collect user memories and factual knowledge.",
            "DELEGATION RULES:",
            "- For storing poems, articles, documents, or factual content -> delegate to Personal AI Agent",
            "- For storing personal info about the user -> delegate to Personal AI Agent",
            "- For web searches -> delegate to Web Agent",
            "- For financial data -> delegate to Finance Agent",
            "- For writing content -> delegate to Writer Agent",
            "- For calculations -> delegate to Calculator Agent",
            "KNOWLEDGE STORAGE EXAMPLES:",
            "- 'Store this poem' -> delegate to Personal AI Agent (will use knowledge tools)",
            "- 'Save this article' -> delegate to Personal AI Agent (will use knowledge tools)",
            "- 'Remember I like skiing' -> delegate to Personal AI Agent (will use memory tools)",
            "You can also answer directly, you don't HAVE to forward the question to a member agent.",
            "Reason about more complex questions before delegating to a member agent.",
            "If the user is only being conversational, encourage them to talk about themselves, life events, and feelings.",
        ],
        markdown=True,
        show_tool_calls=True,
        show_members_responses=True,
        enable_agentic_context=True,  # Enable shared context
        share_member_interactions=True,  # Share interactions between members
        enable_user_memories=True,  # Enable user memory creation
    )

    print("✅ Team created with shared memory context")
    return agent_team


async def cleanup_team(team):
    """Comprehensive cleanup of team resources to prevent ResourceWarnings."""
    print("\n🧹 Cleaning up team resources...")

    try:
        # 1. Close team-level resources
        if hasattr(team, "model") and team.model:
            try:
                await _cleanup_model(team.model, "Team")
            except Exception as e:
                print(f"  ⚠️ Error cleaning up team model: {e}")

        if hasattr(team, "memory") and hasattr(team.memory, "db"):
            try:
                if hasattr(team.memory.db, "close"):
                    await team.memory.db.close()
                print("  ✅ Team memory database closed")
            except Exception as e:
                print(f"  ⚠️ Error closing team memory database: {e}")

        # 2. Close member-level resources
        if hasattr(team, "members") and team.members:
            for i, member in enumerate(team.members):
                member_name = getattr(member, "name", f"Member-{i}")
                print(f"  🔧 Cleaning up {member_name}...")

                # Close member's model
                if hasattr(member, "model") and member.model:
                    try:
                        await _cleanup_model(member.model, member_name)
                    except Exception as e:
                        print(f"    ⚠️ Error cleaning up {member_name} model: {e}")

                # Close member's memory
                if hasattr(member, "memory") and hasattr(member.memory, "db"):
                    try:
                        if hasattr(member.memory.db, "close"):
                            await member.memory.db.close()
                        print(f"    ✅ {member_name} memory database closed")
                    except Exception as e:
                        print(f"    ⚠️ Error closing {member_name} memory database: {e}")

                # Close member's tools
                if hasattr(member, "tools") and member.tools:
                    for j, tool in enumerate(member.tools):
                        if tool:  # Check if tool is not None
                            tool_name = getattr(tool.__class__, "__name__", f"Tool-{j}")
                            try:
                                await _cleanup_tool(tool, f"{member_name}-{tool_name}")
                            except Exception as e:
                                print(
                                    f"    ⚠️ Error cleaning up {member_name}-{tool_name}: {e}"
                                )

        # 3. Force garbage collection to help with cleanup
        import gc

        gc.collect()

        # 4. Give asyncio time to close remaining connections
        await asyncio.sleep(0.5)

        print("  ✅ Team cleanup completed")

    except Exception as e:
        print(f"  ❌ Error during team cleanup: {e}")


async def _cleanup_model(model, model_name: str):
    """Clean up a specific model's resources."""
    try:
        # Close HTTP sessions in the model
        if hasattr(model, "_session") and model._session:
            if not model._session.closed:
                await model._session.close()
            print(f"    ✅ {model_name} model HTTP session closed")

        if hasattr(model, "session") and model.session:
            if not model.session.closed:
                await model.session.close()
            print(f"    ✅ {model_name} model session closed")

        # Close any client connections
        if hasattr(model, "client"):
            if hasattr(model.client, "close"):
                await model.client.close()
            elif hasattr(model.client, "_session") and model.client._session:
                if not model.client._session.closed:
                    await model.client._session.close()
            print(f"    ✅ {model_name} model client closed")

        # Handle OllamaTools specific cleanup
        if hasattr(model, "_client") and model._client:
            if hasattr(model._client, "close"):
                await model._client.close()
            print(f"    ✅ {model_name} Ollama client closed")

    except Exception as e:
        print(f"    ⚠️ Error cleaning up {model_name} model: {e}")


async def _cleanup_tool(tool, tool_name: str):
    """Clean up a specific tool's resources."""
    try:
        # Close HTTP sessions in tools
        if hasattr(tool, "_session") and tool._session:
            if not tool._session.closed:
                await tool._session.close()
            print(f"    ✅ {tool_name} tool HTTP session closed")

        if hasattr(tool, "session") and tool.session:
            if not tool.session.closed:
                await tool.session.close()
            print(f"    ✅ {tool_name} tool session closed")

        # Handle DuckDuckGo tools specifically
        if hasattr(tool, "ddgs"):
            if hasattr(tool.ddgs, "_session") and tool.ddgs._session:
                if not tool.ddgs._session.closed:
                    await tool.ddgs._session.close()
                print(f"    ✅ {tool_name} DuckDuckGo session closed")

            if hasattr(tool.ddgs, "close"):
                await tool.ddgs.close()
                print(f"    ✅ {tool_name} DuckDuckGo client closed")

        # Handle YFinance tools
        if hasattr(tool, "_session") and "yfinance" in str(type(tool)).lower():
            if tool._session and not tool._session.closed:
                await tool._session.close()
                print(f"    ✅ {tool_name} YFinance session closed")

        # Close any other client connections
        if hasattr(tool, "client"):
            if hasattr(tool.client, "close"):
                await tool.client.close()
            elif hasattr(tool.client, "_session") and tool.client._session:
                if not tool.client._session.closed:
                    await tool.client._session.close()
            print(f"    ✅ {tool_name} tool client closed")

    except Exception as e:
        print(f"    ⚠️ Error cleaning up {tool_name} tool: {e}")


# Main execution
async def main(use_remote: bool = False):
    """Main function to run the team with an interactive chat loop."""

    print("🤖 Ollama Multi-Purpose Reasoning Team")
    print("=" * 50)
    print("Initializing team with memory and knowledge capabilities...")
    print("This may take a moment on first run...")

    try:
        # Create the team
        team = await create_team(use_remote=use_remote)

        print("\n✅ Team initialized successfully!")
        print("\nTeam Members:")
        print(
            "- 🧠 Memory Agent: Store and retrieve personal information and knowledge"
        )
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
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("\n👋 Goodbye! Thanks for using the Personal Agent Team!")
                    # Cleanup team resources
                    await cleanup_team(team)
                    break

                elif user_input.lower() == "help":
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

                elif user_input.lower() == "clear":
                    import os

                    os.system("clear" if os.name == "posix" else "cls")
                    print("🤖 Personal Agent Team")
                    print("💬 Chat cleared. How can I help you?")
                    continue

                elif user_input.lower() == "examples":
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
    parser = argparse.ArgumentParser(
        description="Run the Ollama Multi-Purpose Reasoning Team"
    )
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama server"
    )
    args = parser.parse_args()

    print("Starting Ollama Multi-Purpose Reasoning Team...")
    asyncio.run(main(use_remote=args.remote))


if __name__ == "__main__":
    # Run the main function
    cli_main()
