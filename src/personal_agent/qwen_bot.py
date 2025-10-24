from qwen_agent.agents import Assistant

# Define LLM
llm_cfg = {
    "model": "qwen3:8b",  # Corrected model name format for Ollama
    "model_type": "oai",  # Use OpenAI-compatible API type (correct value for qwen_agent)
    "model_server": "http://localhost:11434/v1",  # Ollama OpenAI-compatible endpoint
    "api_key": "ollama",  # Ollama doesn't require a real API key, but some value is needed
    # Other parameters:
    # 'generate_cfg': {
    #         # Add: When the response content is `<think>this is the thought</think>this is the answer;
    #         # Do not add: When the response has been separated by reasoning_content and content.
    #         'thought_in_content': True,
    #     },
}

# Define Tools
tools = [
    {
        "mcpServers": {  # You can specify the MCP configuration file
            "time": {
                "command": "uvx",
                "args": ["mcp-server-time", "--local-timezone=Asia/Shanghai"],
            },
            "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]},
        }
    },
    "code_interpreter",  # Built-in tools
]

# Define Agent
bot = Assistant(llm=llm_cfg, function_list=tools)

# Streaming generation
messages = [
    {
        "role": "user",
        "content": "https://qwenlm.github.io/blog/ Introduce the latest developments of Qwen",
    }
]
for responses in bot.run(messages=messages):
    pass
print(responses)
