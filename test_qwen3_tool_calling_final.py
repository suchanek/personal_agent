#!/usr/bin/env python3
"""
Final diagnostic to test Qwen3 tool calling and confirm the issue
"""

from agno.agent import Agent
from agno.models.message import Message
from agno.models.ollama import OllamaTools
from agno.tools.duckduckgo import DuckDuckGoTools


def test_qwen3_vs_llama():
    """Compare Qwen3 vs Llama3.2 tool calling"""

    print("=== Qwen3 vs Llama3.2 Tool Calling Test ===\n")

    # Test with Qwen3
    print("1. Testing Qwen3:8b")
    qwen_model = OllamaTools(id="qwen3:8b")
    qwen_agent = Agent(
        name="Qwen Test Agent",
        model=qwen_model,
        tools=[DuckDuckGoTools()],
        show_tool_calls=True,
    )

    try:
        response = qwen_agent.run("Search for 'Python tutorials'", stream=False)
        print(f"Qwen3 Response: {response.content[:200]}...")
        print(
            f"Tool calls made: {len(response.tool_calls) if response.tool_calls else 0}"
        )
    except Exception as e:
        print(f"Qwen3 Error: {e}")

    print("\n" + "=" * 50 + "\n")

    # Test with Llama3.2 (if available)
    print("2. Testing Llama3.2:8b")
    try:
        llama_model = OllamaTools(id="llama3.2:3b")
        llama_agent = Agent(
            name="Llama Test Agent",
            model=llama_model,
            tools=[DuckDuckGoTools()],
            show_tool_calls=True,
        )

        response = llama_agent.run("Search for 'Python tutorials'", stream=False)
        print(f"Llama3.2 Response: {response.content[:200]}...")
        print(
            f"Tool calls made: {len(response.tool_calls) if response.tool_calls else 0}"
        )
    except Exception as e:
        print(f"Llama3.2 Error (model may not be available): {e}")


if __name__ == "__main__":
    test_qwen3_vs_llama()
