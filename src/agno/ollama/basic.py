from agno.agent import Agent, RunResponse  # noqa
from agno.models.ollama import Ollama

qwen = "qwen2.5-coder:14b"
llama3 = "llama3.1:8b"
agent = Agent(model=Ollama(id=qwen), markdown=True)

# Get the response in a variable
# run: RunResponse = agent.run("Share a 2 sentence horror story")
# print(run.content)

# Print the response in the terminal
agent.print_response("Write a program to simulate a dice roll", markdown=True)

