import asyncio

from langchain_ollama import ChatOllama
from mcp_use import MCPAgent, MCPClient


async def main():
    # 1. Load MCP client config
    client = MCPClient.from_config_file("mcp_config.json")
    # 2. Connect local LLM
    llm = ChatOllama(model="qwen3:1.7b")
    # 3. Create agent
    agent = MCPAgent(llm=llm, client=client)
    # 4. Run a query
    response = agent.run("Show me all unread Slack messages from this week.")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
