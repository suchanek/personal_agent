import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agno.agent import Agent
from personal_agent.core.agent_model_manager import AgentModelManager


async def main():
    # Create the model using the project's model manager
    model_manager = AgentModelManager(
        model_provider="ollama",
        model_name="gpt-oss:20b",
        ollama_base_url="http://localhost:11434",
        seed=None
    )
    
    model = model_manager.create_model()
    
    # Create a simple agent with the model
    agent = Agent(
        name="gpt-oss-debug-agent",
        model=model,
        tools=[],  # No tools for simple test
        instructions=[
            "You are a helpful AI assistant.",
            "Provide clear and informative responses.",
            "Focus on being accurate and educational."
        ],
        markdown=True,
        show_tool_calls=False,  # Disable tool call display for cleaner output
    )

    # Your test prompt
    prompt = "Explain the differences between supervised and unsupervised learning."

    print(f"🤖 Running query: {prompt}")
    print("=" * 60)

    # Run the query and collect the response
    response_content = ""
    for chunk in agent.run(prompt, stream=True):
        if hasattr(chunk, 'content') and chunk.content:
            response_content += chunk.content
            print(chunk.content, end='', flush=True)

    print("\n" + "=" * 60)
    print("✅ Query completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
