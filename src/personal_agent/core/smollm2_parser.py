"""
SmolLM2-specific response parsing utilities.

This module provides specialized parsing functions for SmolLM2 models,
which use a different response format than standard models.
"""

import json
import re
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def parse_smollm2_response(text: str) -> Union[str, List[Dict[str, Any]]]:
    """Parse a response from SmolLM2 model, extracting tool calls if present.
    
    SmolLM2 uses <tool_call> XML tags to wrap JSON tool call data.
    
    Args:
        text: Response text from the SmolLM2 model
        
    Returns:
        Either the original text (if no tool calls) or a list of tool call dictionaries
    """
    if not text or not isinstance(text, str):
        return text
    
    # Pattern to match <tool_call>...</tool_call> blocks
    pattern = r"<tool_call>(.*?)</tool_call>"
    matches = re.findall(pattern, text, re.DOTALL)
    
    if not matches:
        # No tool calls found, return original text
        return text
    
    tool_calls = []
    for match in matches:
        try:
            # Clean up the JSON content
            json_content = match.strip()
            
            # Parse the JSON
            parsed_calls = json.loads(json_content)
            
            # Handle both single tool call and list of tool calls
            if isinstance(parsed_calls, list):
                tool_calls.extend(parsed_calls)
            elif isinstance(parsed_calls, dict):
                tool_calls.append(parsed_calls)
            else:
                logger.warning(f"Unexpected tool call format: {type(parsed_calls)}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse tool call JSON: {e}")
            logger.debug(f"Raw content: {json_content}")
            continue
    
    if tool_calls:
        logger.debug(f"Parsed {len(tool_calls)} tool calls from SmolLM2 response")
        return tool_calls
    else:
        # Failed to parse any tool calls, return original text
        return text


def format_smollm2_system_prompt(tools: Optional[List[Dict[str, Any]]] = None) -> str:
    """Format a system prompt for SmolLM2 with tool definitions.
    
    Args:
        tools: List of tool definitions in JSON schema format
        
    Returns:
        Formatted system prompt string
    """
    if not tools:
        tools = []
    
    tools_json = json.dumps(tools, indent=2)
    
    system_prompt = f"""You are an expert in composing functions. You are given a question and a set of possible functions.
Based on the question, you will need to make one or more function/tool calls to achieve the purpose.
If none of the functions can be used, point it out and refuse to answer.
If the given question lacks the parameters required by the function, also point it out.

You have access to the following tools:
<tools>{tools_json}</tools>

The output MUST strictly adhere to the following format, and NO other text MUST be included.
The example format is as follows. Please make sure the parameter type is correct. If no function call is needed, please make the tool calls an empty list '[]'.
<tool_call>[
{{"name": "func_name1", "arguments": {{"argument1": "value1", "argument2": "value2"}}}},
(more tool calls as required)
]</tool_call>"""
    
    return system_prompt


def is_smollm2_model(model_name: str) -> bool:
    """Check if the given model name is a SmolLM2 model.
    
    Args:
        model_name: Name of the model to check
        
    Returns:
        True if it's a SmolLM2 model, False otherwise
    """
    return "smollm2" in model_name.lower()


def extract_content_from_smollm2_response(text: str) -> str:
    """Extract readable content from SmolLM2 response, handling tool response tags properly.
    
    SmolLM2 sometimes wraps the entire response in <tool_response> tags, so we need to
    extract the content from inside these tags rather than removing them entirely.
    
    Args:
        text: Raw response text from SmolLM2
        
    Returns:
        Clean content text without tool call/response XML tags
    """
    if not text or not isinstance(text, str):
        return text
    
    # Remove tool call blocks (for input)
    cleaned_text = re.sub(r"<tool_call>.*?</tool_call>", "", text, flags=re.DOTALL)
    
    # Handle tool response blocks - extract content from inside the tags
    tool_response_pattern = r"<tool_response>(.*?)</tool_response>"
    tool_response_matches = re.findall(tool_response_pattern, cleaned_text, flags=re.DOTALL)
    
    if tool_response_matches:
        # If we found tool_response tags, check if they contain actual response content
        for match in tool_response_matches:
            match_content = match.strip()
            # If the content looks like JSON (tool output), remove it
            if match_content.startswith('{') and match_content.endswith('}'):
                try:
                    json.loads(match_content)  # Validate it's JSON
                    # It's JSON tool output, remove the entire block
                    cleaned_text = re.sub(r"<tool_response>.*?</tool_response>", "", cleaned_text, flags=re.DOTALL)
                except json.JSONDecodeError:
                    # Not valid JSON, might be actual response content, extract it
                    cleaned_text = re.sub(tool_response_pattern, r"\1", cleaned_text, flags=re.DOTALL)
            else:
                # Not JSON, likely actual response content, extract it
                cleaned_text = re.sub(tool_response_pattern, r"\1", cleaned_text, flags=re.DOTALL)
    
    # Clean up extra whitespace and newlines
    cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text.strip())
    
    return cleaned_text


def prepare_smollm2_messages(
    query: str,
    tools: Optional[List[Dict[str, Any]]] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> List[Dict[str, str]]:
    """Prepare messages for SmolLM2 in the expected format.
    
    Args:
        query: User query
        tools: Available tools in JSON schema format
        history: Previous conversation history
        
    Returns:
        List of message dictionaries formatted for SmolLM2
    """
    if tools is None:
        tools = []
        
    if history:
        messages = history.copy()
        messages.append({"role": "user", "content": query})
    else:
        system_content = format_smollm2_system_prompt(tools)
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": query}
        ]
    
    return messages