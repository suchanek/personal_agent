# Personal Log

**2025-08-08**

- v0.11.38dev branch working on personalagent team, tool calling agent

**2025-08-07**

- branch monTeam/v0.11.37 - the agno_agent.py web interface is working well with good debugging on tool calls. I will work to incorporate into the streamlit_agno apps. Need to unify this into a single framework!

**2025-08-06**

- fixed tool listing and agno_web.py. the response handling is now good enough to use within the main agent
- @todo - correct the mcp server handling to use agno's mcptools()

**2.25-08-06**

- branch team/v0.11.37 working on the agno_agent web interface. fixed the init of the knowledgemanager, was not passing the KB

**2025-08-03**

- Created new branch `v0.11.37` from the latest `team/v0.11.37` branch. This version is generally functional and includes a significant refactoring of `user_sync.py` for improved robustness.

**2025-08-02**

- Need to create a simple memory agent with only memory tools. The `reasoning_team` initialization of the `AgnoMemoryAgent` seems to include all tools, which is not what is desired for this specific use case.

**2025-08-01**

- The `Qwen3:8B` model appears to be the top-performing model for the enhanced Ollama Reasoning Team, providing a good balance of speed and reasoning capability.

**2025-07-31**

- The Qwen reasoning models will call tools correctly. it's hard to stop their reasoning though. 
- Llama models have proven generally useless for tool calling
