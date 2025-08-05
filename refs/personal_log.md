# Personal Log

**2025-08-03**

- Created new branch `v0.11.37` from the latest `team/v0.11.37` branch. This version is generally functional and includes a significant refactoring of `user_sync.py` for improved robustness.

**2025-08-02**

- Need to create a simple memory agent with only memory tools. The `reasoning_team` initialization of the `AgnoMemoryAgent` seems to include all tools, which is not what is desired for this specific use case.

**2025-08-01**

- The `Qwen3:8B` model appears to be the top-performing model for the enhanced Ollama Reasoning Team, providing a good balance of speed and reasoning capability.

**2025-07-31**

- The Qwen reasoning models will call tools correctly. it's hard to stop their reasoning though. 
- Llama models have proven generally useless for tool calling