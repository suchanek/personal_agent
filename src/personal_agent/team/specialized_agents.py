"""
Specialized Agents for Personal Agent Team

This module defines individual specialized agents that work together as a team.
Each agent has a specific role and set of tools, following the pattern from
examples/teams/reasoning_multi_purpose_team.py
"""

from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Union

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.tools.calculator import CalculatorTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.file import FileTools
from agno.tools.github import GithubTools
from agno.tools.knowledge import KnowledgeTools
from agno.tools.pubmed import PubmedTools
from agno.tools.python import PythonTools
from agno.tools.shell import ShellTools
from agno.tools.yfinance import YFinanceTools

from ..config import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    HOME_DIR,
    LLM_MODEL,
    OLLAMA_URL,
)
from ..config.model_contexts import get_model_context_size_sync
from ..tools.personal_agent_tools import PersonalAgentFilesystemTools
from ..utils import setup_logging

logger = setup_logging(__name__)

SMALL_QWEN = "qwen3:1.7b"


def _create_model(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    temperature: float = 0.3,
) -> Union[OpenAIChat, Ollama]:
    """Create the appropriate model instance based on provider.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param temperature: Model Temperature
    :return: Configured model instance
    :raises ValueError: If unsupported model provider is specified
    """
    if model_provider == "openai":
        logger.info("Using OpenAI model %s", model_name)
        return OpenAIChat(id=model_name)
    elif model_provider == "ollama":
        # Get dynamic context size for this model
        context_size, detection_method = get_model_context_size_sync(
            model_name, ollama_base_url
        )

        logger.info(
            "Using context size %d for model %s (detected via: %s)",
            context_size,
            model_name,
            detection_method,
        )

        return Ollama(
            id=model_name,
            host=ollama_base_url,
            options={
                "num_ctx": context_size,
                "temperature": temperature,
            },
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")


def create_web_research_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    debug: bool = False,
) -> Agent:
    """Create a specialized web research agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param debug: Enable debug mode
    :return: Configured web research agent
    """
    model = _create_model(model_provider, model_name, ollama_base_url)

    agent = Agent(
        name="Web Research Agent",
        role="Search the web for information and current events",
        model=model,
        debug_mode=debug,
        tools=[DuckDuckGoTools(cache_results=True)],
        instructions=[
            "You are a specialized web research agent focused on finding current information online.",
            "Your primary functions are:",
            "1. Search the web for current events and news",
            "2. Find specific information requested by users",
            "3. Provide up-to-date information from reliable sources",
            "",
            "RESEARCH GUIDELINES:",
            "- Always include sources in your responses",
            "- Focus on recent and reliable information",
            "- Use multiple search queries if needed for comprehensive results",
            "- Summarize findings clearly and concisely",
            "- When searching for news, use the news search function",
        ],
        markdown=True,
        show_tool_calls=False,  # Always hide tool calls for clean responses
        add_name_to_instructions=True,
    )

    logger.info("Created Web Research Agent")
    return agent


def create_finance_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    debug: bool = False,
) -> Agent:
    """Create a specialized finance agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param debug: Enable debug mode
    :return: Configured finance agent
    """
    model = _create_model(model_provider, model_name, ollama_base_url)

    agent = Agent(
        name="Finance Agent",
        role="Get financial data and perform market analysis",
        model=model,
        tools=[
            YFinanceTools(
                stock_price=True,
                analyst_recommendations=True,
                company_info=True,
                company_news=True,
                stock_fundamentals=True,
                key_financial_ratios=True,
            )
        ],
        instructions=[
            "You are a specialized finance agent focused on financial data and market analysis.",
            "Your primary functions are:",
            "1. Get current stock prices and market data",
            "2. Analyze company fundamentals and financial ratios",
            "3. Provide analyst recommendations and company news",
            "4. Perform financial analysis and comparisons",
            "",
            "FINANCIAL ANALYSIS GUIDELINES:",
            "- Use tables to display numerical data clearly",
            "- Provide context for financial metrics",
            "- Include relevant company news when analyzing stocks",
            "- Explain financial terms for better understanding",
            "- Always specify the data source and timestamp",
        ],
        markdown=True,
        show_tool_calls=False,  # Always hide tool calls for clean responses
        add_name_to_instructions=True,
    )

    logger.info("Created Finance Agent")
    return agent


def create_calculator_agent(
    model_provider: str = "ollama",
    model_name: str = SMALL_QWEN,
    ollama_base_url: str = OLLAMA_URL,
    debug: bool = False,
) -> Agent:
    """Create a specialized calculator agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param debug: Enable debug mode
    :return: Configured calculator agent
    """
    model = _create_model(model_provider, model_name, ollama_base_url)

    agent = Agent(
        name="Calculator Agent",
        role="Perform calculations and data analysis",
        model=model,
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
        instructions=[
            "You are a specialized calculator agent focused ONLY on mathematical calculations and data analysis.",
            "Your primary functions are:",
            "1. Perform basic and advanced mathematical calculations",
            "2. Execute Python code for complex data analysis",
            "3. Create visualizations and charts when helpful",
            "4. Solve mathematical problems step by step",
            "",
            "CALCULATION GUIDELINES:",
            "- Show your work and explain calculation steps",
            "- Use appropriate tools for different types of calculations",
            "- Provide clear, formatted results",
            "- Create visualizations for data when helpful",
            "- Verify complex calculations using multiple methods when possible",
            "",
            "IMPORTANT RESTRICTIONS:",
            "- DO NOT handle memory-related queries (what do you remember, personal information, etc.)",
            "- DO NOT generate fake memory data or simulate user information",
            "- Only handle mathematical calculations and data analysis tasks",
            "- If asked about memories or personal info, decline and suggest asking the Memory Agent",
        ],
        markdown=True,
        show_tool_calls=False,  # Always hide tool calls for clean responses
        add_name_to_instructions=True,
    )

    logger.info("Created Calculator Agent")
    return agent


def create_file_operations_agent(
    model_provider: str = "ollama",
    model_name: str = SMALL_QWEN,
    ollama_base_url: str = OLLAMA_URL,
    debug: bool = False,
) -> Agent:
    """Create a specialized file operations agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param debug: Enable debug mode
    :return: Configured file operations agent
    """
    model = _create_model(model_provider, model_name, ollama_base_url)

    agent = Agent(
        name="File Operations Agent",
        role="Handle file system operations and shell commands",
        model=model,
        debug_mode=debug,
        tools=[
            PersonalAgentFilesystemTools(),
            ShellTools(base_dir=HOME_DIR),
        ],
        instructions=[
            "You are a specialized file operations agent focused on file system tasks and shell commands.",
            "Your primary functions are:",
            "1. Read and write files",
            "2. List directory contents and navigate file systems",
            "3. Execute shell commands safely",
            "4. Manage file permissions and operations",
            "",
            "FILE OPERATION GUIDELINES:",
            "- Always confirm file operations before executing destructive commands",
            "- Provide clear feedback on operation success/failure",
            "- Use appropriate file paths and handle errors gracefully",
            "- Be cautious with shell commands that could affect system stability",
            "- Explain what file operations will do before performing them",
        ],
        markdown=True,
        show_tool_calls=False,  # Always hide tool calls for clean responses
        add_name_to_instructions=True,
    )

    logger.info("Created File Operations Agent")
    return agent


def create_pubmed_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    debug: bool = False,
) -> Agent:
    """Create a specialized PubMed research agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param debug: Enable debug mode
    :return: Configured PubMed research agent
    """
    model = _create_model(model_provider, model_name, ollama_base_url)

    agent = Agent(
        name="PubMed Research Agent",
        role="Search and analyze biomedical and life science literature",
        model=model,
        debug_mode=debug,
        tools=[PubmedTools()],
        instructions=[
            "You are a specialized PubMed research agent focused on biomedical and life science literature.",
            "Your primary functions are:",
            "1. Search PubMed database for scientific articles and research papers",
            "2. Retrieve detailed information about specific publications",
            "3. Analyze and summarize biomedical research findings",
            "4. Provide evidence-based information from peer-reviewed sources",
            "",
            "PUBMED RESEARCH GUIDELINES:",
            "- Always cite PubMed IDs (PMIDs) and DOIs when available",
            "- Focus on peer-reviewed, high-quality research articles",
            "- Provide publication dates and journal information",
            "- Summarize key findings, methodology, and conclusions clearly",
            "- Use appropriate medical and scientific terminology",
            "- When searching, use relevant MeSH terms and keywords",
            "- Distinguish between different types of studies (RCT, meta-analysis, case study, etc.)",
            "- Include sample sizes and statistical significance when relevant",
            "",
            "IMPORTANT RESTRICTIONS:",
            "- DO NOT provide medical advice or diagnoses",
            "- Always recommend consulting healthcare professionals for medical decisions",
            "- Focus on presenting research findings objectively",
            "- Clearly indicate when information is preliminary or requires further research",
        ],
        markdown=True,
        show_tool_calls=False,  # Always hide tool calls for clean responses
        add_name_to_instructions=True,
    )

    logger.info("Created PubMed Research Agent")
    return agent


def create_writer_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    debug: bool = False,
) -> Agent:
    """Create a specialized writing agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param debug: Enable debug mode
    :return: Configured writing agent
    """
    model = _create_model(model_provider, model_name, ollama_base_url)

    agent = Agent(
        name="Writer Agent",
        role="Create, edit, and improve written content",
        model=model,
        debug_mode=debug,
        tools=[FileTools()],  # File tools for reading/writing documents
        instructions=[
            "You are a specialized writing agent focused on creating, editing, and improving written content.",
            "Your primary functions are:",
            "1. Write original content (articles, essays, reports, stories, etc.)",
            "2. Edit and improve existing text for clarity, style, and grammar",
            "3. Adapt writing style for different audiences and purposes",
            "4. Create structured documents with proper formatting",
            "5. Proofread and provide feedback on written content",
            "",
            "WRITING GUIDELINES:",
            "- Always consider the target audience and purpose",
            "- Use clear, concise, and engaging language",
            "- Maintain consistent tone and style throughout",
            "- Structure content logically with proper headings and paragraphs",
            "- Check for grammar, spelling, and punctuation errors",
            "- Provide constructive feedback when editing others' work",
            "- Use appropriate formatting (markdown, headings, lists, etc.)",
            "",
            "CONTENT TYPES YOU CAN HELP WITH:",
            "- Business documents (reports, proposals, emails)",
            "- Academic writing (essays, research papers, summaries)",
            "- Creative writing (stories, poems, scripts)",
            "- Technical documentation (guides, manuals, README files)",
            "- Marketing content (copy, descriptions, social media posts)",
            "- Personal writing (letters, journals, blogs)",
            "",
            "IMPORTANT GUIDELINES:",
            "- Always maintain originality and avoid plagiarism",
            "- Respect copyright and intellectual property",
            "- Provide citations when referencing sources",
            "- Ask for clarification on requirements when needed",
            "- Offer multiple options or approaches when appropriate",
        ],
        markdown=True,
        show_tool_calls=False,  # Always hide tool calls for clean responses
        add_name_to_instructions=True,
    )

    logger.info("Created Writer Agent")
    return agent


# This is the PersonalAgent with full knowledge and memory tools.
def create_knowledge_memory_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    storage_dir: str = AGNO_STORAGE_DIR,
    knowledge_dir: str = AGNO_KNOWLEDGE_DIR,
    user_id: str = "default_user",
    debug: bool = False,
) -> "AgnoPersonalAgent":
    """Create a knowledge/memory agent using PersonalAgnoAgent with all_tools=False.

    This agent is specifically configured for knowledge and memory operations within
    a team context, using the full PersonalAgnoAgent capabilities but without
    built-in tools to avoid conflicts with team coordination.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param storage_dir: Directory for storage files
    :param knowledge_dir: Directory containing knowledge files to load
    :param user_id: User identifier for memory operations
    :param debug: Enable debug mode
    :return: Configured PersonalAgnoAgent instance for knowledge/memory operations
    """
    from ..core.agno_agent import AgnoPersonalAgent

    logger.info(
        "Creating Knowledge/Memory Agent using PersonalAgnoAgent with all_tools=False"
    )

    # Create PersonalAgnoAgent with specific configuration for team use
    agent = AgnoPersonalAgent(
        model_provider=model_provider,
        model_name=model_name,
        enable_memory=True,  # Enable memory system
        enable_mcp=False,  # Disable MCP to avoid conflicts
        storage_dir=storage_dir,
        knowledge_dir=knowledge_dir,
        debug=debug,
        ollama_base_url=ollama_base_url,
        user_id=user_id,
        recreate=False,
        alltools=False,  # Disable built-in tools for team context
        initialize_agent=True,  # Force initialization to ensure proper model setup
    )

    # Force initialization to ensure tools are properly loaded
    import asyncio

    try:
        # Try to get the current event loop
        asyncio.get_running_loop()
        # If we're in a running loop, we need to handle this differently
        logger.warning("Event loop detected - agent will initialize lazily")
    except RuntimeError:
        # No running event loop, safe to initialize now
        asyncio.run(agent.initialize())
        logger.info(
            "Agent initialized synchronously with %d tools",
            len(agent.tools) if agent.tools else 0,
        )

    # Override the agent name and role for team context
    agent.name = "Personal Memory and Knowledge Agent"
    agent.role = "Handle personal information, memories, and knowledge queries"

    logger.info(
        "Created Knowledge/Memory Agent using PersonalAgnoAgent (user_id=%s, memory=%s)",
        user_id,
        agent.enable_memory,
    )

    return agent
