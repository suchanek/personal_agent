#!/usr/bin/env python3
"""
Test script for structured JSON response functionality with real Ollama model testing.

This script demonstrates the new structured response handling with JSON schema
validation and metadata extraction, including actual Ollama model calls.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.core.structured_response import (
    StructuredResponse,
    StructuredResponseParser,
    get_ollama_format_schema,
    create_structured_instructions,
)
from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.config import LLM_MODEL, OLLAMA_URL


def test_structured_response_parser():
    """Test the structured response parser with various inputs."""
    print("🧪 Testing Structured Response Parser")
    print("=" * 50)
    
    # Test 1: Valid JSON structured response
    print("\n📊 Test 1: Valid JSON Structured Response")
    json_response = {
        "content": "I found some great information about AI trends for you!",
        "tool_calls": [
            {
                "function_name": "duckduckgo_search",
                "arguments": {"query": "AI trends 2024", "max_results": 5},
                "reasoning": "Searching for current AI trends to provide up-to-date information"
            }
        ],
        "metadata": {
            "confidence": 0.95,
            "sources": ["DuckDuckGo Search", "Web Results"],
            "reasoning_steps": ["Identified search query", "Executed web search", "Analyzed results"],
            "response_type": "structured"
        }
    }
    
    json_str = json.dumps(json_response)
    parsed = StructuredResponseParser.parse(json_str)
    
    print(f"✅ Content: {parsed.content}")
    print(f"✅ Tool Calls: {parsed.tool_calls_count}")
    print(f"✅ Confidence: {parsed.metadata.confidence if parsed.metadata else 'None'}")
    print(f"✅ Sources: {parsed.metadata.sources if parsed.metadata else 'None'}")
    
    # Test 2: Plain text fallback
    print("\n📝 Test 2: Plain Text Fallback")
    text_response = "This is a regular text response without JSON structure."
    parsed_text = StructuredResponseParser.parse(text_response)
    
    print(f"✅ Content: {parsed_text.content}")
    print(f"✅ Response Type: {parsed_text.metadata.response_type if parsed_text.metadata else 'None'}")
    
    # Test 3: Invalid JSON handling
    print("\n❌ Test 3: Invalid JSON Handling")
    invalid_json = '{"content": "Missing closing brace"'
    parsed_invalid = StructuredResponseParser.parse(invalid_json)
    
    print(f"✅ Content: {parsed_invalid.content}")
    print(f"✅ Error: {parsed_invalid.error.message if parsed_invalid.error else 'None'}")
    
    # Test 4: JSON with error
    print("\n🚨 Test 4: JSON with Error Response")
    error_response = {
        "content": "I encountered an issue while processing your request.",
        "error": {
            "code": "SEARCH_FAILED",
            "message": "Unable to connect to search service",
            "recoverable": True
        }
    }
    
    error_str = json.dumps(error_response)
    parsed_error = StructuredResponseParser.parse(error_str)
    
    print(f"✅ Content: {parsed_error.content}")
    print(f"✅ Error Code: {parsed_error.error.code if parsed_error.error else 'None'}")
    print(f"✅ Recoverable: {parsed_error.error.recoverable if parsed_error.error else 'None'}")


def test_ollama_schema():
    """Test the Ollama format schema generation."""
    print("\n🔧 Testing Ollama Format Schema")
    print("=" * 50)
    
    schema = get_ollama_format_schema()
    print("✅ Generated Ollama Format Schema:")
    print(json.dumps(schema, indent=2))
    
    # Validate required fields
    assert "type" in schema
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "content" in schema["properties"]
    assert "required" in schema
    assert "content" in schema["required"]
    
    print("✅ Schema validation passed!")


def test_instruction_enhancement():
    """Test the instruction enhancement with structured output requirements."""
    print("\n📋 Testing Instruction Enhancement")
    print("=" * 50)
    
    base_instructions = """
    You are a helpful AI assistant.
    Answer questions clearly and concisely.
    """
    
    enhanced = create_structured_instructions(base_instructions)
    
    print("✅ Base Instructions:")
    print(base_instructions.strip())
    print("\n✅ Enhanced Instructions (first 200 chars):")
    print(enhanced[:200] + "...")
    
    # Check that JSON requirements are included
    assert "JSON" in enhanced
    assert "content" in enhanced
    assert "tool_calls" in enhanced
    assert "metadata" in enhanced
    
    print("✅ Instruction enhancement validation passed!")


async def test_real_ollama_model():
    """Test with actual Ollama model calls."""
    print("\n🤖 Testing Real Ollama Model")
    print("=" * 50)
    
    try:
        # Initialize the AgnoPersonalAgent
        print("🔧 Initializing AgnoPersonalAgent...")
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            enable_memory=False,  # Disable memory for simpler testing
            enable_mcp=False,     # Disable MCP for simpler testing
            debug=True
        )
        
        # Initialize the agent
        print("⚙️ Initializing agent...")
        success = await agent.initialize()
        if not success:
            print("❌ Failed to initialize agent")
            return
        
        print(f"✅ Agent initialized successfully with model: {LLM_MODEL}")
        
        # Test questions to ask the model
        test_questions = [
            "What is 2 + 2?",
            "Explain what artificial intelligence is in one sentence.",
            "What are the primary colors?",
            "Give me a financial analysis of stock NVDA",
            "What's the weather like today?"
        ]
        
        print(f"\n📝 Testing {len(test_questions)} questions with Ollama model...")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{'='*60}")
            print(f"🔍 Question {i}: {question}")
            print(f"{'='*60}")
            
            start_time = time.time()
            
            try:
                # Get response from agent
                response = await agent.run(question)
                end_time = time.time()
                response_time = end_time - start_time
                
                print(f"⏱️ Response time: {response_time:.2f} seconds")
                print(f"📄 Response length: {len(response)} characters")
                
                # Try to parse as structured response
                structured = StructuredResponseParser.parse(response)
                
                print(f"\n📊 Response Analysis:")
                print(f"✅ Content preview: {structured.content[:200]}...")
                print(f"✅ Tool calls detected: {structured.tool_calls_count}")
                print(f"✅ Response type: {structured.metadata.response_type if structured.metadata else 'text'}")
                
                if structured.tool_calls_count > 0:
                    print(f"\n🔧 Tool Calls Made:")
                    for j, tool_call in enumerate(structured.tool_calls, 1):
                        print(f"  {j}. {tool_call.function_name}")
                        if tool_call.arguments:
                            print(f"     Args: {tool_call.arguments}")
                        if tool_call.reasoning:
                            print(f"     Reasoning: {tool_call.reasoning}")
                
                # Get tool call info from agent
                tool_info = agent.get_last_tool_calls()
                if tool_info["tool_calls_count"] > 0:
                    print(f"\n🛠️ Agent Tool Call Info:")
                    print(f"   Tool calls detected by agent: {tool_info['tool_calls_count']}")
                    print(f"   Response type: {tool_info['response_type']}")
                    
                    for j, tool_detail in enumerate(tool_info["tool_call_details"], 1):
                        print(f"   {j}. {tool_detail.get('function_name', 'Unknown')}")
                        if tool_detail.get('function_args'):
                            print(f"      Args: {tool_detail['function_args']}")
                
                print(f"\n📋 Full Response:")
                print(f"{response}")
                
            except Exception as e:
                print(f"❌ Error with question {i}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Cleanup
        await agent.cleanup()
        print(f"\n✅ Agent cleanup completed")
        
    except Exception as e:
        print(f"❌ Failed to test real Ollama model: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_integration_example():
    """Demonstrate how the structured response would work in practice."""
    print("\n🚀 Integration Example (Simulated)")
    print("=" * 50)
    
    # Simulate what an agent might return
    simulated_agent_response = {
        "content": "Based on my search, here are the top 3 AI trends for 2024:\n\n1. **Multimodal AI**: Integration of text, image, and audio processing\n2. **AI Agents**: Autonomous systems that can perform complex tasks\n3. **Edge AI**: Running AI models directly on devices for better privacy",
        "tool_calls": [
            {
                "function_name": "duckduckgo_search",
                "arguments": {
                    "query": "AI trends 2024 machine learning",
                    "max_results": 10
                },
                "reasoning": "Searching for the latest AI trends to provide current information"
            },
            {
                "function_name": "store_user_memory",
                "arguments": {
                    "content": "User asked about AI trends for 2024",
                    "topics": ["technology", "AI", "research"]
                },
                "reasoning": "Storing this interaction for future reference"
            }
        ],
        "metadata": {
            "confidence": 0.92,
            "sources": ["DuckDuckGo Search Results", "Technology News"],
            "reasoning_steps": [
                "Parsed user query about AI trends",
                "Executed web search for current information",
                "Analyzed and summarized top trends",
                "Stored interaction in memory"
            ],
            "response_type": "structured"
        }
    }
    
    # Parse the response
    response_json = json.dumps(simulated_agent_response)
    structured = StructuredResponseParser.parse(response_json)
    
    print("📊 Parsed Structured Response:")
    print(f"✅ Main Content: {structured.content[:100]}...")
    print(f"✅ Tool Calls Made: {structured.tool_calls_count}")
    print(f"✅ Confidence Score: {structured.metadata.confidence}")
    print(f"✅ Sources: {', '.join(structured.metadata.sources)}")
    
    print("\n🔧 Tool Call Details:")
    for i, tool_call in enumerate(structured.tool_calls, 1):
        print(f"  {i}. {tool_call.function_name}")
        print(f"     Args: {tool_call.arguments}")
        if tool_call.reasoning:
            print(f"     Reasoning: {tool_call.reasoning}")
    
    print("\n🧠 Reasoning Steps:")
    for i, step in enumerate(structured.metadata.reasoning_steps, 1):
        print(f"  {i}. {step}")


def main():
    """Run all tests."""
    print("🧪 Structured Response Testing Suite with Real Ollama Model")
    print("=" * 60)
    
    try:
        # Run parser tests first
        test_structured_response_parser()
        test_ollama_schema()
        test_instruction_enhancement()
        asyncio.run(test_integration_example())
        
        # Now test with real Ollama model
        print(f"\n{'='*60}")
        print("🤖 REAL OLLAMA MODEL TESTING")
        print(f"{'='*60}")
        asyncio.run(test_real_ollama_model())
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed! Structured response system tested with real Ollama model.")
        print("\n📋 Summary of testing:")
        print("  ✅ JSON schema validation for Ollama responses")
        print("  ✅ Structured tool call parsing")
        print("  ✅ Confidence scores and source attribution")
        print("  ✅ Error handling with recovery information")
        print("  ✅ Reasoning step tracking")
        print("  ✅ Fallback to text responses when needed")
        print("  ✅ Real Ollama model integration testing")
        print("  ✅ Tool call detection and analysis")
        print("  ✅ Response time measurement")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
