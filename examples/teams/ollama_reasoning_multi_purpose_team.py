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
import os
from pathlib import Path
from textwrap import dedent

from dotenv import load_dotenv

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
    LLM_MODEL,
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

# Load environment variables
load_dotenv()

cwd = Path(__file__).parent.resolve()

def create_ollama_model(model_name: str = LLM_MODEL) -> OllamaTools:
    """Create an Ollama model using your AgentModelManager."""
    model_manager = AgentModelManager(
        model_provider="ollama",
        model_name=model_name,
        ollama_base_url=OLLAMA_URL,
        seed=None
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
        enable_agentic_memory=False,  # Disable to avoid conflicts
        enable_user_memories=False,   # Use our custom tools instead
        storage=agno_storage,
        knowledge=agno_knowledge,
        memory=agno_memory,
    )
    
    return agent

# Create the team
async def create_team():
    """Create the team with all agents including the memory agent."""
    
    # Create memory agent (must be async)
    memory_agent = await create_memory_agent()
    
    # Create the team
    agent_team = Team(
        name="Ollama Multi-Purpose Team",
        mode="coordinate",
        model=create_ollama_model(),
        tools=[
            ReasoningTools(add_instructions=True, add_few_shot=True),
        ],
        members=[
            web_agent,
            finance_agent,
            writer_agent,
            calculator_agent,
            memory_agent,  # Add the memory agent
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

# Main execution
async def main():
    """Main function to run the team."""
    
    # Create the team
    team = await create_team()
    
    # Example queries
    queries = [
        "Hi! What are you capable of doing?",
        "Remember that I love skiing and live in Colorado",
        "What do you remember about me?",
        "Give me a financial analysis of NVDA",
        "Calculate the square root of 144",
        "Write a short poem about AI agents working together",
    ]
    
    # Run example queries
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        
        await team.aprint_response(query, stream=True)
        print("\n")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())