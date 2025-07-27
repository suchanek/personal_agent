#!/usr/bin/env python3
"""Test the fixed AgentModelManager with regular Ollama instead of OllamaTools"""

from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from src.personal_agent.core.agent_model_manager import AgentModelManager
from src.personal_agent.config.settings import OLLAMA_URL

def test_fixed_qwen3_tool_calling():
    """Test Qwen3 with the fixed AgentModelManager using regular Ollama."""
    
    print("=== Testing Fixed AgentModelManager with Qwen3 ===\n")
    
    # Create model using the fixed AgentModelManager
    model_manager = AgentModelManager(
        model_provider="ollama",
        model_name="qwen3:8b",
        ollama_base_url=OLLAMA_URL,
        seed=42
    )
    
    model = model_manager.create_model()
    print(f"✓ Created model: {type(model).__name__}")
    print(f"✓ Model ID: {model.id}")
    print(f"✓ Model host: {model.host}")
    
    # Create agent with the fixed model
    agent = Agent(
        name="Fixed Qwen3 Agent",
        model=model,
        tools=[DuckDuckGoTools()],
        show_tool_calls=True
    )
    
    print(f"✓ Created agent with {len(agent.tools)} tools")
    
    # Test tool calling
    print("\n" + "="*50)
    print("Testing tool calling with fixed setup...")
    print("="*50)
    
    try:
        response = agent.run("Search for 'Python programming tutorials'", stream=False)
        
        # Check if we got actual search results (not just reasoning)
        content = response.content.lower()
        has_search_results = any(keyword in content for keyword in [
            'python.org', 'tutorial', 'programming', 'learn', 'guide', 'documentation'
        ])
        
        print(f"Response length: {len(response.content)} characters")
        print(f"Contains search results: {has_search_results}")
        
        if has_search_results:
            print("✅ SUCCESS: Tool calling is working! Agent executed search and returned results.")
            print(f"First 300 chars: {response.content[:300]}...")
        else:
            print("❌ ISSUE: Agent may not have executed tools properly.")
            print(f"Response: {response.content[:500]}...")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixed_qwen3_tool_calling()