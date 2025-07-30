#!/usr/bin/env python3
"""
Debug script to examine the specific response parsing issue.

The error shows: 'str' object has no attribute 'get'
This happens in agno/models/openai/chat.py line 614: response.error.get("message", "Unknown model error")

This suggests that response.error is a string instead of a dict.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agent_model_manager import AgentModelManager
from personal_agent.config.settings import LLM_MODEL, LMSTUDIO_URL


async def test_raw_openai_response():
    """Test the raw OpenAI response to see what LMStudio is actually returning."""
    print("🔍 Testing raw OpenAI response from LMStudio...")
    print("=" * 60)
    
    try:
        from openai import AsyncOpenAI
        
        # Create direct client
        client = AsyncOpenAI(
            base_url=LMSTUDIO_URL,
            api_key="lm-studio"
        )
        
        print(f"Base URL: {LMSTUDIO_URL}")
        print(f"Model: {LLM_MODEL}")
        
        # Test simple request first
        print("\n1. Testing simple request...")
        try:
            response = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": "Say hello"}],
                max_tokens=50
            )
            
            print(f"✅ Simple request successful")
            print(f"   Response type: {type(response)}")
            print(f"   Response: {response}")
            
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                print(f"   Choice type: {type(choice)}")
                print(f"   Message: {choice.message}")
                print(f"   Content: {choice.message.content}")
            
        except Exception as e:
            print(f"❌ Simple request failed: {e}")
            print(f"   Error type: {type(e)}")
            return
        
        # Test structured output request
        print("\n2. Testing structured output request...")
        try:
            response = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": "Respond with JSON: {\"message\": \"hello\"}"}],
                response_format={"type": "json_object"},
                max_tokens=100
            )
            
            print(f"✅ Structured request successful")
            print(f"   Response type: {type(response)}")
            
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                content = choice.message.content
                print(f"   Content: {content}")
                print(f"   Content type: {type(content)}")
                
                # Try to parse as JSON
                try:
                    parsed = json.loads(content)
                    print(f"   ✅ Content is valid JSON: {parsed}")
                except json.JSONDecodeError as e:
                    print(f"   ❌ Content is not valid JSON: {e}")
            
        except Exception as e:
            print(f"❌ Structured request failed: {e}")
            print(f"   Error type: {type(e)}")
            
            # Check if this is the error we're looking for
            if "'str' object has no attribute 'get'" in str(e):
                print("   🎯 This is the same error we see in Agno!")
                
                # Try to examine the error more closely
                import traceback
                traceback.print_exc()
        
    except ImportError:
        print("❌ OpenAI client not available")
    except Exception as e:
        print(f"❌ Error setting up client: {e}")


async def test_agno_model_internals():
    """Test the Agno model internals to see where the parsing fails."""
    print("\n" + "=" * 60)
    print("🔍 Testing Agno model internals...")
    print("=" * 60)
    
    try:
        # Create the model using AgentModelManager
        model_manager = AgentModelManager(
            model_provider="openai",
            model_name=LLM_MODEL,
            ollama_base_url=LMSTUDIO_URL,
            seed=42,
        )
        
        model = model_manager.create_model()
        print(f"✅ Model created: {type(model).__name__}")
        
        # Check the model's client configuration
        if hasattr(model, 'client'):
            print(f"   Client: {type(model.client)}")
            print(f"   Client base URL: {model.client.base_url}")
        
        # Check request parameters
        if hasattr(model, 'request_params'):
            print(f"   Request params: {model.request_params}")
        
        # Try to make a direct call to the model's client
        print("\n1. Testing model's client directly...")
        try:
            raw_response = await model.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role": "user", "content": "Say hello in JSON format"}],
                **model.request_params  # This includes the response_format
            )
            
            print(f"✅ Direct client call successful")
            print(f"   Response type: {type(raw_response)}")
            
            # Examine the response structure
            print(f"   Response attributes: {dir(raw_response)}")
            
            if hasattr(raw_response, 'choices'):
                print(f"   Choices: {raw_response.choices}")
                if raw_response.choices:
                    choice = raw_response.choices[0]
                    print(f"   First choice: {choice}")
                    print(f"   Message: {choice.message}")
                    print(f"   Content: {choice.message.content}")
            
            # Check for error attribute
            if hasattr(raw_response, 'error'):
                print(f"   Error attribute: {raw_response.error}")
                print(f"   Error type: {type(raw_response.error)}")
            else:
                print("   No error attribute found")
                
        except Exception as e:
            print(f"❌ Direct client call failed: {e}")
            print(f"   Error type: {type(e)}")
            
            # This might be where the issue occurs
            if hasattr(e, 'response'):
                print(f"   Exception response: {e.response}")
            
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error creating model: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🚀 Starting response parsing debug session...")
    
    # Test raw OpenAI client behavior
    await test_raw_openai_response()
    
    # Test Agno model internals
    await test_agno_model_internals()
    
    print("\n" + "=" * 60)
    print("🏁 Debug session complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())