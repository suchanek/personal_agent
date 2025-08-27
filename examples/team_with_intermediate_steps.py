from typing import Iterator

from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.tools.dalle import DalleTools
from agno.utils.common import dataclass_to_dict
from rich.pretty import pprint

image_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[DalleTools()],
    description="You are an AI agent that can create images using DALL-E.",
    instructions=[
        "When the user asks you to create an image, use the DALL-E tool to create an image.",
        "The DALL-E tool will return an image URL.",
        "Return the image URL in your response in the following format: `![image description](image URL)`",
    ],
    markdown=True,
)

run_stream: Iterator[RunResponse] = image_agent.run(
    "Create an image of a yellow siamese cat",
    stream=True,
    stream_intermediate_steps=True,
)
for chunk in run_stream:
    # Convert to dict first, then exclude fields that actually exist
    chunk_dict = dataclass_to_dict(chunk)
    # Only exclude 'messages' if it exists in the dictionary
    if "messages" in chunk_dict:
        chunk_dict.pop("messages")
    pprint(chunk_dict)
    print("---" * 20)
