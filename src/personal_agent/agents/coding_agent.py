"""Run `pip install ollama sqlalchemy 'fastapi[standard]'` to install dependencies."""

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.playground import Playground
from agno.storage.sqlite import SqliteStorage

from agno.tools.python import PythonTools
from personal_agent.config.settings import DATA_DIR, LLM_MODEL, ROOT_DIR

local_agent_storage_file: str = f"{DATA_DIR}/local_agents.db"
common_instructions = [
    "If the user asks about you or your skills, tell them your name and role.",
    "You are a coding agent specialized in writing and debugging code.",
    "You can write code in Python, JavaScript, and other languages.",
    "You can also help with debugging and code reviews.",
    "If the user asks for help with a coding problem, ask them to provide the code they are working on.",
    "If the user asks for help with a specific coding problem, ask them to provide the details of the problem.",
    "If the user asks for help with a coding problem, ask them to provide the code they are working on.",
    "Use proper docstring and comments in your code.",
    "Use :param: style for function parameters in docstrings.",
]

coding_agent = Agent(
    name="Coding Agent",
    agent_id="coding_agent",
    model=Ollama(id=LLM_MODEL),
    reasoning=True,
    markdown=True,
    add_history_to_messages=True,
    description="You are a coding agent",
    instructions=common_instructions,
    add_datetime_to_instructions=True,
    tools=[
        PythonTools(
            read_files=True,
            base_dir=ROOT_DIR,
            run_code=True,
            list_files=True,
            uv_pip_install=False,
        )
    ],
    storage=SqliteStorage(
        table_name="coding_agent",
        db_file=local_agent_storage_file,
        auto_upgrade_schema=True,
    ),
)

playground = Playground(
    agents=[coding_agent],
    name="Coding Agent",
    description="A playground for coding agent",
    app_id="coding-agent",
)
app = playground.get_app()

if __name__ == "__main__":
    playground.serve(app="coding_agent:app", reload=True)
