# Ollama-Based Multi-Purpose Reasoning Team

A complete implementation of a multi-agent reasoning team that uses your local Ollama instance and integrates with your personal agent's memory and knowledge infrastructure.

## Overview

This implementation creates a new version of the `reasoning_multi_purpose_team.py` that:

- ✅ **Uses Local Ollama Models**: No external API dependencies or costs
- ✅ **Includes Memory Agent**: Proper integration with your memory and knowledge systems
- ✅ **Follows Your Architecture**: Uses your established patterns and components
- ✅ **Supports Reasoning**: Leverages your optimized Ollama model configurations

## Team Members

### 1. Web Agent
- **Role**: Search the web for information
- **Tools**: DuckDuckGoTools
- **Model**: Your local Ollama instance
- **Capabilities**: Current events, news, general web search

### 2. Finance Agent
- **Role**: Get financial data and market analysis
- **Tools**: YFinanceTools
- **Model**: Your local Ollama instance
- **Capabilities**: Stock prices, company info, analyst recommendations

### 3. Writer Agent
- **Role**: Create content and written materials
- **Tools**: None (pure generation)
- **Model**: Your local Ollama instance
- **Capabilities**: Articles, poems, stories, professional writing

### 4. Calculator Agent
- **Role**: Perform calculations and data analysis
- **Tools**: CalculatorTools, PythonTools
- **Model**: Your local Ollama instance
- **Capabilities**: Math, statistics, code execution, data visualization

### 5. Memory Agent ⭐ (NEW)
- **Role**: Store and retrieve personal information and knowledge
- **Tools**: KnowledgeTools, AgnoMemoryTools
- **Model**: Your local Ollama instance
- **Capabilities**: 
  - Personal memory storage/retrieval
  - Knowledge base management
  - Document ingestion
  - Semantic search across both memory and knowledge

## Key Features

### Memory & Knowledge Integration
The memory agent properly initializes your dual storage system:
- **SQLite Memory**: For personal information about the user
- **LightRAG Graph**: For relationship mapping and semantic search
- **Knowledge Base**: For factual information and documents
- **Automatic Deduplication**: Prevents storing duplicate memories

### Local Ollama Models
All agents use your `AgentModelManager` for consistent configuration:
- Dynamic context sizing based on model capabilities
- Optimized parameters for your `qwen3:8b` model
- Reasoning support for compatible models
- No external API costs or dependencies

### Proper Initialization Sequence
Follows the exact pattern from your `agno_agent.py`:
1. Create Agno storage
2. Create combined knowledge base
3. Load knowledge base content (async)
4. Create memory with SemanticMemoryManager
5. Initialize managers
6. Create tool instances
7. Create Agent

## Files Created

### 1. `examples/teams/ollama_reasoning_multi_purpose_team.py`
The main implementation file with all agents and team coordination.

### 2. `test_ollama_reasoning_team.py`
Comprehensive test script to verify all functionality.

### 3. `ollama_reasoning_team_design.md`
Detailed design document and architecture explanation.

### 4. `README_ollama_reasoning_team.md`
This documentation file.

## Usage

### Basic Usage
```python
import asyncio
from examples.teams.ollama_reasoning_multi_purpose_team import create_team

async def main():
    # Create the team
    team = await create_team()
    
    # Ask questions
    await team.aprint_response("Remember that I love skiing and live in Colorado")
    await team.aprint_response("What do you remember about me?")
    await team.aprint_response("Give me a financial analysis of NVDA")
    await team.aprint_response("Calculate the square root of 144")

if __name__ == "__main__":
    asyncio.run(main())
```

### Running the Example
```bash
# Run the main example
python examples/teams/ollama_reasoning_multi_purpose_team.py

# Run the test suite
python test_ollama_reasoning_team.py
```

## Example Interactions

### Memory Storage and Retrieval
```
User: "Remember that I love skiing and live in Colorado"
Memory Agent: ✅ Successfully stored memory: I love skiing and live in Colorado...

User: "What do you remember about me?"
Memory Agent: 🧠 Based on my stored memories, you love skiing and live in Colorado.
```

### Financial Analysis
```
User: "Give me a financial analysis of NVDA"
Finance Agent: [Retrieves current stock data, analyst recommendations, company news]
```

### Web Search
```
User: "What's the latest news about AI?"
Web Agent: [Searches web and provides current AI news with sources]
```

### Calculations
```
User: "Calculate compound interest on $10,000 at 5% for 10 years"
Calculator Agent: [Performs calculation and shows work]
```

## Testing

The test script (`test_ollama_reasoning_team.py`) includes:

### Functionality Tests
- Team creation and initialization
- Memory storage and retrieval
- Financial data queries
- Mathematical calculations
- Web search capabilities
- Content generation

### Memory Persistence Tests
- Verifies memories persist across team instances
- Tests the dual storage system (SQLite + LightRAG)
- Confirms proper initialization sequence

### Running Tests
```bash
python test_ollama_reasoning_team.py
```

Expected output:
```
🚀 Testing Ollama Multi-Purpose Reasoning Team
📝 Creating team...
✅ Team created successfully!

🧪 Test 1/7: Test team introduction and capabilities
Expected agent: Team coordinator
Query: Hi! What are you capable of doing?
[Team response showing all capabilities]
✅ Test completed successfully
...
```

## Configuration

### Environment Variables
Ensure these are set in your `.env` file:
```bash
LLM_MODEL=qwen3:8b
OLLAMA_URL=http://localhost:11434
USER_ID=your_user_id
LIGHTRAG_URL=http://localhost:9621
LIGHTRAG_MEMORY_URL=http://localhost:9622
```

### Dependencies
The team uses your existing infrastructure:
- Ollama server running locally
- LightRAG servers for knowledge and memory
- Your personal agent's storage and memory systems

## Architecture Benefits

### 1. Fully Local
- No external API costs
- Complete privacy and control
- Works offline (except web search)

### 2. Memory Persistent
- Remembers information across sessions
- Builds relationships over time
- Semantic search capabilities

### 3. Knowledge Aware
- Can ingest documents and URLs
- Maintains factual knowledge base
- Separates personal memory from factual knowledge

### 4. Reasoning Capable
- Uses your optimized model configurations
- Supports complex multi-step reasoning
- Coordinates between specialized agents

### 5. Consistent Architecture
- Follows your established patterns
- Uses your existing components
- Maintains compatibility with your system

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're running from the project root
   - Check that all dependencies are installed

2. **Model Not Found**
   - Verify your Ollama server is running
   - Check that `qwen3:8b` model is available
   - Update `LLM_MODEL` in `.env` if using different model

3. **Memory/Knowledge Errors**
   - Ensure LightRAG servers are running
   - Check storage directory permissions
   - Verify database initialization

4. **Tool Errors**
   - Check internet connection for web search
   - Verify API keys for financial data
   - Ensure Python environment has required packages

### Debug Mode
Enable debug mode for detailed logging:
```python
memory_agent = await create_memory_agent(debug=True)
```

## Comparison with Original

| Feature | Original Team | New Ollama Team |
|---------|---------------|-----------------|
| Models | Claude/OpenAI | Local Ollama |
| Memory | None | Full memory system |
| Knowledge | Limited | Full knowledge base |
| Cost | API costs | Free (local) |
| Privacy | External APIs | Fully local |
| Persistence | None | Full persistence |
| Reasoning | Limited | Enhanced |

## Next Steps

### Potential Enhancements
1. **Add More Agents**: Medical, legal, research specialists
2. **Enhanced Tools**: File operations, code analysis, data visualization
3. **Team Coordination**: Improved reasoning and delegation
4. **Memory Analytics**: Memory statistics and insights
5. **Knowledge Management**: Automated knowledge ingestion

### Integration Options
- Use with your Streamlit dashboard
- Integrate with your CLI interface
- Add to your existing agent workflows
- Extend with additional MCP servers

## Conclusion

This implementation provides a complete, working multi-agent reasoning team that:
- Uses your local Ollama infrastructure
- Integrates with your memory and knowledge systems
- Follows your established architectural patterns
- Provides persistent memory and knowledge capabilities
- Works entirely locally without external API dependencies

The team is ready to use and can be extended with additional agents and capabilities as needed.