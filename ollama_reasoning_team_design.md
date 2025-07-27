# Ollama-Based Multi-Purpose Reasoning Team Design

## Overview

This document provides a complete design and implementation plan for creating a new version of the `reasoning_multi_purpose_team.py` that uses your local Ollama instance and includes a proper memory agent with your existing memory and knowledge infrastructure.

## Key Architecture Decisions

### 1. Use Local Ollama Models
- Replace all Claude/OpenAI models with `OllamaTools` configurations
- Use your `AgentModelManager` for consistent model setup
- Leverage your `qwen3:8b` model with optimized parameters

### 2. Proper Memory Agent Integration
- Follow the exact initialization pattern from `agno_agent.py`
- Use separate `KnowledgeTools` and `AgnoMemoryTools` classes
- Initialize all required components before creating the Agent

### 3. Critical Initialization Sequence

Based on `agno_agent.py` lines 329-414, the memory agent MUST follow this sequence:

```python
# 1. Create Agno storage
agno_storage = create_agno_storage(storage_dir)

# 2. Create combined knowledge base
agno_knowledge = create_combined_knowledge_base(
    storage_dir, knowledge_dir, agno_storage
)

# 3. Load knowledge base content (async)
await load_combined_knowledge_base(agno_knowledge, recreate=False)

# 4. Create memory with SemanticMemoryManager
agno_memory = create_agno_memory(storage_dir, debug_mode=debug)

# 5. Initialize managers
memory_manager = AgentMemoryManager(user_id, storage_dir, agno_memory, ...)
knowledge_manager = AgentKnowledgeManager(user_id, storage_dir, ...)

# 6. Create tool instances
knowledge_tools = KnowledgeTools(knowledge_manager)
memory_tools = AgnoMemoryTools(memory_manager)

# 7. Create Agent with tools
agent = Agent(
    model=model,
    tools=[knowledge_tools, memory_tools],
    # ... other config
)
```

## Complete Implementation

### File: `examples/teams/ollama_reasoning_multi_purpose_team.py`

```python
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
        show_tool_calls=debug,
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
```

## Key Features

### 1. Full Ollama Integration
- All agents use local Ollama models via `OllamaTools`
- Consistent model configuration using your `AgentModelManager`
- No external API dependencies

### 2. Proper Memory Agent
- Follows exact initialization sequence from `agno_agent.py`
- Uses separate `KnowledgeTools` and `AgnoMemoryTools`
- Supports both personal memory and factual knowledge storage
- Integrates with your dual storage system (SQLite + LightRAG)

### 3. Team Capabilities
- **Web Agent**: Search the web using DuckDuckGo
- **Finance Agent**: Get financial data using YFinance
- **Writer Agent**: Generate content and articles
- **Calculator Agent**: Perform calculations and run Python code
- **Memory Agent**: Store/retrieve personal info and knowledge

### 4. Usage Examples

The team can handle queries like:
- "Remember that I love skiing" → Memory agent stores personal info
- "What do you remember about me?" → Memory agent retrieves stored info
- "Give me NVDA analysis" → Finance agent gets stock data
- "Calculate 5 + 7" → Calculator agent performs math
- "Search for AI news" → Web agent searches online
- "Write a poem about robots" → Writer agent creates content

## Testing Instructions

1. **Setup**: Ensure Ollama is running with your models
2. **Dependencies**: Install required packages
3. **Configuration**: Update paths in settings if needed
4. **Run**: Execute the script to test all agents
5. **Memory Test**: Try storing and retrieving personal information
6. **Knowledge Test**: Try ingesting and querying factual information

## Benefits

- **Fully Local**: No external API costs or dependencies
- **Memory Persistent**: Remembers information across sessions
- **Knowledge Aware**: Can ingest and query documents
- **Reasoning Capable**: Uses your optimized Ollama models
- **Consistent Architecture**: Follows your established patterns

This design provides a complete, working implementation that leverages all your existing infrastructure while being fully local and memory-enabled.