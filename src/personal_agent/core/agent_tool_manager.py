"""
Agent Tool Manager for the Personal AI Agent.

This module provides a dedicated class for managing tool operations,
extracted from the AgnoPersonalAgent class to improve modularity and maintainability.
"""

import asyncio
import inspect
import json
import os
from typing import Dict, List, Optional, Tuple, Union, Any, Callable

# Configure logging
import logging
logger = logging.getLogger(__name__)


class AgentToolManager:
    """Manages tool operations including registration, validation, and execution."""
    
    def __init__(self, user_id: str, storage_dir: str):
        """Initialize the tool manager.
        
        Args:
            user_id: User identifier for tool operations
            storage_dir: Directory for storage files
        """
        self.user_id = user_id
        self.storage_dir = storage_dir
        self.tools = {}
        self.tool_categories = {}
        self.tool_descriptions = {}
        self.tool_parameters = {}
        self.tool_examples = {}
        
    def register_tool(self, 
                      tool_func: Callable, 
                      name: Optional[str] = None, 
                      description: Optional[str] = None,
                      category: str = "general",
                      parameters: Optional[Dict] = None,
                      examples: Optional[List[Dict]] = None) -> str:
        """Register a tool function with the agent.
        
        Args:
            tool_func: The function to register as a tool
            name: Optional custom name for the tool (defaults to function name)
            description: Optional description of the tool
            category: Category for the tool (e.g., 'general', 'memory', 'knowledge')
            parameters: Optional parameter descriptions
            examples: Optional examples of tool usage
            
        Returns:
            The registered tool name
        """
        # Get function name if not provided
        tool_name = name or tool_func.__name__
        
        # Get function signature and docstring
        sig = inspect.signature(tool_func)
        doc = inspect.getdoc(tool_func) or ""
        
        # Extract parameter information
        params = {}
        for param_name, param in sig.parameters.items():
            # Skip 'self' parameter
            if param_name == 'self':
                continue
                
            param_info = {
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                "required": param.default == inspect.Parameter.empty,
            }
            
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
                
            params[param_name] = param_info
            
        # Register the tool
        self.tools[tool_name] = tool_func
        self.tool_descriptions[tool_name] = description or doc
        self.tool_categories[tool_name] = category
        self.tool_parameters[tool_name] = parameters or params
        self.tool_examples[tool_name] = examples or []
        
        logger.info(f"Registered tool: {tool_name} in category {category}")
        return tool_name
        
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool.
        
        Args:
            tool_name: Name of the tool to unregister
            
        Returns:
            True if tool was unregistered successfully
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            del self.tool_descriptions[tool_name]
            del self.tool_categories[tool_name]
            del self.tool_parameters[tool_name]
            del self.tool_examples[tool_name]
            logger.info(f"Unregistered tool: {tool_name}")
            return True
        else:
            logger.warning(f"Tool not found: {tool_name}")
            return False
            
    def get_tool(self, tool_name: str) -> Optional[Callable]:
        """Get a tool function by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool function or None if not found
        """
        return self.tools.get(tool_name)
        
    def get_tool_info(self, tool_name: str) -> Dict:
        """Get information about a tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with tool information
        """
        if tool_name not in self.tools:
            return {"error": f"Tool not found: {tool_name}"}
            
        return {
            "name": tool_name,
            "description": self.tool_descriptions.get(tool_name, ""),
            "category": self.tool_categories.get(tool_name, "general"),
            "parameters": self.tool_parameters.get(tool_name, {}),
            "examples": self.tool_examples.get(tool_name, [])
        }
        
    def get_all_tools(self, category: Optional[str] = None) -> List[Dict]:
        """Get information about all registered tools, optionally filtered by category.
        
        Args:
            category: Optional category to filter by
            
        Returns:
            List of tool information dictionaries
        """
        tools_info = []
        
        for tool_name in self.tools:
            # Skip if category filter is applied and doesn't match
            if category and self.tool_categories.get(tool_name) != category:
                continue
                
            tools_info.append(self.get_tool_info(tool_name))
            
        return tools_info
        
    def get_tool_categories(self) -> List[str]:
        """Get all tool categories.
        
        Returns:
            List of unique tool categories
        """
        return list(set(self.tool_categories.values()))
        
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool by name with the provided arguments.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Result of the tool execution
        """
        tool_func = self.get_tool(tool_name)
        
        if not tool_func:
            error_msg = f"Tool not found: {tool_name}"
            logger.error(error_msg)
            return {"error": error_msg}
            
        try:
            # Check if the tool is a coroutine function
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**kwargs)
            else:
                result = tool_func(**kwargs)
                
            return result
        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
            
    def validate_tool_args(self, tool_name: str, args: Dict) -> Tuple[bool, Optional[str]]:
        """Validate arguments for a tool.
        
        Args:
            tool_name: Name of the tool
            args: Arguments to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if tool_name not in self.tools:
            return False, f"Tool not found: {tool_name}"
            
        parameters = self.tool_parameters.get(tool_name, {})
        
        # Check for required parameters
        for param_name, param_info in parameters.items():
            if param_info.get("required", False) and param_name not in args:
                return False, f"Missing required parameter: {param_name}"
                
        # Check for unknown parameters
        for arg_name in args:
            if arg_name not in parameters:
                return False, f"Unknown parameter: {arg_name}"
                
        return True, None
        
    def format_tool_for_llm(self, tool_name: str) -> Dict:
        """Format tool information for LLM consumption.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Dictionary with formatted tool information
        """
        if tool_name not in self.tools:
            return {"error": f"Tool not found: {tool_name}"}
            
        tool_info = self.get_tool_info(tool_name)
        
        # Format parameters for LLM
        formatted_params = []
        for param_name, param_info in tool_info["parameters"].items():
            param_desc = {
                "name": param_name,
                "type": param_info.get("type", "Any"),
                "required": param_info.get("required", False)
            }
            
            if "default" in param_info:
                param_desc["default"] = param_info["default"]
                
            formatted_params.append(param_desc)
            
        # Format examples for LLM
        formatted_examples = []
        for example in tool_info["examples"]:
            formatted_examples.append({
                "input": example.get("input", {}),
                "output": example.get("output", "")
            })
            
        return {
            "name": tool_name,
            "description": tool_info["description"],
            "parameters": formatted_params,
            "examples": formatted_examples
        }
        
    def format_all_tools_for_llm(self, category: Optional[str] = None) -> List[Dict]:
        """Format all tools for LLM consumption, optionally filtered by category.
        
        Args:
            category: Optional category to filter by
            
        Returns:
            List of formatted tool information dictionaries
        """
        formatted_tools = []
        
        for tool_name in self.tools:
            # Skip if category filter is applied and doesn't match
            if category and self.tool_categories.get(tool_name) != category:
                continue
                
            formatted_tools.append(self.format_tool_for_llm(tool_name))
            
        return formatted_tools
        
    def save_tools_config(self, filename: Optional[str] = None) -> bool:
        """Save tool configuration to a file.
        
        Args:
            filename: Optional filename (defaults to user_id_tools.json)
            
        Returns:
            True if configuration was saved successfully
        """
        try:
            # Use default filename if not provided
            if not filename:
                filename = os.path.join(self.storage_dir, f"{self.user_id}_tools.json")
                
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Prepare tool configuration
            tools_config = {}
            
            for tool_name in self.tools:
                # Skip built-in tools that can't be serialized
                if inspect.isbuiltin(self.tools[tool_name]):
                    continue
                    
                tools_config[tool_name] = {
                    "description": self.tool_descriptions.get(tool_name, ""),
                    "category": self.tool_categories.get(tool_name, "general"),
                    "parameters": self.tool_parameters.get(tool_name, {}),
                    "examples": self.tool_examples.get(tool_name, [])
                }
                
            # Save to file
            with open(filename, "w") as f:
                json.dump(tools_config, f, indent=2)
                
            logger.info(f"Saved tools configuration to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving tools configuration: {e}")
            return False
            
    def load_tools_config(self, filename: Optional[str] = None) -> bool:
        """Load tool configuration from a file.
        
        Args:
            filename: Optional filename (defaults to user_id_tools.json)
            
        Returns:
            True if configuration was loaded successfully
        """
        try:
            # Use default filename if not provided
            if not filename:
                filename = os.path.join(self.storage_dir, f"{self.user_id}_tools.json")
                
            # Check if file exists
            if not os.path.exists(filename):
                logger.warning(f"Tools configuration file not found: {filename}")
                return False
                
            # Load from file
            with open(filename, "r") as f:
                tools_config = json.load(f)
                
            # Update tool configuration
            for tool_name, config in tools_config.items():
                # Skip if tool doesn't exist
                if tool_name not in self.tools:
                    logger.warning(f"Tool not found: {tool_name}")
                    continue
                    
                self.tool_descriptions[tool_name] = config.get("description", "")
                self.tool_categories[tool_name] = config.get("category", "general")
                self.tool_parameters[tool_name] = config.get("parameters", {})
                self.tool_examples[tool_name] = config.get("examples", [])
                
            logger.info(f"Loaded tools configuration from {filename}")
            return True
        except Exception as e:
            logger.error(f"Error loading tools configuration: {e}")
            return False