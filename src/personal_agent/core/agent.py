"""Agent initialization and configuration."""

import logging
from typing import List

from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama

from ..config import LLM_MODEL, OLLAMA_URL

logger = logging.getLogger(__name__)


def create_agent_executor(tools: List[BaseTool]) -> AgentExecutor:
    """Create the ReAct agent executor with the provided tools."""

    # Initialize Ollama LLM
    llm = ChatOllama(model=LLM_MODEL, temperature=0.7, base_url=OLLAMA_URL)

    # System prompt for the agent
    system_prompt = """You are a helpful personal assistant with access to various tools for file operations, knowledge management, web search, and GitHub integration.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action as valid JSON (e.g., {{"param1": "value1", "param2": "value2"}})
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

IMPORTANT: Action Input must be valid JSON format. For example:
- Correct: {{"file_path": "~/test.txt", "content": "Hello world"}}
- Incorrect: file_path = '~/test.txt', content = '''Hello world'''

When storing information, always use a relevant topic to categorize it for better retrieval.
When working with files, prefer using absolute paths and be careful about file permissions.
Always store important interactions in memory for future reference. When asked about Github
repositories, use the GitHub tool to search for repositories and provide relevant information.
When asked about the weather, use the weather tool to get current conditions. When asked about
the news, use the news tool to get the latest headlines.

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

    # Create prompt template
    prompt = PromptTemplate.from_template(system_prompt)

    # Create the ReAct agent
    agent = create_react_agent(llm, tools, prompt)

    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10,
        handle_parsing_errors=True,
    )

    logger.info("Created agent executor with %d tools", len(tools))
    return agent_executor
