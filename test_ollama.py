# test_ollama_tool_loop.py
import json

import ollama


# ---- Define your tools ----
def add_two_numbers(a: int, b: int) -> int:
    return a + b


TOOLS = {
    "add_two_numbers": add_two_numbers,
}

# Optional: a schema-like descriptor for the model (helps some templates)
tool_specs = [
    {
        "type": "function",
        "function": {
            "name": "add_two_numbers",
            "description": "Add two integers and return the sum.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "integer"},
                    "b": {"type": "integer"},
                },
                "required": ["a", "b"],
            },
        },
    }
]

# ---- 1) Initial user question with tools enabled (NO format='json') ----
messages = [{"role": "user", "content": "What is 10 + 32? Use the tool if needed."}]

resp = ollama.chat(
    model="llama3.1:8b",
    messages=messages,
    tools=tool_specs,  # important: pass tools here
)

msg = resp["message"] if isinstance(resp, dict) else resp.message

# ---- 2) If the model asked to call a tool, execute it ----
tool_calls = msg.get("tool_calls", []) or getattr(msg, "tool_calls", [])
if tool_calls:
    results_to_feed = []
    for tc in tool_calls:
        fn = tc.get("function", {})
        name = fn.get("name")
        args = fn.get("arguments", {}) or {}

        if name not in TOOLS:
            raise RuntimeError(f"Unknown tool requested: {name}")

        result = TOOLS[name](**args)  # execute the Python function

        # ---- 3) Feed tool result back as a 'tool' role message ----
        # Ollama associates by function name; include JSON payload.
        results_to_feed.append(
            {
                "role": "tool",
                "name": name,
                "content": json.dumps({"result": result}),
            }
        )

    # Extend conversation with assistant’s tool-call turn and the tool results
    messages.append({"role": "assistant", "content": msg.get("content", "")})
    messages.extend(results_to_feed)

    # ---- 4) Ask the model to produce the final answer ----
    final = ollama.chat(
        model="llama3.1:8b",
        messages=messages,
        tools=tool_specs,  # keep tools in case follow-up is needed
    )

    final_msg = final["message"] if isinstance(final, dict) else final.message
    print("FINAL:", final_msg.get("content", ""))

else:
    # No tool needed; just print the model's answer
    print("FINAL (no tools):", msg.get("content", ""))
