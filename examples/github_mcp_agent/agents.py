import os
from textwrap import dedent

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.mcp import MCPTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Import configuration settings
try:
    from personal_agent.config.settings import LLM_MODEL, OLLAMA_URL
except ImportError:
    # Fallback defaults if settings not available
    LLM_MODEL = "llama3.2:3b"
    OLLAMA_URL = "http://localhost:11434"


async def run_github_agent(message, model_name=None, ollama_url=None):
    if not os.getenv("GITHUB_TOKEN"):
        return "Error: GitHub token not provided"

    try:
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
        )

        # Create client session
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize MCP toolkit
                mcp_tools = MCPTools(session=session)
                await mcp_tools.initialize()

                # Use provided parameters or fall back to defaults
                model_id = model_name or LLM_MODEL
                host_url = ollama_url or OLLAMA_URL

                # Create Ollama model
                model = Ollama(
                    id=model_id,
                    host=host_url,  # Use host parameter for Ollama
                    options={
                        "temperature": 0.7,
                        "num_predict": -1,  # Allow unlimited prediction length
                        "top_k": 40,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1,
                        "num_ctx": 16384,  # Context window
                    },
                )

                # Create agent with Ollama model
                agent = Agent(
                    model=model,
                    tools=[mcp_tools],
                    instructions=dedent(
                        """\
                        You are a GitHub assistant. Help users explore repositories and their activity.
                        - Provide organized, concise insights about the repository
                        - Focus on facts and data from the GitHub API
                        - Use markdown formatting for better readability
                        - Present numerical data in tables when appropriate
                        - Include links to relevant GitHub pages when helpful
                    """
                    ),
                    markdown=True,
                    show_tool_calls=True,
                )

                # Run agent with longer timeout (120 seconds like other operations in the codebase)
                import asyncio

                response = await asyncio.wait_for(agent.arun(message), timeout=120)
                return response.content
    except asyncio.TimeoutError:
        return "Error: GitHub agent execution timed out after 2 minutes"
    except Exception as e:
        return f"Error: {str(e)}"
