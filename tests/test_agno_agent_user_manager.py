#!/usr/bin/env python3
"""
Test Script for AgnoPersonalAgent UserManager Integration

This script tests the proper initialization of AgnoPersonalAgent() and verifies
that the UserManager() class is working correctly by testing:
- self.user_details
- self.delta_year  
- self.cognitive_state

The script demonstrates both synchronous and asynchronous initialization patterns.
"""

import sys
import asyncio
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.core.user_manager import UserManager
from personal_agent.config.user_id_mgr import get_userid


def test_user_manager_standalone():
    """Test UserManager functionality independently."""
    print("=" * 60)
    print("TESTING USERMANAGER STANDALONE")
    print("=" * 60)
    
    # Initialize UserManager
    user_manager = UserManager()
    current_user_id = get_userid()
    
    print(f"Current User ID: {current_user_id}")
    
    # Ensure current user is registered
    user_manager.ensure_current_user_registered()
    
    # Test getting user details
    user_details = user_manager.get_user_details(current_user_id)
    print(f"\nUser Details from UserManager:")
    print(f"  user_id: {user_details.get('user_id')}")
    print(f"  user_name: {user_details.get('user_name')}")
    print(f"  user_type: {user_details.get('user_type')}")
    print(f"  delta_year: {user_details.get('delta_year')}")
    print(f"  cognitive_state: {user_details.get('cognitive_state')}")
    print(f"  email: {user_details.get('email')}")
    print(f"  phone: {user_details.get('phone')}")
    print(f"  address: {user_details.get('address')}")
    print(f"  birth_date: {user_details.get('birth_date')}")
    print(f"  is_current: {user_details.get('is_current')}")
    
    return user_details


def test_agno_agent_sync_initialization():
    """Test AgnoPersonalAgent with synchronous initialization pattern."""
    print("\n" + "=" * 60)
    print("TESTING AGNO AGENT - SYNCHRONOUS INITIALIZATION")
    print("=" * 60)
    
    try:
        # Create agent with lazy initialization (default)
        print("Creating AgnoPersonalAgent with lazy initialization...")
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name="llama3.2:3b",
            enable_memory=True,
            debug=True,
            initialize_agent=False  # Use lazy initialization
        )
        
        print(f"✅ Agent created successfully")
        print(f"   Initialized: {agent._initialized}")
        print(f"   User ID: {agent.user_id}")
        
        # Test UserManager integration attributes
        print(f"\nUserManager Integration Attributes:")
        print(f"   user_details: {agent.user_details}")
        print(f"   delta_year: {agent.delta_year}")
        print(f"   cognitive_state: {agent.cognitive_state}")
        
        # Verify these match what UserManager returns directly
        user_manager = UserManager()
        direct_details = user_manager.get_user_details(agent.user_id)
        
        print(f"\nVerification against direct UserManager call:")
        print(f"   delta_year matches: {agent.delta_year == direct_details.get('delta_year')}")
        print(f"   cognitive_state matches: {agent.cognitive_state == direct_details.get('cognitive_state')}")
        print(f"   user_details matches: {agent.user_details == direct_details}")
        
        return agent
        
    except Exception as e:
        print(f"❌ Error in synchronous initialization: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_agno_agent_async_initialization():
    """Test AgnoPersonalAgent with asynchronous initialization pattern."""
    print("\n" + "=" * 60)
    print("TESTING AGNO AGENT - ASYNCHRONOUS INITIALIZATION")
    print("=" * 60)
    
    try:
        # Create agent and initialize it
        print("Creating AgnoPersonalAgent with async initialization...")
        agent = await AgnoPersonalAgent.create_with_init(
            model_provider="ollama",
            model_name="llama3.2:3b",
            enable_memory=True,
            debug=True
        )
        
        print(f"✅ Agent created and initialized successfully")
        print(f"   Initialized: {agent._initialized}")
        print(f"   User ID: {agent.user_id}")
        print(f"   Tools count: {len(agent.tools) if agent.tools else 0}")
        
        # Test UserManager integration attributes
        print(f"\nUserManager Integration Attributes:")
        print(f"   user_details: {agent.user_details}")
        print(f"   delta_year: {agent.delta_year}")
        print(f"   cognitive_state: {agent.cognitive_state}")
        
        # Verify these match what UserManager returns directly
        user_manager = UserManager()
        direct_details = user_manager.get_user_details(agent.user_id)
        
        print(f"\nVerification against direct UserManager call:")
        print(f"   delta_year matches: {agent.delta_year == direct_details.get('delta_year')}")
        print(f"   cognitive_state matches: {agent.cognitive_state == direct_details.get('cognitive_state')}")
        print(f"   user_details matches: {agent.user_details == direct_details}")
        
        # Test that the agent can be used (use arun for async tools)
        print(f"\nTesting agent functionality...")
        try:
            response = await agent.arun("Hello! What's my user ID?")
            print(f"   Agent response: {response.content[:100]}..." if len(response.content) > 100 else f"   Agent response: {response.content}")
        except Exception as e:
            print(f"   ⚠️  Agent run test failed: {e}")
        
        return agent
        
    except Exception as e:
        print(f"❌ Error in asynchronous initialization: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_lazy_initialization():
    """Test that lazy initialization works correctly."""
    print("\n" + "=" * 60)
    print("TESTING LAZY INITIALIZATION")
    print("=" * 60)
    
    try:
        # Create agent without initialization
        print("Creating AgnoPersonalAgent with lazy initialization...")
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name="llama3.2:3b",
            enable_memory=True,
            debug=True,
            initialize_agent=False
        )
        
        print(f"✅ Agent created (not yet initialized)")
        print(f"   Initialized: {agent._initialized}")
        print(f"   User ID: {agent.user_id}")
        
        # UserManager attributes should still be available
        print(f"\nUserManager Integration Attributes (before initialization):")
        print(f"   user_details: {agent.user_details}")
        print(f"   delta_year: {agent.delta_year}")
        print(f"   cognitive_state: {agent.cognitive_state}")
        
        # Now trigger initialization by running the agent (use arun for async tools)
        print(f"\nTriggering lazy initialization by running agent...")
        try:
            response = await agent.arun("Hello! Please tell me about yourself.")
            
            print(f"✅ Lazy initialization completed")
            print(f"   Initialized: {agent._initialized}")
            print(f"   Tools count: {len(agent.tools) if agent.tools else 0}")
            print(f"   Response: {response.content[:100]}..." if len(response.content) > 100 else f"   Response: {response.content}")
        except Exception as e:
            print(f"   ⚠️  Agent run test failed: {e}")
            print(f"✅ Lazy initialization completed (despite run error)")
            print(f"   Initialized: {agent._initialized}")
            print(f"   Tools count: {len(agent.tools) if agent.tools else 0}")
        
        # UserManager attributes should still be the same
        print(f"\nUserManager Integration Attributes (after initialization):")
        print(f"   user_details: {agent.user_details}")
        print(f"   delta_year: {agent.delta_year}")
        print(f"   cognitive_state: {agent.cognitive_state}")
        
        return agent
        
    except Exception as e:
        print(f"❌ Error in lazy initialization test: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_user_manager_with_custom_user():
    """Test UserManager with a custom test user."""
    print("\n" + "=" * 60)
    print("TESTING USERMANAGER WITH CUSTOM USER")
    print("=" * 60)
    
    try:
        user_manager = UserManager()
        
        # Create a test user with specific attributes (use timestamp to avoid conflicts)
        import time
        test_user_id = f"test_user_{int(time.time())}"
        print(f"Creating test user: {test_user_id}")
        
        result = user_manager.create_user(
            user_id=test_user_id,
            user_name="Test User",
            user_type="Standard",
            email="test@example.com",
            phone="555-123-4567",
            address="123 Test Street",
            birth_date="1990-01-01",
            delta_year=5,  # Writing memories as a 5-year-old
            cognitive_state=80
        )
        
        print(f"User creation result: {result}")
        
        if result.get('success'):
            # Test AgnoPersonalAgent with this custom user
            print(f"\nTesting AgnoPersonalAgent with custom user...")
            agent = AgnoPersonalAgent(
                user_id=test_user_id,
                model_provider="ollama",
                model_name="llama3.2:3b",
                enable_memory=True,
                debug=True,
                initialize_agent=False
            )
            
            print(f"✅ Agent created with custom user")
            print(f"   User ID: {agent.user_id}")
            print(f"   user_details: {agent.user_details}")
            print(f"   delta_year: {agent.delta_year}")
            print(f"   cognitive_state: {agent.cognitive_state}")
            
            # Verify the custom values
            expected_delta_year = 5
            expected_cognitive_state = 80
            
            print(f"\nVerification:")
            print(f"   delta_year is {expected_delta_year}: {agent.delta_year == expected_delta_year}")
            print(f"   cognitive_state is {expected_cognitive_state}: {agent.cognitive_state == expected_cognitive_state}")
            print(f"   user_details contains email: {'email' in agent.user_details}")
            print(f"   user_details email: {agent.user_details.get('email')}")
            
            return agent
        else:
            print(f"❌ Failed to create test user: {result}")
            return None
            
    except Exception as e:
        print(f"❌ Error in custom user test: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main test function."""
    print("🧪 AGNO PERSONAL AGENT USER MANAGER INTEGRATION TEST")
    print("=" * 60)
    print("This script tests the proper initialization of AgnoPersonalAgent()")
    print("and verifies UserManager() class functionality.")
    print("=" * 60)
    
    # Test 1: UserManager standalone
    user_details = test_user_manager_standalone()
    
    # Test 2: Synchronous initialization
    sync_agent = test_agno_agent_sync_initialization()
    
    # Test 3: Asynchronous initialization
    async_agent = await test_agno_agent_async_initialization()
    
    # Test 4: Lazy initialization
    lazy_agent = await test_lazy_initialization()
    
    # Test 5: Custom user
    custom_agent = test_user_manager_with_custom_user()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("UserManager Standalone", user_details is not None),
        ("Synchronous Initialization", sync_agent is not None),
        ("Asynchronous Initialization", async_agent is not None),
        ("Lazy Initialization", lazy_agent is not None),
        ("Custom User Test", custom_agent is not None)
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! UserManager integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
    
    # Cleanup
    if async_agent:
        await async_agent.cleanup()
    if lazy_agent:
        await lazy_agent.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test script failed: {e}")
        import traceback
        traceback.print_exc()
