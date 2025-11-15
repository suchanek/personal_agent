"""
Unit tests for AgentToolManager.

This module tests the tool management functionality
extracted from the AgnoPersonalAgent class using Python's built-in unittest framework.
"""

import unittest
import asyncio
import json
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from src.personal_agent.core.agent_tool_manager import AgentToolManager


class TestAgentToolManager(unittest.TestCase):
    """Test cases for AgentToolManager."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.user_id = "test_user"
        self.temp_dir = tempfile.mkdtemp()
        
        self.manager = AgentToolManager(
            user_id=self.user_id,
            storage_dir=self.temp_dir
        )
    
    def tearDown(self):
        """Clean up after each test."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test AgentToolManager initialization."""
        self.assertEqual(self.manager.user_id, self.user_id)
        self.assertEqual(self.manager.storage_dir, self.temp_dir)
        self.assertEqual(self.manager.tools, {})
        self.assertEqual(self.manager.tool_categories, {})
        self.assertEqual(self.manager.tool_descriptions, {})
        self.assertEqual(self.manager.tool_parameters, {})
        self.assertEqual(self.manager.tool_examples, {})
    
    def test_register_tool_basic(self):
        """Test registering a basic tool."""
        def test_tool(param1: str, param2: int = 10) -> str:
            """A test tool that does something."""
            return f"Result: {param1}, {param2}"
        
        tool_name = self.manager.register_tool(test_tool)
        
        self.assertEqual(tool_name, "test_tool")
        self.assertIn("test_tool", self.manager.tools)
        self.assertEqual(self.manager.tools["test_tool"], test_tool)
        self.assertEqual(self.manager.tool_categories["test_tool"], "general")
        self.assertIn("A test tool that does something", self.manager.tool_descriptions["test_tool"])
        
        # Check parameters
        params = self.manager.tool_parameters["test_tool"]
        self.assertIn("param1", params)
        self.assertIn("param2", params)
        self.assertTrue(params["param1"]["required"])
        self.assertFalse(params["param2"]["required"])
        self.assertEqual(params["param2"]["default"], 10)
    
    def test_register_tool_with_custom_name(self):
        """Test registering a tool with a custom name."""
        def some_function():
            """Test function."""
            pass
        
        tool_name = self.manager.register_tool(some_function, name="custom_tool")
        
        self.assertEqual(tool_name, "custom_tool")
        self.assertIn("custom_tool", self.manager.tools)
        self.assertEqual(self.manager.tools["custom_tool"], some_function)
    
    def test_register_tool_with_metadata(self):
        """Test registering a tool with full metadata."""
        def advanced_tool(query: str, limit: int = 5) -> dict:
            """An advanced tool."""
            return {"query": query, "limit": limit}
        
        parameters = {
            "query": {"type": "str", "required": True, "description": "Search query"},
            "limit": {"type": "int", "required": False, "default": 5, "description": "Result limit"}
        }
        
        examples = [
            {"input": {"query": "test", "limit": 3}, "output": {"query": "test", "limit": 3}},
            {"input": {"query": "example"}, "output": {"query": "example", "limit": 5}}
        ]
        
        tool_name = self.manager.register_tool(
            advanced_tool,
            name="search_tool",
            description="A tool for searching",
            category="search",
            parameters=parameters,
            examples=examples
        )
        
        self.assertEqual(tool_name, "search_tool")
        self.assertEqual(self.manager.tool_categories["search_tool"], "search")
        self.assertEqual(self.manager.tool_descriptions["search_tool"], "A tool for searching")
        self.assertEqual(self.manager.tool_parameters["search_tool"], parameters)
        self.assertEqual(self.manager.tool_examples["search_tool"], examples)
    
    def test_register_tool_skips_self_parameter(self):
        """Test that 'self' parameter is skipped during registration."""
        class TestClass:
            def method_tool(self, param1: str) -> str:
                """A method tool."""
                return param1
        
        instance = TestClass()
        tool_name = self.manager.register_tool(instance.method_tool)
        
        # Should not include 'self' in parameters
        params = self.manager.tool_parameters[tool_name]
        self.assertNotIn("self", params)
        self.assertIn("param1", params)
    
    def test_unregister_tool(self):
        """Test unregistering a tool."""
        def test_tool():
            """Test tool."""
            pass
        
        # Register the tool
        tool_name = self.manager.register_tool(test_tool)
        self.assertIn(tool_name, self.manager.tools)
        
        # Unregister the tool
        result = self.manager.unregister_tool(tool_name)
        
        self.assertTrue(result)
        self.assertNotIn(tool_name, self.manager.tools)
        self.assertNotIn(tool_name, self.manager.tool_categories)
        self.assertNotIn(tool_name, self.manager.tool_descriptions)
        self.assertNotIn(tool_name, self.manager.tool_parameters)
        self.assertNotIn(tool_name, self.manager.tool_examples)
    
    def test_unregister_nonexistent_tool(self):
        """Test unregistering a tool that doesn't exist."""
        result = self.manager.unregister_tool("nonexistent_tool")
        
        self.assertFalse(result)
    
    def test_get_tool(self):
        """Test getting a tool function."""
        def test_tool():
            """Test tool."""
            return "test result"
        
        tool_name = self.manager.register_tool(test_tool)
        
        retrieved_tool = self.manager.get_tool(tool_name)
        self.assertEqual(retrieved_tool, test_tool)
        
        # Test getting non-existent tool
        non_existent = self.manager.get_tool("nonexistent")
        self.assertIsNone(non_existent)
    
    def test_get_tool_info(self):
        """Test getting tool information."""
        def test_tool(param1: str) -> str:
            """A test tool."""
            return param1
        
        tool_name = self.manager.register_tool(
            test_tool,
            description="Custom description",
            category="test",
            examples=[{"input": {"param1": "test"}, "output": "test"}]
        )
        
        info = self.manager.get_tool_info(tool_name)
        
        self.assertEqual(info["name"], tool_name)
        self.assertEqual(info["description"], "Custom description")
        self.assertEqual(info["category"], "test")
        self.assertIn("param1", info["parameters"])
        self.assertEqual(len(info["examples"]), 1)
    
    def test_get_tool_info_nonexistent(self):
        """Test getting info for non-existent tool."""
        info = self.manager.get_tool_info("nonexistent")
        
        self.assertIn("error", info)
        self.assertIn("Tool not found", info["error"])
    
    def test_get_all_tools(self):
        """Test getting all tools."""
        def tool1():
            """Tool 1."""
            pass
        
        def tool2():
            """Tool 2."""
            pass
        
        self.manager.register_tool(tool1, category="category1")
        self.manager.register_tool(tool2, category="category2")
        
        # Get all tools
        all_tools = self.manager.get_all_tools()
        self.assertEqual(len(all_tools), 2)
        
        tool_names = [tool["name"] for tool in all_tools]
        self.assertIn("tool1", tool_names)
        self.assertIn("tool2", tool_names)
    
    def test_get_all_tools_filtered_by_category(self):
        """Test getting tools filtered by category."""
        def tool1():
            """Tool 1."""
            pass
        
        def tool2():
            """Tool 2."""
            pass
        
        def tool3():
            """Tool 3."""
            pass
        
        self.manager.register_tool(tool1, category="search")
        self.manager.register_tool(tool2, category="memory")
        self.manager.register_tool(tool3, category="search")
        
        # Get tools by category
        search_tools = self.manager.get_all_tools(category="search")
        self.assertEqual(len(search_tools), 2)
        
        tool_names = [tool["name"] for tool in search_tools]
        self.assertIn("tool1", tool_names)
        self.assertIn("tool3", tool_names)
        self.assertNotIn("tool2", tool_names)
    
    def test_get_tool_categories(self):
        """Test getting all tool categories."""
        def tool1():
            pass
        
        def tool2():
            pass
        
        def tool3():
            pass
        
        self.manager.register_tool(tool1, category="search")
        self.manager.register_tool(tool2, category="memory")
        self.manager.register_tool(tool3, category="search")  # Duplicate category
        
        categories = self.manager.get_tool_categories()
        
        self.assertEqual(len(categories), 2)
        self.assertIn("search", categories)
        self.assertIn("memory", categories)
    
    def test_validate_tool_args_valid(self):
        """Test validating tool arguments with valid args."""
        def test_tool(required_param: str, optional_param: int = 10):
            """Test tool."""
            pass
        
        tool_name = self.manager.register_tool(test_tool)
        
        # Valid args with all parameters
        is_valid, error = self.manager.validate_tool_args(tool_name, {
            "required_param": "test",
            "optional_param": 20
        })
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # Valid args with only required parameter
        is_valid, error = self.manager.validate_tool_args(tool_name, {
            "required_param": "test"
        })
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_tool_args_missing_required(self):
        """Test validating tool arguments with missing required parameter."""
        def test_tool(required_param: str, optional_param: int = 10):
            """Test tool."""
            pass
        
        tool_name = self.manager.register_tool(test_tool)
        
        is_valid, error = self.manager.validate_tool_args(tool_name, {
            "optional_param": 20
        })
        
        self.assertFalse(is_valid)
        self.assertIn("Missing required parameter", error)
        self.assertIn("required_param", error)
    
    def test_validate_tool_args_unknown_parameter(self):
        """Test validating tool arguments with unknown parameter."""
        def test_tool(param1: str):
            """Test tool."""
            pass
        
        tool_name = self.manager.register_tool(test_tool)
        
        is_valid, error = self.manager.validate_tool_args(tool_name, {
            "param1": "test",
            "unknown_param": "value"
        })
        
        self.assertFalse(is_valid)
        self.assertIn("Unknown parameter", error)
        self.assertIn("unknown_param", error)
    
    def test_validate_tool_args_nonexistent_tool(self):
        """Test validating arguments for non-existent tool."""
        is_valid, error = self.manager.validate_tool_args("nonexistent", {"param": "value"})
        
        self.assertFalse(is_valid)
        self.assertIn("Tool not found", error)
    
    def test_format_tool_for_llm(self):
        """Test formatting tool information for LLM consumption."""
        def test_tool(param1: str, param2: int = 10) -> str:
            """A test tool for LLM."""
            return f"{param1}:{param2}"
        
        examples = [{"input": {"param1": "test", "param2": 5}, "output": "test:5"}]
        
        tool_name = self.manager.register_tool(
            test_tool,
            description="LLM test tool",
            examples=examples
        )
        
        formatted = self.manager.format_tool_for_llm(tool_name)
        
        self.assertEqual(formatted["name"], tool_name)
        self.assertEqual(formatted["description"], "LLM test tool")
        self.assertEqual(len(formatted["parameters"]), 2)
        
        # Check parameter formatting
        param1 = next(p for p in formatted["parameters"] if p["name"] == "param1")
        param2 = next(p for p in formatted["parameters"] if p["name"] == "param2")
        
        self.assertTrue(param1["required"])
        self.assertFalse(param2["required"])
        self.assertEqual(param2["default"], 10)
        
        # Check examples
        self.assertEqual(len(formatted["examples"]), 1)
        self.assertEqual(formatted["examples"][0]["input"]["param1"], "test")
        self.assertEqual(formatted["examples"][0]["output"], "test:5")
    
    def test_format_tool_for_llm_nonexistent(self):
        """Test formatting non-existent tool for LLM."""
        formatted = self.manager.format_tool_for_llm("nonexistent")
        
        self.assertIn("error", formatted)
        self.assertIn("Tool not found", formatted["error"])
    
    def test_format_all_tools_for_llm(self):
        """Test formatting all tools for LLM consumption."""
        def tool1():
            """Tool 1."""
            pass
        
        def tool2():
            """Tool 2."""
            pass
        
        self.manager.register_tool(tool1, category="category1")
        self.manager.register_tool(tool2, category="category2")
        
        formatted_tools = self.manager.format_all_tools_for_llm()
        
        self.assertEqual(len(formatted_tools), 2)
        tool_names = [tool["name"] for tool in formatted_tools]
        self.assertIn("tool1", tool_names)
        self.assertIn("tool2", tool_names)
    
    def test_format_all_tools_for_llm_filtered(self):
        """Test formatting tools for LLM with category filter."""
        def tool1():
            """Tool 1."""
            pass
        
        def tool2():
            """Tool 2."""
            pass
        
        self.manager.register_tool(tool1, category="search")
        self.manager.register_tool(tool2, category="memory")
        
        formatted_tools = self.manager.format_all_tools_for_llm(category="search")
        
        self.assertEqual(len(formatted_tools), 1)
        self.assertEqual(formatted_tools[0]["name"], "tool1")
    
    def test_save_tools_config(self):
        """Test saving tools configuration to file."""
        def test_tool(param: str) -> str:
            """Test tool."""
            return param
        
        self.manager.register_tool(
            test_tool,
            description="Test description",
            category="test",
            examples=[{"input": {"param": "test"}, "output": "test"}]
        )
        
        result = self.manager.save_tools_config()
        
        self.assertTrue(result)
        
        # Check that file was created
        config_file = os.path.join(self.temp_dir, f"{self.user_id}_tools.json")
        self.assertTrue(os.path.exists(config_file))
        
        # Check file contents
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        self.assertIn("test_tool", config)
        self.assertEqual(config["test_tool"]["description"], "Test description")
        self.assertEqual(config["test_tool"]["category"], "test")
    
    def test_save_tools_config_custom_filename(self):
        """Test saving tools configuration with custom filename."""
        def test_tool():
            """Test tool."""
            pass
        
        self.manager.register_tool(test_tool)
        
        custom_file = os.path.join(self.temp_dir, "custom_tools.json")
        result = self.manager.save_tools_config(custom_file)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(custom_file))
    
    def test_load_tools_config(self):
        """Test loading tools configuration from file."""
        # First register a tool and save config
        def test_tool(param: str):
            """Original description."""
            pass
        
        tool_name = self.manager.register_tool(test_tool, category="original")
        self.manager.save_tools_config()
        
        # Modify the saved config file
        config_file = os.path.join(self.temp_dir, f"{self.user_id}_tools.json")
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        config[tool_name]["description"] = "Updated description"
        config[tool_name]["category"] = "updated"
        config[tool_name]["examples"] = [{"input": {}, "output": "test"}]
        
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        # Load the config
        result = self.manager.load_tools_config()
        
        self.assertTrue(result)
        self.assertEqual(self.manager.tool_descriptions[tool_name], "Updated description")
        self.assertEqual(self.manager.tool_categories[tool_name], "updated")
        self.assertEqual(len(self.manager.tool_examples[tool_name]), 1)
    
    def test_load_tools_config_nonexistent_file(self):
        """Test loading tools configuration when file doesn't exist."""
        result = self.manager.load_tools_config()
        
        self.assertFalse(result)
    
    def test_load_tools_config_nonexistent_tool(self):
        """Test loading config for tools that don't exist."""
        # Create a config file with a non-existent tool
        config_file = os.path.join(self.temp_dir, f"{self.user_id}_tools.json")
        config = {
            "nonexistent_tool": {
                "description": "This tool doesn't exist",
                "category": "test"
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f)
        
        result = self.manager.load_tools_config()
        
        # Should still return True but skip the non-existent tool
        self.assertTrue(result)


class TestAgentToolManagerAsync(unittest.IsolatedAsyncioTestCase):
    """Async test cases for AgentToolManager."""
    
    async def asyncSetUp(self):
        """Set up async test fixtures."""
        self.user_id = "test_user"
        self.temp_dir = tempfile.mkdtemp()
        
        self.manager = AgentToolManager(
            user_id=self.user_id,
            storage_dir=self.temp_dir
        )
    
    async def asyncTearDown(self):
        """Clean up after each async test."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    async def test_execute_tool_sync_function(self):
        """Test executing a synchronous tool function."""
        def sync_tool(message: str) -> str:
            """A synchronous tool."""
            return f"Sync: {message}"
        
        tool_name = self.manager.register_tool(sync_tool)
        
        result = await self.manager.execute_tool(tool_name, message="test")
        
        self.assertEqual(result, "Sync: test")
    
    async def test_execute_tool_async_function(self):
        """Test executing an asynchronous tool function."""
        async def async_tool(message: str) -> str:
            """An asynchronous tool."""
            await asyncio.sleep(0.01)  # Simulate async work
            return f"Async: {message}"
        
        tool_name = self.manager.register_tool(async_tool)
        
        result = await self.manager.execute_tool(tool_name, message="test")
        
        self.assertEqual(result, "Async: test")
    
    async def test_execute_tool_nonexistent(self):
        """Test executing a non-existent tool."""
        result = await self.manager.execute_tool("nonexistent_tool", param="value")
        
        self.assertIn("error", result)
        self.assertIn("Tool not found", result["error"])
    
    async def test_execute_tool_with_exception(self):
        """Test executing a tool that raises an exception."""
        def error_tool():
            """A tool that raises an error."""
            raise ValueError("Test error")
        
        tool_name = self.manager.register_tool(error_tool)
        
        result = await self.manager.execute_tool(tool_name)
        
        self.assertIn("error", result)
        self.assertIn("Error executing tool", result["error"])
        self.assertIn("Test error", result["error"])
    
    async def test_execute_tool_with_kwargs(self):
        """Test executing a tool with keyword arguments."""
        def multi_param_tool(param1: str, param2: int = 10, param3: bool = False) -> dict:
            """A tool with multiple parameters."""
            return {
                "param1": param1,
                "param2": param2,
                "param3": param3
            }
        
        tool_name = self.manager.register_tool(multi_param_tool)
        
        result = await self.manager.execute_tool(
            tool_name,
            param1="test",
            param2=20,
            param3=True
        )
        
        self.assertEqual(result["param1"], "test")
        self.assertEqual(result["param2"], 20)
        self.assertTrue(result["param3"])


class TestAgentToolManagerIntegration(unittest.TestCase):
    """Integration tests for AgentToolManager."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up after integration tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_tool_manager_full_workflow(self):
        """Test a complete workflow with the tool manager."""
        manager = AgentToolManager(
            user_id="integration_test_user",
            storage_dir=self.temp_dir
        )
        
        # Define some test tools
        def search_tool(query: str, limit: int = 5) -> dict:
            """Search for information."""
            return {"query": query, "results": [f"result_{i}" for i in range(limit)]}
        
        def calculate_tool(expression: str) -> float:
            """Calculate a mathematical expression."""
            # Simple calculator (unsafe eval for testing only)
            try:
                return eval(expression)
            except:
                return 0.0
        
        async def async_fetch_tool(url: str) -> dict:
            """Fetch data from a URL asynchronously."""
            await asyncio.sleep(0.01)  # Simulate network delay
            return {"url": url, "status": "success"}
        
        # Register tools
        search_name = manager.register_tool(
            search_tool,
            description="Search for information",
            category="search",
            examples=[{"input": {"query": "test"}, "output": {"query": "test", "results": ["result_0"]}}]
        )
        
        calc_name = manager.register_tool(
            calculate_tool,
            description="Calculate expressions",
            category="math"
        )
        
        fetch_name = manager.register_tool(
            async_fetch_tool,
            description="Fetch data from URLs",
            category="network"
        )
        
        # Test tool registration
        self.assertEqual(len(manager.tools), 3)
        self.assertIn(search_name, manager.tools)
        self.assertIn(calc_name, manager.tools)
        self.assertIn(fetch_name, manager.tools)
        
        # Test categories
        categories = manager.get_tool_categories()
        self.assertIn("search", categories)
        self.assertIn("math", categories)
        self.assertIn("network", categories)
        
        # Test getting tools by category
        search_tools = manager.get_all_tools(category="search")
        self.assertEqual(len(search_tools), 1)
        self.assertEqual(search_tools[0]["name"], search_name)
        
        # Test tool validation
        is_valid, error = manager.validate_tool_args(search_name, {"query": "test", "limit": 3})
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        is_valid, error = manager.validate_tool_args(search_name, {"limit": 3})  # Missing required param
        self.assertFalse(is_valid)
        self.assertIn("Missing required parameter", error)
        
        # Test LLM formatting
        formatted_tools = manager.format_all_tools_for_llm()
        self.assertEqual(len(formatted_tools), 3)
        
        # Test configuration persistence
        result = manager.save_tools_config()
        self.assertTrue(result)
        
        # Create new manager and load config
        manager2 = AgentToolManager(
            user_id="integration_test_user",
            storage_dir=self.temp_dir
        )
        
        # Register the same tools (functions need to be re-registered)
        manager2.register_tool(search_tool)
        manager2.register_tool(calculate_tool)
        manager2.register_tool(async_fetch_tool)
        
        # Load the saved configuration
        result = manager2.load_tools_config()
        self.assertTrue(result)
        
        # Verify configuration was loaded
        self.assertEqual(manager2.tool_descriptions[search_name], "Search for information")
        self.assertEqual(manager2.tool_categories[search_name], "search")
    
    def test_tool_manager_realistic_scenario(self):
        """Test tool manager with realistic tools and scenarios."""
        manager = AgentToolManager(
            user_id="realistic_user",
            storage_dir=self.temp_dir
        )
        
        # Define realistic tools
        def get_weather(city: str, units: str = "celsius") -> dict:
            """Get weather information for a city."""
            return {
                "city": city,
                "temperature": 22 if units == "celsius" else 72,
                "units": units,
                "condition": "sunny"
            }
        
        def send_email(to: str, subject: str, body: str, cc: list = None) -> dict:
            """Send an email."""
            return {
                "to": to,
                "subject": subject,
                "body": body,
                "cc": cc or [],
                "status": "sent"
            }
        
        def file_search(pattern: str, directory: str = ".", recursive: bool = True) -> list:
            """Search for files matching a pattern."""
            return [
                f"{directory}/file1.txt",
                f"{directory}/file2.py",
                f"{directory}/subdir/file3.md"
            ] if recursive else [f"{directory}/file1.txt"]
        
        # Register tools with proper metadata
        weather_tool = manager.register_tool(
            get_weather,
            description="Get current weather information for any city",
            category="information",
            examples=[
                {"input": {"city": "New York"}, "output": {"city": "New York", "temperature": 22}},
                {"input": {"city": "London", "units": "fahrenheit"}, "output": {"city": "London", "temperature": 72}}
            ]
        )
        
        email_tool = manager.register_tool(
            send_email,
            description="Send emails to recipients",
            category="communication",
            examples=[
                {"input": {"to": "user@example.com", "subject": "Test", "body": "Hello"}, "output": {"status": "sent"}}
            ]
        )
        
        search_tool = manager.register_tool(
            file_search,
            description="Search for files in directories",
            category="filesystem"
        )
        
        # Test comprehensive tool information
        all_tools = manager.get_all_tools()
        self.assertEqual(len(all_tools), 3)
        
        # Test tool info retrieval
        weather_info = manager.get_tool_info(weather_tool)
        self.assertEqual(weather_info["category"], "information")
        self.assertEqual(len(weather_info["examples"]), 2)
        self.assertIn("city", weather_info["parameters"])
        self.assertIn("units", weather_info["parameters"])
        
        # Test parameter validation with complex scenarios
        # Valid email with all parameters
        is_valid, error = manager.validate_tool_args(email_tool, {
            "to": "user@example.com",
            "subject": "Test Subject",
            "body": "Test Body",
            "cc": ["cc@example.com"]
        })
        self.assertTrue(is_valid)
        
        # Valid email with minimal parameters
        is_valid, error = manager.validate_tool_args(email_tool, {
            "to": "user@example.com",
            "subject": "Test",
            "body": "Hello"
        })
        self.assertTrue(is_valid)
        
        # Invalid email missing required parameter
        is_valid, error = manager.validate_tool_args(email_tool, {
            "subject": "Test",
            "body": "Hello"
        })
        self.assertFalse(is_valid)
        self.assertIn("Missing required parameter: to", error)


if __name__ == "__main__":
    unittest.main()
