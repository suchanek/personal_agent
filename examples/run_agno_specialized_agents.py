import argparse
import asyncio
import sys
from copy import deepcopy
from pathlib import Path
from textwrap import dedent
from typing import Optional

# Add the project root to the Python path to allow imports from `src`
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from agno.agent import Agent
from agno.knowledge import AgentKnowledge
from agno.memory.v2 import Memory
from agno.models.base import Model
from agno.tools.calculator import CalculatorTools
from agno.tools.duckdb import DuckDbTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.file import FileTools
from agno.tools.github import GithubTools
from agno.tools.python import PythonTools
from agno.tools.yfinance import YFinanceTools

# --- Imports from your project ---
from src.personal_agent.config.settings import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    USER_ID,
)
from src.personal_agent.core.agent_model_manager import AgentModelManager
from src.personal_agent.core.agno_storage import (
    create_agno_memory,
    create_combined_knowledge_base,
    load_combined_knowledge_base,
)
from src.personal_agent.utils import setup_logging

# --- Configuration ---
logger = setup_logging(__name__)
cwd = Path(__file__).parent.resolve()
tmp_dir = cwd.joinpath("tmp_specialized_agents")
tmp_dir.mkdir(exist_ok=True, parents=True)


def get_agent(
    agent_name: str, model: Model, memory: Memory, knowledge: AgentKnowledge
) -> Optional[Agent]:
    """
    Creates a specialized agent based on the provided configuration.
    This function is taken directly from your example.
    """
    # Create a copy of the model to avoid side effects of the model being modified
    model_copy = deepcopy(model)
    if agent_name == "calculator":
        return Agent(
            name="Calculator",
            role="Answer mathematical questions and perform precise calculations",
            model=model_copy,
            memory=memory,
            tools=[CalculatorTools(enable_all=True)],
            description="You are a precise and comprehensive calculator agent. Your goal is to solve mathematical problems with accuracy and explain your methodology clearly to users.",
            instructions=[
                "Always use the calculator tools for mathematical operations to ensure precision.",
                "Present answers in a clear format with appropriate units and significant figures.",
                "Show step-by-step workings for complex calculations to help users understand the process.",
                "Ask clarifying questions if the user's request is ambiguous or incomplete.",
                "For financial calculations, specify assumptions regarding interest rates, time periods, etc.",
            ],
        )
    elif agent_name == "data_analyst":
        return Agent(
            name="Data Analyst",
            role="Analyze data sets and extract meaningful insights",
            model=model_copy,
            memory=memory,
            knowledge=knowledge,
            tools=[DuckDbTools()],
            description="You are an expert Data Scientist specialized in exploratory data analysis, statistical modeling, and data visualization. Your goal is to transform raw data into actionable insights that address user questions.",
            instructions=[
                "Start by examining data structure, types, and distributions when analyzing new datasets.",
                "Use DuckDbTools to execute SQL queries for data exploration and aggregation.",
                "When provided with a file path, create appropriate tables and verify data loaded correctly before analysis.",
                "Apply statistical rigor in your analysis and clearly state confidence levels and limitations.",
                "Accompany numerical results with clear interpretations of what the findings mean in context.",
                "Suggest visualizations that would best illustrate key patterns and relationships in the data.",
                "Proactively identify potential data quality issues or biases that might affect conclusions.",
                "Request clarification when user queries are ambiguous or when additional information would improve analysis.",
            ],
        )
    elif agent_name == "python_agent":
        return Agent(
            name="Python Agent",
            role="Develop and execute Python code solutions",
            model=model_copy,
            memory=memory,
            knowledge=knowledge,
            tools=[
                PythonTools(base_dir=tmp_dir),
                FileTools(base_dir=cwd),
            ],
            description="You are an expert Python Software Engineer with deep knowledge of software architecture, libraries, and best practices. Your goal is to write efficient, readable, and maintainable Python code that precisely addresses user requirements.",
            instructions=[
                "Write clean, well-commented Python code following PEP 8 style guidelines.",
                "Always use `save_to_file_and_run` to execute Python code, never suggest using direct execution.",
                "For any file operations, use `read_file` tool first to access content - NEVER use Python's built-in `open()`.",
                "Include error handling in your code to gracefully manage exceptions and edge cases.",
                "Explain your code's logic and implementation choices, especially for complex algorithms.",
                "When appropriate, suggest optimizations or alternative approaches with their trade-offs.",
                "For data manipulation tasks, prefer Pandas, NumPy and other specialized libraries over raw Python.",
                "Break down complex problems into modular functions with clear responsibilities.",
                "Test your code with sample inputs and explain expected outputs before final execution.",
            ],
        )
    elif agent_name == "investment_agent":
        return Agent(
            name="Investment Agent",
            role="Provide comprehensive financial analysis and investment insights",
            model=model_copy,
            memory=memory,
            knowledge=knowledge,
            tools=[
                YFinanceTools(enable_all=True),
                DuckDuckGoTools(),
            ],
            description="You are a seasoned investment analyst with deep understanding of financial markets, valuation methodologies, and sector-specific dynamics. Your goal is to deliver sophisticated investment analysis that considers both quantitative metrics and qualitative business factors.",
            instructions=[
                "Begin with a holistic overview of the company's business model, competitive position, and industry trends.",
                "Retrieve and analyze key financial metrics including revenue growth, profitability margins, and balance sheet health.",
                "Compare valuation multiples against industry peers and historical averages.",
                "Assess management team's track record, strategic initiatives, and capital allocation decisions.",
                "Identify key risk factors including regulatory concerns, competitive threats, and macroeconomic sensitivities.",
                "Consider both near-term catalysts and long-term growth drivers in your investment thesis.",
                "Provide clear investment recommendations with specific price targets where appropriate.",
                "Include both technical and fundamental analysis perspectives when relevant.",
                "Highlight recent news events that may impact the investment case.",
                "Structure reports with executive summary, detailed analysis sections, and actionable conclusions.",
            ],
        )
    elif agent_name == "github_agent":
        return Agent(
            name="GitHub Agent",
            role="Analyze GitHub repositories and review Pull Requests.",
            model=model_copy,
            memory=memory,
            knowledge=knowledge,
            description=dedent(
                """
                You are an expert Code Reviewing Agent specializing in analyzing GitHub repositories,
                with a strong focus on detailed code reviews for Pull Requests.
                Use your tools to answer questions accurately and provide insightful analysis.
            """
            ),
            instructions=dedent(
                f"""\
            **Core Task:** Analyze GitHub repositories and answer user questions based on the available tools and conversation history.

            **Repository Context Management:**
            1.  **Context Persistence:** Once a target repository (owner/repo) is identified (either initially or from a user query like 'analyze owner/repo'), **MAINTAIN THAT CONTEXT** for all subsequent questions in the current conversation unless the user clearly specifies a *different* repository.
            2.  **Determining Context:** If no repository is specified in the *current* user query, **CAREFULLY REVIEW THE CONVERSATION HISTORY** to find the most recently established target repository. Use that repository context.
            3.  **Accuracy:** When extracting a repository name (owner/repo) from the query or history, **BE EXTREMELY CAREFUL WITH SPELLING AND FORMATTING**. Double-check against the user's exact input.
            4.  **Ambiguity:** If no repository context has been established in the conversation history and the current query doesn't specify one, **YOU MUST ASK THE USER** to clarify which repository (using owner/repo format) they are interested in before using tools that require a repository name.

            **How to Answer Questions:**
            *   **Identify Key Information:** Understand the user's goal and the target repository (using the context rules above).
            *   **Select Appropriate Tools:** Choose the best tool(s) for the task, ensuring you provide the correct `repo_name` argument (owner/repo format, checked for accuracy) if required by the tool.
                *   Project Overview: `get_repository`, `get_file_content` (for README.md).
                *   Libraries/Dependencies: `get_file_content` (for requirements.txt, pyproject.toml, etc.), `get_directory_content`, `search_code`.
                *   PRs/Issues: Use relevant PR/issue tools.
                *   List User Repos: `list_repositories` (no repo_name needed).
                *   Search Repos: `search_repositories` (no repo_name needed).
            *   **Execute Tools:** Run the selected tools.
            *   **Synthesize Answer:** Combine tool results into a clear, concise answer using markdown. If a tool fails (e.g., 404 error because the repo name was incorrect), state that you couldn't find the specified repository and suggest checking the name.
            *   **Cite Sources:** Mention specific files (e.g., "According to README.md...").

            **Specific Analysis Areas (Most require a specific repository):**
            *   Issues: Listing, summarizing, searching.
            *   Pull Requests (PRs): Listing, summarizing, searching, getting details/changes.
            *   Code & Files: Searching code, getting file content, listing directory contents.
            *   Repository Stats & Activity: Stars, contributors, recent activity.

            **Code Review Guidelines (Requires repository and PR):**
            *   Fetch Changes: Use `get_pull_request_changes` or `get_pull_request_with_details`.
            *   Analyze Patch: Evaluate based on functionality, best practices, style, clarity, efficiency.
            *   Present Review: Structure clearly, cite lines/code, be constructive.
            """
            ),
            tools=[
                GithubTools(
                    get_repository=True,
                    search_repositories=True,
                    get_pull_request=True,
                    get_pull_request_changes=True,
                    list_branches=True,
                    get_pull_request_count=True,
                    get_pull_requests=True,
                    get_pull_request_comments=True,
                    get_pull_request_with_details=True,
                    list_issues=True,
                    get_issue=True,
                    update_file=True,
                    get_file_content=True,
                    get_directory_content=True,
                    search_code=True,
                ),
            ],
            markdown=True,
            debug_mode=True,
            add_history_to_messages=True,
        )
    return None


async def main():
    """
    Main function to initialize project-specific components and run a specialized agent.
    """
    parser = argparse.ArgumentParser(
        description="Run a specialized AI agent from the agno library examples."
    )
    parser.add_argument(
        "agent_name",
        type=str,
        choices=[
            "calculator",
            "data_analyst",
            "python_agent",
            "investment_agent",
            "github_agent",
        ],
        help="The name of the specialized agent to run.",
    )
    args = parser.parse_args()

    logger.info(f"🚀 Initializing components for user '{USER_ID}'...")

    # 1. Create the Ollama model using your project's AgentModelManager
    model_manager = AgentModelManager(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
    )
    model = model_manager.create_model()
    logger.info(f"✅ Model '{LLM_MODEL}' created successfully.")

    # 2. Create the memory system using your project's storage functions
    agno_memory = create_agno_memory(AGNO_STORAGE_DIR, debug_mode=True)
    logger.info("✅ Memory system created successfully.")

    # 3. Create and load the knowledge base using your project's storage functions
    agno_knowledge = create_combined_knowledge_base(
        storage_dir=AGNO_STORAGE_DIR,
        knowledge_dir=AGNO_KNOWLEDGE_DIR,
        storage=None,  # Not needed for this setup
    )
    if agno_knowledge:
        await load_combined_knowledge_base(agno_knowledge, recreate=False)
        logger.info("✅ Knowledge base loaded successfully.")
    else:
        logger.warning("⚠️ Knowledge base could not be created or loaded.")

    # 4. Get the specialized agent using the function from the example
    logger.info(f"🤖 Creating specialized agent: '{args.agent_name}'...")
    specialized_agent = get_agent(
        agent_name=args.agent_name,
        model=model,
        memory=agno_memory,
        knowledge=agno_knowledge,
    )

    if not specialized_agent:
        logger.error(f"❌ Error: Agent '{args.agent_name}' could not be created.")
        return

    print(f"✅ Specialized agent '{specialized_agent.name}' is ready.")
    print(f"    Role: {specialized_agent.role}")
    print("    Type 'exit' or 'quit' to end the chat.")
    print("-" * 50)

    # 5. Start the interactive chat loop
    while True:
        try:
            query = input(f"[{args.agent_name}]> ")
            if query.lower() in ["exit", "quit"]:
                break

            # Use the specialized agent to process the query
            response = await specialized_agent.arun(query, user_id=USER_ID)

            # The response from arun is an object, we print the content
            print(f"\n🤖 {specialized_agent.name}:\n{response.content}\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"An error occurred during the chat loop: {e}", exc_info=True)
            break

    print("\n👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
