Agno Tool Agent

"""
A minimal Agno + Ollama tool-only agent with Qwen3-Instruct.

Requires:
  agno>=0.3.* (or your current Agno)
  Ollama running locally with your chosen qwen model pulled.

:param model_name: Ollama model tag, e.g., "qwen3:4b-instruct"
"""

import json
import re
from typing import Dict, Any

from agno.agents import Agent
from agno.models.ollama import Ollama
from agno.tools import tool

# --- 1) Define tools ---------------------------------------------------------

@tool
def get_weather(location: str) -> Dict[str, Any]:
    """
    Return the current weather for a given city (demo stub).
    :param location: City name, e.g., "Cincinnati"
    """
    # Replace with your real implementation
    return {"location": location, "temperature_c": 26.3, "conditions": "Partly cloudy"}

@tool
def web_search(query: str, k: int = 3) -> Dict[str, Any]:
    """
    Demo search tool (stub).
    :param query: Search query
    :param k: Max results
    """
    return {"query": query, "results": [f"Result {i+1} for {query}" for i in range(k)]}

TOOLS = [get_weather, web_search]

# --- 2) Small Qwen model (non-thinking) -------------------------------------

MODEL_NAME = "qwen3:4b-instruct"   # or "qwen3:1.7b-instruct" / "qwen2.5:3b-instruct"

# --- 3) System prompt to enforce tool-only ----------------------------------

SYSTEM_PROMPT = """
You are a tool-calling router. Strict rules:
1) ALWAYS respond by calling one of the provided tools.
2) NEVER output explanations or prose.
3) If you need to answer in prose, call a tool named 'reply' (if provided). If not provided, you must still call one of the available tools.
4) Do not emit any hidden reasoning or <think> blocks.
5) If inputs are ambiguous, call a tool to clarify.
"""

# Optional: add a trivial "reply" tool if you want all text to be channeled via a tool.
# @tool
# def reply(text: str) -> str:
#     return text
# TOOLS.append(reply)

# --- 4) Helper: strip any stray <think>...</think> just in case --------------

THINK_TAG_RE = re.compile(r"<think>.*?</think>", flags=re.DOTALL)

def strip_think_blocks(text: str) -> str:
    """Remove Qwen-style think tags if they appear."""
    return THINK_TAG_RE.sub("", text or "").strip()

# --- 5) Create the agent -----------------------------------------------------

agent = Agent(
    model=Ollama(model=MODEL_NAME, temperature=0.2),
    tools=TOOLS,
    instructions=SYSTEM_PROMPT,
    # If your Agno version supports it, this hint increases reliability:
    # tool_choice="required",   # uncomment if available in your Agno release
)

# --- 6) Run a query (tool-only) ---------------------------------------------

def ask(user_text: str) -> Any:
    """
    Route a user query. If the model returns stray text, we treat it as violation
    and re-issue the instruction (rare with *-instruct models).
    """
    result = agent.run(user_text)

    # Agno typically exposes tool invocations in result.tool_calls (or similar).
    # If your version returns a message object, adapt accordingly.
    tool_calls = getattr(result, "tool_calls", None)

    # Failsafe: if no tool_calls, retry with a stronger reminder
    if not tool_calls:
        reminder = (
            "Reminder: You MUST call a tool. Do not reply with text. "
            "Choose the most relevant tool and call it with arguments."
        )
        result = agent.run(reminder + "\n\nUser: " + user_text)
        tool_calls = getattr(result, "tool_calls", None)

    # UI cleanup: if result contains assistant text, strip any <think>…</think>
    if hasattr(result, "content") and isinstance(result.content, str):
        result.content = strip_think_blocks(result.content)

    return result

if __name__ == "__main__":
    out = ask("What's the temperature in Cincinnati right now?")
    print(out)

