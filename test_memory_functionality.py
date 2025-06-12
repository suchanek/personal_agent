#!/usr/bin/env python3
"""
Test script to verify agentic memory functionality with the Personal AI Agent.
This script tests memory creation, retention, and intelligent recall through multiple interactions.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List

from rich import print

from src.personal_agent.config import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    DATA_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    USER_ID,
)
from src.personal_agent.core.agno_agent import AgnoPersonalAgent


class MemoryTestSuite:
    """Test suite for verifying agentic memory functionality."""

    def __init__(self, user_id: str = None):
        self.user_id = user_id or USER_ID
        self.agent = None
        self.test_results = []
        self.interactions_log = []

    async def initialize_agent(self) -> bool:
        """Initialize the agent with agentic memory enabled."""
        print("🧪 Initializing AgnoPersonalAgent for Memory Testing")
        print("=" * 60)

        self.agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            enable_memory=True,
            enable_mcp=False,  # Disable MCP for focused memory testing
            storage_dir=AGNO_STORAGE_DIR,
            knowledge_dir=AGNO_KNOWLEDGE_DIR,
            debug=True,
            ollama_base_url=OLLAMA_URL,
            user_id=self.user_id,
        )

        print(f"🚀 Initializing agent with user_id: {self.user_id}")
        success = await self.agent.initialize()

        if not success:
            print("❌ Failed to initialize agent")
            return False

        print("✅ Agent initialized successfully!")

        # Verify agent configuration
        agent_info = self.agent.get_agent_info()
        print(f"📊 Agent Configuration:")
        for key, value in agent_info.items():
            print(f"  - {key}: {value}")

        return True

    async def run_interaction(self, message: str, test_name: str) -> Dict[str, Any]:
        """Run a single interaction with the agent and log results."""
        print(f"\n💬 {test_name}")
        print(f"👤 User: {message}")

        thoughts = []

        def thought_callback(thought: str):
            thoughts.append(thought)
            print(f"💭 {thought}")

        try:
            start_time = datetime.now()
            response = await self.agent.run(
                message, add_thought_callback=thought_callback
            )
            end_time = datetime.now()

            print(f"🤖 Agent: {response}")

            interaction_log = {
                "test_name": test_name,
                "timestamp": start_time.isoformat(),
                "user_message": message,
                "agent_response": response,
                "thoughts": thoughts,
                "duration_ms": (end_time - start_time).total_seconds() * 1000,
                "success": True,
            }

            self.interactions_log.append(interaction_log)
            return interaction_log

        except Exception as e:
            print(f"❌ Error during interaction: {e}")
            interaction_log = {
                "test_name": test_name,
                "timestamp": datetime.now().isoformat(),
                "user_message": message,
                "agent_response": None,
                "thoughts": thoughts,
                "error": str(e),
                "success": False,
            }
            self.interactions_log.append(interaction_log)
            return interaction_log

    async def test_basic_memory_creation(self) -> bool:
        """Test basic memory creation with personal information."""
        print("\n🧠 TEST 1: Basic Memory Creation")
        print("-" * 40)

        interactions = [
            (
                f"Hi! My name is {self.user_id} and I'm testing this AI agent.",
                "Initial Introduction",
            ),
            (
                "I work as a software engineer and love programming in Python.",
                "Professional Info",
            ),
            (
                "My favorite color is blue and I enjoy hiking on weekends.",
                "Personal Preferences",
            ),
            ("I have a cat named Whiskers who is 3 years old.", "Pet Information"),
            (
                "I live in San Francisco and have been there for 5 years.",
                "Location Info",
            ),
        ]

        success = True
        for message, test_name in interactions:
            result = await self.run_interaction(message, test_name)
            if not result["success"]:
                success = False

        self.test_results.append({"test": "basic_memory_creation", "success": success})
        return success

    async def test_memory_recall(self) -> bool:
        """Test that the agent can recall previously stored information."""
        print("\n🔍 TEST 2: Memory Recall")
        print("-" * 40)

        recall_questions = [
            ("What's my name?", "Name Recall"),
            ("What do I do for work?", "Job Recall"),
            ("What's my favorite color?", "Preference Recall"),
            ("Tell me about my pet.", "Pet Recall"),
            ("Where do I live and for how long?", "Location Recall"),
        ]

        success = True
        for question, test_name in recall_questions:
            result = await self.run_interaction(question, test_name)
            if not result["success"]:
                success = False

        self.test_results.append({"test": "memory_recall", "success": success})
        return success

    async def test_memory_integration(self) -> bool:
        """Test that the agent can integrate and connect different memories."""
        print("\n🔗 TEST 3: Memory Integration")
        print("-" * 40)

        integration_prompts = [
            (
                "Based on what you know about me, what kind of activities might I enjoy?",
                "Activity Suggestions",
            ),
            (
                "Given my profession and location, what might be some challenges I face?",
                "Problem Analysis",
            ),
            (
                "Create a brief profile summary of me based on our conversations.",
                "Profile Summary",
            ),
            (
                "What questions would you ask to learn more about my interests?",
                "Curiosity Test",
            ),
        ]

        success = True
        for prompt, test_name in integration_prompts:
            result = await self.run_interaction(prompt, test_name)
            if not result["success"]:
                success = False

        self.test_results.append({"test": "memory_integration", "success": success})
        return success

    async def test_memory_updates(self) -> bool:
        """Test that the agent can update existing memories with new information."""
        print("\n🔄 TEST 4: Memory Updates")
        print("-" * 40)

        update_interactions = [
            (
                "Actually, I just got a promotion! I'm now a senior software engineer.",
                "Job Update",
            ),
            (
                "I moved to a new apartment in the Mission district of San Francisco.",
                "Location Update",
            ),
            ("Whiskers just had her 4th birthday last week!", "Pet Age Update"),
            ("I've started learning JavaScript in addition to Python.", "Skill Update"),
        ]

        success = True
        for message, test_name in update_interactions:
            result = await self.run_interaction(message, test_name)
            if not result["success"]:
                success = False

        # Test recall of updated information
        recall_tests = [
            ("What's my current job title?", "Updated Job Recall"),
            ("Where exactly do I live now?", "Updated Location Recall"),
            ("How old is Whiskers now?", "Updated Pet Age Recall"),
            ("What programming languages do I know?", "Updated Skills Recall"),
        ]

        for question, test_name in recall_tests:
            result = await self.run_interaction(question, test_name)
            if not result["success"]:
                success = False

        self.test_results.append({"test": "memory_updates", "success": success})
        return success

    async def test_duplicate_prevention(self) -> bool:
        """Test that the agent handles duplicate/similar information intelligently."""
        print("\n🚫 TEST 5: Duplicate Prevention")
        print("-" * 40)

        # Provide similar information multiple times
        duplicate_interactions = [
            ("I really love Python programming.", "Duplicate Interest 1"),
            ("Python is my favorite programming language.", "Duplicate Interest 2"),
            ("I'm passionate about coding in Python.", "Duplicate Interest 3"),
            ("My cat Whiskers is very playful.", "Duplicate Pet Info 1"),
            ("Whiskers loves to play and is quite energetic.", "Duplicate Pet Info 2"),
        ]

        success = True
        for message, test_name in duplicate_interactions:
            result = await self.run_interaction(message, test_name)
            if not result["success"]:
                success = False

        # Test how the agent handles the duplicates
        result = await self.run_interaction(
            "Can you tell me about my interests and my cat, being mindful not to repeat information?",
            "Duplicate Handling Test",
        )

        if not result["success"]:
            success = False

        self.test_results.append({"test": "duplicate_prevention", "success": success})
        return success

    async def test_contextual_memory(self) -> bool:
        """Test that the agent uses memory contextually in conversations."""
        print("\n🎯 TEST 6: Contextual Memory Usage")
        print("-" * 40)

        contextual_prompts = [
            ("I'm feeling stressed about work today.", "Stress Context"),
            (
                "Can you recommend some weekend activities for me?",
                "Activity Recommendation",
            ),
            (
                "I'm thinking about getting another pet. What do you think?",
                "Pet Advice",
            ),
            ("What career advice would you give me?", "Career Guidance"),
        ]

        success = True
        for prompt, test_name in contextual_prompts:
            result = await self.run_interaction(prompt, test_name)
            if not result["success"]:
                success = False

        self.test_results.append({"test": "contextual_memory", "success": success})
        return success

    async def run_all_tests(self) -> bool:
        """Run all memory tests and generate a comprehensive report."""
        print("🚀 Starting Comprehensive Memory Test Suite")
        print("=" * 60)

        # Initialize agent
        if not await self.initialize_agent():
            return False

        # Run all test phases
        test_methods = [
            self.test_basic_memory_creation,
            self.test_memory_recall,
            self.test_memory_integration,
            self.test_memory_updates,
            self.test_duplicate_prevention,
            self.test_contextual_memory,
        ]

        overall_success = True
        for test_method in test_methods:
            try:
                result = await test_method()
                if not result:
                    overall_success = False
            except Exception as e:
                print(f"❌ Test method {test_method.__name__} failed with error: {e}")
                overall_success = False

        # Generate report
        await self.generate_test_report()

        # Cleanup
        await self.cleanup()

        return overall_success

    async def generate_test_report(self):
        """Generate a comprehensive test report."""
        print("\n📊 MEMORY TEST REPORT")
        print("=" * 60)

        # Overall results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])

        print(f"Total Test Categories: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        print("\n📋 Test Category Results:")
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"  {status} - {result['test']}")

        # Interaction statistics
        total_interactions = len(self.interactions_log)
        successful_interactions = sum(
            1 for log in self.interactions_log if log["success"]
        )

        print(f"\n💬 Interaction Statistics:")
        print(f"Total Interactions: {total_interactions}")
        print(f"Successful: {successful_interactions}")
        print(f"Failed: {total_interactions - successful_interactions}")

        if successful_interactions > 0:
            avg_duration = (
                sum(
                    log.get("duration_ms", 0)
                    for log in self.interactions_log
                    if log["success"]
                )
                / successful_interactions
            )
            print(f"Average Response Time: {avg_duration:.0f}ms")

        # Save detailed log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"memory_test_log_{timestamp}.json"

        test_summary = {
            "timestamp": datetime.now().isoformat(),
            "user_id": self.user_id,
            "test_results": self.test_results,
            "interactions_log": self.interactions_log,
            "summary": {
                "total_test_categories": total_tests,
                "passed_categories": passed_tests,
                "success_rate": (passed_tests / total_tests) * 100,
                "total_interactions": total_interactions,
                "successful_interactions": successful_interactions,
            },
        }

        with open(log_file, "w") as f:
            json.dump(test_summary, f, indent=2)

        print(f"\n📄 Detailed log saved to: {log_file}")

    async def cleanup(self):
        """Clean up agent resources."""
        if self.agent:
            await self.agent.cleanup()
            print("\n🧹 Agent cleanup completed")


async def main():
    """Run the memory test suite."""
    test_suite = MemoryTestSuite(user_id=USER_ID)

    try:
        success = await test_suite.run_all_tests()

        if success:
            print("\n🎉 ALL MEMORY TESTS COMPLETED SUCCESSFULLY!")
        else:
            print("\n⚠️  Some memory tests encountered issues. Check the report above.")

    except KeyboardInterrupt:
        print("\n⏹️  Test suite interrupted by user")
        await test_suite.cleanup()
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        await test_suite.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
