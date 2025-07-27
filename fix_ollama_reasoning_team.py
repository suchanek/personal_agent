#!/usr/bin/env python3
"""
Fix for Ollama Reasoning Team - Replace Qwen3 with Llama3.2 for tool calling
"""

import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Update your imports to use Llama3.2
from agno.agent import Agent
from agno.models.ollama.tools import OllamaTools
from agno.team.team import Team
from agno.tools.calculator import CalculatorTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.python import PythonTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools

# Import your personal agent components
from src.personal_agent.config.settings import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    LIGHTRAG_URL,
    LIGHTRAG_MEMORY_URL,
    OLLAMA_URL,
    USER_ID,
)
from src.personal_agent.core.agent_knowledge_manager import AgentKnowledgeManager
from src.personal_agent.core.agent_memory_manager import AgentMemoryManager
from src.personal_agent.core.agent_model_manager import AgentModelManager
from src.personal_agent.core.agno_storage import (
    create_agno_memory,
    create_agno_storage,
    create_combined_knowledge_base,
    load_combined_knowledge_base,
)
from src.personal_agent.tools.knowledge_tools import KnowledgeTools
from src.personal_agent.tools.refactored_memory_tools import AgnoMemoryTools

load_dotenv()

def create_ollama_model(model_name: str = "llama3.2:8b") -> OllamaTools:
    """Create an Ollama model using Llama3.2 for proper tool calling."""
    model_manager = AgentModelManager(
        model_provider="ollama",
        model_name=model_name,
        ollama_base_url=OLLAMA_URL,
        seed=None
    )
    return model_manager.create_model()

# Web search agent using Llama3.2
web_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    model=create_ollama_model("llama3.2:8b"),  # Changed from qwen3:8b
    tools=[DuckDuckGoTools(cache_results=True)],
    instructions=["Always include sources"],
    show_tool_calls=True,
)

# Finance agent using Llama3.2
finance_agent = Agent(
    name="Finance Agent",
    role="Get financial data",
    model=create_ollama_model("llama3.2:8b"),  # Changed from qwen3:8b
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

# Writer agent using Llama3.2
writer_agent = Agent(
    name="Writer Agent",
    role="Write content",
    model=create_ollama_model("llama3.2:8b"),  # Changed from qwen3:8b
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

# Calculator agent using Llama3.2
calculator_agent = Agent(
    name="Calculator Agent",
    model=create_ollama_model("llama3.2:8b"),  # Changed from qwen3:8b
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
    """Create a memory agent using Llama3.2 for proper tool calling."""
    
    # 1. Create Agno storage
    agno_storage = create_agno_storage(storage_dir)
    
    # 2. Create combined knowledge base
    agno_knowledge = create_combined_knowledge_base(
        storage_dir, knowledge_dir, agno_storage
    )
    
    # 3. Load knowledge base content
    if agno_knowledge:
        await load_combined_knowledge_base(agno_knowledge, recreate=False)
    
    # 4. Create memory with SemanticMemoryManager
    agno_memory = create_agno_memory(storage_dir, debug_mode=debug)
    
    # 5. Initialize managers
    memory_manager = AgentMemoryManager(
        user_id=user_id,
        storage_dir=storage_dir,
        agno_memory=agno_memory,
        lightrag_url=LIGHTRAG_URL,
        lightrag_memory_url=LIGHTRAG_MEMORY_URL,
        enable_memory=True,
    )
    
    memory_manager.initialize(agno_memory)
    
    knowledge_manager = AgentKnowledgeManager(
        user_id=user_id,
        storage_dir=storage_dir,
        lightrag_url=LIGHTRAG_URL,
        lightrag_memory_url=LIGHTRAG_MEMORY_URL,
    )
    
    # 6. Create tool instances
    knowledge_tools = KnowledgeTools(knowledge_manager)
    memory_tools = AgnoMemoryTools(memory_manager)
    
    # 7. Create the Agent with Llama3.2
    agent = Agent(
        name="Memory Agent",
        role="Store and retrieve personal information and knowledge",
        model=create_ollama_model("llama3.2:8b"),  # Changed from qwen3:8b
        tools=[knowledge_tools, memory_tools],
        instructions=[
            "You are a memory and knowledge agent with access to both personal memory and factual knowledge.",
            "Use memory tools for personal information about the user.",
            "Use knowledge tools for factual information and documents.",
            "Always search your memory when asked about the user.",
            "Always search your knowledge base when asked about factual information.",
            "Store new personal information in memory and new factual information in knowledge.",
        ],
        markdown=True,
        show_tool_calls=True,
        user_id=user_id,
        enable_agentic_memory=False,
        enable_user_memories=False,
        storage=agno_storage,
        knowledge=agno_knowledge,
        memory=agno_memory,
    )
    
    return agent

async def create_fixed_team():
    """Create the team with Llama3.2 models for proper tool calling."""
    
    # Create memory agent
    memory_agent = await create_memory_agent()
    
    # Create the team with Llama3.2
    agent_team = Team(
        name="Fixed Ollama Multi-Purpose Team",
        mode="coordinate",
        model=create_ollama_model("llama3.2:8b"),  # Changed from qwen3:8b
        tools=[
            ReasoningTools(add_instructions=True, add_few_shot=True),
        ],
        members=[
            web_agent,
            finance_agent,
            writer_agent,
            calculator_agent,
            memory_agent,
        ],
        instructions=[
            "You are a team of agents using local Ollama models that can answer a variety of questions.",
            "You can use your member agents to answer the questions.",
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

async def test_fixed_team():
    """Test the fixed team with tool calling."""
    
    print("=== Testing Fixed Ollama Team with Llama3.2 ===\n")
    
    # Create the fixed team
    team = await create_fixed_team()
    
    # Test queries that require tool calling
    test_queries = [
        "Search for the latest news about artificial intelligence",
        "Calculate the square root of 256",
        "Remember that I am a software engineer who loves Python",
        "What do you remember about me?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        try:
            await team.aprint_response(query, stream=True)
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n")

if __name__ == "__main__":
    asyncio.run(test_fixed_team())