"""
Agent Model Manager for the Personal AI Agent.

This module provides a dedicated class for managing model creation and configuration,
extracted from the AgnoPersonalAgent class to improve modularity and maintainability.
"""

# Configure logging
import logging
from typing import Any, Dict, Optional, Union

from agno.models.ollama import Ollama  # Use regular Ollama instead of OllamaTools
from agno.models.openai import OpenAIChat

from ..config.model_contexts import get_model_context_size_sync
from ..config import settings

logger = logging.getLogger(__name__)


class AgentModelManager:
    """Manages model creation and configuration."""

    def __init__(
        self,
        model_provider: str,
        model_name: str,
        ollama_base_url: str,
        seed: Optional[int] = None,
    ):
        """Initialize the model manager.

        Args:
            model_provider: LLM provider ('ollama' or 'openai')
            model_name: Model name to use
            ollama_base_url: Base URL for Ollama API
            seed: Optional seed for model reproducibility
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url
        self.seed = seed

    def create_model(self) -> Union[OpenAIChat, Ollama]:
        """Create the appropriate model instance based on provider.

        Returns:
            Configured model instance (uses regular Ollama for Qwen3 compatibility)

        Raises:
            ValueError: If unsupported model provider is specified
        """
        if self.model_provider == "openai":
            # Use LMStudio URL from settings when provider is openai
            lmstudio_url = settings.LMSTUDIO_URL
            
            # Check if we're using LMStudio (localhost:1234 indicates LMStudio)
            if "localhost:1234" in lmstudio_url or "1234" in lmstudio_url:
                # Use LMStudio with OpenAI-compatible API
                # Ensure the base URL has the correct /v1 endpoint for LMStudio
                base_url = lmstudio_url
                if not base_url.endswith('/v1'):
                    base_url = base_url.rstrip('/') + '/v1'
                
                logger.info(f"Using LMStudio with OpenAI-compatible API at: {base_url}")
                logger.info(f"Model: {self.model_name}")
                logger.info("This will use /v1/chat/completions endpoint (OpenAI format)")
                
                # Remove response_format constraint to allow native OpenAI tool calling
                # LMStudio should support OpenAI's standard tool calling via the tools parameter
                model = OpenAIChat(
                    id=self.model_name,
                    base_url=base_url,  # Use corrected base URL with /v1 endpoint
                    api_key="lm-studio",  # LMStudio doesn't require a real API key
                    # No request_params with response_format - let OpenAI handle tool calling natively
                )
                
                # WORKAROUND: Fix incorrect role mapping in Agno framework
                # The default_role_map incorrectly maps "system" -> "developer"
                # but OpenAI API only accepts: user, assistant, system, tool
                if hasattr(model, "role_map"):
                    model.role_map = {
                        "system": "system",  # Fix: should be "system", not "developer"
                        "user": "user",
                        "assistant": "assistant",
                        "tool": "tool",
                        "model": "assistant",
                    }
                    logger.info(f"🔧 Applied role mapping fix to LMStudio model: {self.model_name}")
                
                return model
            else:
                # Standard OpenAI API
                logger.info(f"Using standard OpenAI API with model: {self.model_name}")
                model = OpenAIChat(id=self.model_name)
                
                # WORKAROUND: Fix incorrect role mapping in Agno framework
                # The default_role_map incorrectly maps "system" -> "developer"
                # but OpenAI API only accepts: user, assistant, system, tool
                if hasattr(model, "role_map"):
                    model.role_map = {
                        "system": "system",  # Fix: should be "system", not "developer"
                        "user": "user",
                        "assistant": "assistant",
                        "tool": "tool",
                        "model": "assistant",
                    }
                    logger.info(f"🔧 Applied role mapping fix to OpenAI model: {self.model_name}")
                
                return model
        elif self.model_provider == "ollama":
            # Get dynamic context size for this model
            context_size, detection_method = get_model_context_size_sync(
                self.model_name, self.ollama_base_url
            )

            logger.info(
                "Using context size %d for model %s (detected via: %s)",
                context_size,
                self.model_name,
                detection_method,
            )

            # Special handling for smollm2 model using optimized configuration
            if "smollm2" in self.model_name.lower():
                logger.info(
                    "Using optimized configuration for SmolLM2 model: %s",
                    self.model_name,
                )

                # CRITICAL: Use the instruct model, not the base model
                model_id = self.model_name

                # Use regular Ollama with configuration optimized for SmolLM2
                model = Ollama(
                    id=model_id,
                    host=self.ollama_base_url,
                    options={
                        "temperature": 0.0,  # Use deterministic generation for tool calls
                        "num_ctx": context_size,  # Use dynamically detected context window
                        "num_predict": 512,  # Allow more tokens for tool call responses
                        "top_p": 1.0,  # Use full probability distribution
                        "top_k": -1,  # Disable top-k sampling for deterministic results
                        "repeat_penalty": 1.0,  # Disable repeat penalty
                        "seed": self.seed,
                        # SmolLM2 specific options
                        "mirostat": 0,  # Disable mirostat sampling
                        "mirostat_eta": 0.1,
                        "mirostat_tau": 5.0,
                    },
                )
                
                # WORKAROUND: Fix incorrect role mapping in Agno framework
                # The default_role_map incorrectly maps "system" -> "developer"
                # but OpenAI API only accepts: user, assistant, system, tool
                if hasattr(model, "role_map"):
                    model.role_map = {
                        "system": "system",  # Fix: should be "system", not "developer"
                        "user": "user",
                        "assistant": "assistant",
                        "tool": "tool",
                        "model": "assistant",
                    }
                    logger.info(f"🔧 Applied role mapping fix to SmolLM2 model: {self.model_name}")
                
                return model
            else:
                # Use standard configuration for other models
                model_options = {
                    "num_ctx": context_size,  # Use dynamically detected context window
                    "temperature": 0.7,  # Optional: set temperature for consistency
                    "num_predict": -1,  # Allow unlimited prediction length
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "seed": self.seed,
                }

                # Special handling for qwen3 models with optimized parameters
                if "qwen3" in self.model_name.lower():
                    logger.info(
                        "Using optimized configuration for Qwen3 model: %s",
                        self.model_name,
                    )
                    model_options.update(
                        {
                            "num_predict": 32768,  # Set specific prediction length for qwen3
                            "temperature": 0.6,
                            "top_k": 20,
                            "top_p": 0.95,
                            "min_p": 0,
                            "repeat_penalty": 1.1,
                        }
                    )

                if "llama3.1" in self.model_name.lower():
                    logger.info(
                        "Using optimized configuration for Llama 3.1 model: %s",
                        self.model_name,
                    )
                    model_options.update(
                        {
                            "stop": ["<|start_header_id|>", "<|end_header_id|>", "<|eot_id|>"],
                        }
                    )

                # Add reasoning support for compatible models
                reasoning_models = [
                    "o1",
                    "o1-preview",
                    "o1-mini",  # OpenAI reasoning models
                    "qwen",
                    "qwq",  # Qwen reasoning models
                    "deepseek-r1",
                    "deepseek-reasoner",  # DeepSeek reasoning models
                    "llama3.2",
                    "llama3.3",  # Recent Llama models with reasoning
                    "mistral",
                    "mixtral",  # Mistral models with reasoning capabilities
                    "smollm2",
                ]

                # Check if current model supports reasoning
                model_supports_reasoning = any(
                    reasoning_model in self.model_name.lower()
                    for reasoning_model in reasoning_models
                )

                if model_supports_reasoning:
                    logger.info(
                        "Model %s supports reasoning - using standard Ollama configuration",
                        self.model_name,
                    )
                else:
                    logger.info(
                        "Model %s does not appear to support reasoning - using standard configuration",
                        self.model_name,
                    )

                model = Ollama(
                    id=self.model_name,
                    host=self.ollama_base_url,  # Use host parameter for Ollama
                    options=model_options,
                )
                
                # WORKAROUND: Fix incorrect role mapping in Agno framework
                # The default_role_map incorrectly maps "system" -> "developer"
                # but OpenAI API only accepts: user, assistant, system, tool
                if hasattr(model, "role_map"):
                    model.role_map = {
                        "system": "system",  # Fix: should be "system", not "developer"
                        "user": "user",
                        "assistant": "assistant",
                        "tool": "tool",
                        "model": "assistant",
                    }
                    logger.info(f"🔧 Applied role mapping fix to Ollama model: {self.model_name}")
                
                return model
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")
