# Personal Agent Team Architecture

This document describes the new team-based approach for the Personal AI Agent, where specialized agents work together instead of having one monolithic agent.

## 🎯 Overview

The team approach transforms the single large `AgnoPersonalAgent` into a coordinated team of specialized agents, each with a specific role and set of tools. This follows the pattern from `examples/teams/reasoning_multi_purpose_team.py` in the agno framework.

## 🏗️ Architecture

### Team Composition

The Personal Agent Team consists of:

1. **Memory Agent** 🧠 - *Your specialized memory expert*
   - **Role**: Memory recall and storage specialist
   - **Tools**: Semantic memory tools (store_user_memory, query_memory, get_recent_memories, get_all_memories)
   - **Specialization**: Personal information storage and retrieval with deduplication and topic classification
   - **Priority**: Highest - always consulted first for personal information

2. **Web Research Agent** 🌐 - *Your web search specialist*
   - **Role**: Search the web for information and current events
   - **Tools**: DuckDuckGoTools (web search, news search)
   - **Specialization**: Current events, news, web research

3. **Finance Agent** 💰 - *Your financial analysis expert*
   - **Role**: Financial data and market analysis
   - **Tools**: YFinanceTools (stock prices, company info, analyst recommendations)
   - **Specialization**: Stock analysis, financial metrics, market data

4. **Calculator Agent** 🔢 - *Your computation specialist*
   - **Role**: Mathematical calculations and data analysis
   - **Tools**: CalculatorTools, PythonTools
   - **Specialization**: Math problems, calculations, data analysis, programming

5. **File Operations Agent** 📁 - *Your file system expert*
   - **Role**: File system operations and shell commands
   - **Tools**: PersonalAgentFilesystemTools, ShellTools
   - **Specialization**: File operations, directory navigation, system commands

6. **Team Coordinator** 🤝 - *The orchestrator*
   - **Role**: Reasoning and delegation
   - **Tools**: ReasoningTools
   - **Purpose**: Analyzes queries and delegates to appropriate specialized agents

## 🚀 Key Benefits

### 1. **Separation of Concerns**
- Each agent has a clear, focused responsibility
- Easier to debug and maintain individual components
- Cleaner code organization

### 2. **Specialized Expertise**
- Memory Agent focuses solely on semantic memory with advanced features
- Each agent optimized for its specific domain
- Better performance in specialized tasks

### 3. **Scalability**
- Easy to add new specialized agents
- Can modify individual agents without affecting others
- Modular architecture supports growth

### 4. **Transparency**
- Clear visibility into which agent handles what
- Better debugging and monitoring
- User can see which specialists are consulted

### 5. **Memory-First Approach**
- Memory Agent gets highest priority for personal information
- Semantic memory with deduplication and topic classification
- No MCP dependencies - pure semantic memory focus

## 📁 File Structure

```
src/personal_agent/team/
├── __init__.py                    # Module exports
├── specialized_agents.py          # Individual agent definitions
└── personal_agent_team.py         # Team coordinator and wrapper

tools/
└── paga_streamlit_team.py         # Streamlit app for team

examples/
└── personal_agent_team_demo.py    # Demo script

test_personal_agent_team.py        # Comprehensive test suite
```

## 🛠️ Implementation Details

### Specialized Agents (`specialized_agents.py`)

Each agent is created with:
- Specific model configuration
- Focused tool set
- Specialized instructions
- Clear role definition

Example:
```python
def create_memory_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    storage_dir: str = "./data/agno",
    user_id: str = "default_user",
    debug: bool = False,
) -> Agent:
    # Creates memory agent with semantic memory tools
```

### Team Coordinator (`personal_agent_team.py`)

The team uses agno's `Team` class with:
- **Mode**: "coordinate" for reasoning and delegation
- **Tools**: ReasoningTools for analysis
- **Members**: All specialized agents
- **Instructions**: Detailed coordination strategy

### Team Wrapper (`PersonalAgentTeamWrapper`)

Provides compatibility with existing interfaces:
- Similar API to `AgnoPersonalAgent`
- Async initialization and execution
- Tool call tracking and debugging
- Agent information reporting

## 🎮 Usage Examples

### Basic Team Usage

```python
from personal_agent.team.personal_agent_team import PersonalAgentTeamWrapper

# Create team
team = PersonalAgentTeamWrapper(
    model_provider="ollama",
    model_name="llama3.2:3b",
    storage_dir="./data/agno",
    user_id="your_user_id",
    debug=True,
)

# Initialize
await team.initialize()

# Use team
response = await team.run("What do you remember about me?")
print(response)
```

### Streamlit Integration

```bash
# Run team-based Streamlit app
streamlit run tools/paga_streamlit_team.py
```

### Testing

```bash
# Run comprehensive test suite
python test_personal_agent_team.py

# Run interactive demo
python examples/personal_agent_team_demo.py
```

## 🧠 Memory Agent Specialization

The Memory Agent is the star of the team:

### Features
- **Semantic Memory**: Uses SemanticMemoryManager with advanced capabilities
- **Automatic Deduplication**: Prevents storing duplicate memories
- **Topic Classification**: Automatically categorizes memories by topic
- **Comprehensive Search**: Searches through ALL stored memories semantically
- **No MCP Dependencies**: Pure semantic memory focus

### Memory Tools
1. `store_user_memory(content, topics)` - Store new personal information
2. `query_memory(query, limit)` - Search memories semantically
3. `get_recent_memories(limit)` - Get most recent memories
4. `get_all_memories()` - Get all stored memories

### Memory-First Strategy
- **Priority**: Memory Agent always consulted first for personal information
- **Immediate Action**: No hesitation when user asks about personal info
- **Comprehensive**: Searches through all memories, not just recent ones

## 🔄 Migration from Single Agent

### Before (Single Agent)
```python
from personal_agent.core.agno_agent import AgnoPersonalAgent

agent = AgnoPersonalAgent(
    model_name="llama3.2:3b",
    enable_memory=True,
    enable_mcp=False,
)
await agent.initialize()
response = await agent.run("What do you remember about me?")
```

### After (Team Approach)
```python
from personal_agent.team.personal_agent_team import PersonalAgentTeamWrapper

team = PersonalAgentTeamWrapper(
    model_name="llama3.2:3b",
    storage_dir="./data/agno",
    user_id="your_user_id",
)
await team.initialize()
response = await team.run("What do you remember about me?")
```

## 🎯 Coordination Strategy

### Delegation Rules
1. **Personal Information** → Memory Agent (highest priority)
2. **Current Events/News** → Web Research Agent
3. **Financial Data** → Finance Agent
4. **Calculations** → Calculator Agent
5. **File Operations** → File Operations Agent

### Memory-First Approach
- Any question about the user → Memory Agent immediately
- "What do you remember?" → Memory Agent
- Personal preferences/history → Memory Agent
- Store new personal info → Memory Agent

### Reasoning Process
1. **Analyze** the user's query using ReasoningTools
2. **Identify** which specialized agent(s) to consult
3. **Delegate** to appropriate agent(s)
4. **Coordinate** responses from multiple agents if needed
5. **Present** cohesive, friendly response to user

## 🧪 Testing Strategy

### Test Coverage
1. **Individual Agent Tests** - Each agent works correctly
2. **Team Coordination Tests** - Proper delegation and reasoning
3. **Memory Specialization Tests** - Memory agent focus
4. **Integration Tests** - Team wrapper compatibility
5. **Streamlit Tests** - UI integration works

### Test Files
- `test_personal_agent_team.py` - Comprehensive test suite
- `examples/personal_agent_team_demo.py` - Interactive demo

## 🚀 Getting Started

### 1. Install Dependencies
```bash
# Make sure you have agno and dependencies installed
pip install -r requirements.txt
```

### 2. Start Ollama
```bash
# Make sure Ollama is running
ollama serve
```

### 3. Test the Team
```bash
# Run the test suite
python test_personal_agent_team.py

# Or try the interactive demo
python examples/personal_agent_team_demo.py
```

### 4. Use Streamlit App
```bash
# Run the team-based Streamlit app
streamlit run tools/paga_streamlit_team.py
```

## 🔮 Future Enhancements

### Potential New Agents
- **Email Agent**: Handle email operations
- **Calendar Agent**: Manage scheduling and events
- **Document Agent**: Advanced document processing
- **Code Agent**: Specialized programming assistance

### Advanced Features
- **Agent Learning**: Agents learn from user preferences
- **Dynamic Routing**: Smarter delegation based on context
- **Agent Collaboration**: Agents working together on complex tasks
- **Performance Optimization**: Caching and optimization strategies

## 📊 Comparison: Single Agent vs Team

| Aspect | Single Agent | Team Approach |
|--------|-------------|---------------|
| **Complexity** | High (one agent does everything) | Low (specialized agents) |
| **Debugging** | Difficult (everything mixed) | Easy (clear separation) |
| **Maintenance** | Hard (changes affect everything) | Easy (modify individual agents) |
| **Performance** | Good (but unfocused) | Better (specialized optimization) |
| **Scalability** | Limited (monolithic) | High (modular) |
| **Memory Focus** | Mixed with other concerns | Dedicated Memory Agent |
| **Transparency** | Low (black box) | High (clear delegation) |

## 🎉 Conclusion

The team approach provides a cleaner, more maintainable, and more scalable architecture for the Personal AI Agent. The specialized Memory Agent ensures that personal information handling gets the focus it deserves, while other agents handle their respective domains efficiently.

This approach follows the successful pattern from agno's `reasoning_multi_purpose_team.py` and provides a solid foundation for future enhancements and new capabilities.
