"""
Structured response handling for JSON-based Ollama outputs.

This module provides classes and utilities for handling structured JSON responses
from Ollama models, improving response parsing and metadata extraction.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a structured tool call."""
    function_name: str
    arguments: Dict[str, Any]
    reasoning: Optional[str] = None


@dataclass
class ResponseMetadata:
    """Metadata associated with a structured response."""
    confidence: Optional[float] = None
    sources: List[str] = field(default_factory=list)
    reasoning_steps: List[str] = field(default_factory=list)
    response_type: str = "structured"


@dataclass
class ResponseError:
    """Error information in a structured response."""
    code: str
    message: str
    recoverable: bool = True


@dataclass
class StructuredResponse:
    """Complete structured response from the agent."""
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    metadata: Optional[ResponseMetadata] = None
    error: Optional[ResponseError] = None
    
    @property
    def has_tool_calls(self) -> bool:
        """Check if response contains tool calls."""
        return len(self.tool_calls) > 0
    
    @property
    def tool_calls_count(self) -> int:
        """Get number of tool calls."""
        return len(self.tool_calls)


class StructuredResponseParser:
    """Parser for converting JSON responses to StructuredResponse objects."""
    
    # JSON Schema for structured responses
    RESPONSE_SCHEMA = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "Main response content for the user"
            },
            "tool_calls": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "function_name": {"type": "string"},
                        "arguments": {"type": "object"},
                        "reasoning": {"type": "string"}
                    },
                    "required": ["function_name", "arguments"]
                }
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "reasoning_steps": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "response_type": {"type": "string"}
                }
            },
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "recoverable": {"type": "boolean"}
                }
            }
        },
        "required": ["content"]
    }
    
    @classmethod
    def parse(cls, response_text: str) -> StructuredResponse:
        """
        Parse a response string into a StructuredResponse object.
        
        Args:
            response_text: Raw response text (JSON or plain text)
            
        Returns:
            StructuredResponse object
        """
        try:
            # Log the raw response for debugging
            logger.debug("Parsing response text: %s", response_text[:200] + "..." if len(response_text) > 200 else response_text)
            
            # Try to parse as JSON first
            if response_text.strip().startswith('{'):
                # Check if JSON is complete
                if not response_text.strip().endswith('}'):
                    logger.warning("Incomplete JSON detected, falling back to text parsing")
                    return cls._parse_text_response(response_text)
                
                data = json.loads(response_text)
                return cls._parse_json_response(data)
            else:
                # Fallback to plain text response
                return cls._parse_text_response(response_text)
                
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse JSON response: %s. Response: %s", e, response_text[:100])
            return cls._parse_text_response(response_text)
        except Exception as e:
            logger.error("Error parsing response: %s", e)
            return StructuredResponse(
                content=response_text,
                error=ResponseError(
                    code="PARSE_ERROR",
                    message=f"Failed to parse response: {str(e)}",
                    recoverable=True
                )
            )
    
    @classmethod
    def _parse_json_response(cls, data: Dict[str, Any]) -> StructuredResponse:
        """Parse a JSON response into StructuredResponse."""
        try:
            # Extract content
            content = data.get("content", "")
            
            # Parse tool calls
            tool_calls = []
            if "tool_calls" in data and isinstance(data["tool_calls"], list):
                for tc_data in data["tool_calls"]:
                    if isinstance(tc_data, dict):
                        tool_call = ToolCall(
                            function_name=tc_data.get("function_name", "unknown"),
                            arguments=tc_data.get("arguments", {}),
                            reasoning=tc_data.get("reasoning")
                        )
                        tool_calls.append(tool_call)
            
            # Parse metadata
            metadata = None
            if "metadata" in data and isinstance(data["metadata"], dict):
                meta_data = data["metadata"]
                metadata = ResponseMetadata(
                    confidence=meta_data.get("confidence"),
                    sources=meta_data.get("sources", []),
                    reasoning_steps=meta_data.get("reasoning_steps", []),
                    response_type=meta_data.get("response_type", "structured")
                )
            
            # Parse error
            error = None
            if "error" in data and isinstance(data["error"], dict):
                error_data = data["error"]
                error = ResponseError(
                    code=error_data.get("code", "UNKNOWN"),
                    message=error_data.get("message", "Unknown error"),
                    recoverable=error_data.get("recoverable", True)
                )
            
            return StructuredResponse(
                content=content,
                tool_calls=tool_calls,
                metadata=metadata,
                error=error
            )
            
        except Exception as e:
            logger.error("Error parsing JSON response data: %s", e)
            return StructuredResponse(
                content=str(data),
                error=ResponseError(
                    code="JSON_PARSE_ERROR",
                    message=f"Failed to parse JSON data: {str(e)}",
                    recoverable=True
                )
            )
    
    @classmethod
    def _parse_text_response(cls, text: str) -> StructuredResponse:
        """Parse a plain text response into StructuredResponse."""
        return StructuredResponse(
            content=text,
            metadata=ResponseMetadata(response_type="fallback_text")
        )
    
    @classmethod
    def create_system_prompt(cls) -> str:
        """
        Create a system prompt that instructs the model to use structured JSON output.
        
        Returns:
            System prompt string
        """
        return """
You must respond using the following JSON structure. Always return valid JSON that matches this exact schema:

{
  "content": "Your main response to the user goes here",
  "tool_calls": [
    {
      "function_name": "name_of_function_to_call",
      "arguments": {"arg1": "value1", "arg2": "value2"},
      "reasoning": "Why you're calling this function (optional)"
    }
  ],
  "metadata": {
    "confidence": 0.95,
    "sources": ["source1", "source2"],
    "reasoning_steps": ["step1", "step2"],
    "response_type": "structured"
  }
}

CRITICAL RULES:
1. ALWAYS return valid JSON
2. The "content" field is required and contains your main response
3. Include "tool_calls" array if you need to use any tools
4. Add "metadata" with confidence (0.0-1.0) when possible
5. List sources in "sources" array when referencing information
6. If there's an error, include an "error" object with "code", "message", and "recoverable" fields
7. Do not include any text outside the JSON structure
"""


def get_ollama_format_schema() -> Dict[str, Any]:
    """
    Get the format schema for Ollama structured outputs.
    
    Returns:
        Dictionary containing the JSON schema for Ollama format parameter
    """
    return StructuredResponseParser.RESPONSE_SCHEMA


def create_structured_instructions(base_instructions: str) -> str:
    """
    Combine base agent instructions with structured output requirements.
    
    Args:
        base_instructions: Original agent instructions
        
    Returns:
        Enhanced instructions with JSON structure requirements
    """
    structured_prompt = StructuredResponseParser.create_system_prompt()
    
    return f"""
{base_instructions}

## RESPONSE FORMAT REQUIREMENTS

{structured_prompt}

Remember: Your response must be valid JSON following the exact schema above. The user will see the "content" field as your main response.
"""
