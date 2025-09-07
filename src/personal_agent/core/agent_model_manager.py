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

from ..config import settings
from ..config.model_contexts import get_model_parameters_dict
from ..utils import setup_logging

logger = setup_logging(__name__)


class AgentModelManager:
    """Manages model creation and configuration."""

    def __init__(
        self,
        model_provider: str,
        model_name: str,
        ollama_base_url: str,
        openai_base_url: Optional[str] = None,
        seed: Optional[int] = None,
    ):
        """Initialize the model manager.

        Args:
            model_provider: LLM provider ('ollama' or 'openai')
            model_name: Model name to use
            ollama_base_url: Base URL for Ollama API
            openai_base_url: Optional base URL for OpenAI-compatible APIs.
            seed: Optional seed for model reproducibility
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url
        self.openai_base_url = openai_base_url
        self.seed = seed

    def create_model(self) -> Union[OpenAIChat, Ollama]:
        """Create the appropriate model instance based on provider.

        Returns:
            Configured model instance (uses regular Ollama for Qwen3 compatibility)

        Raises:
            ValueError: If unsupported model provider is specified
        """
        if self.model_provider == "openai":
            # Check if LMSTUDIO_URL is configured and points to LMStudio
            lmstudio_url = getattr(settings, 'LMSTUDIO_URL', None)
            
            # Use LMStudio if LMSTUDIO_URL is set and contains localhost:1234
            if lmstudio_url and ("localhost:1234" in lmstudio_url or "127.0.0.1:1234" in lmstudio_url):
                # Use LMStudio with OpenAI-compatible API
                # Ensure the base URL has the correct /v1 endpoint for LMStudio
                base_url = lmstudio_url
                if not base_url.endswith("/v1"):
                    base_url = base_url.rstrip("/") + "/v1"

                logger.info(
                    f"Using LMStudio with OpenAI-compatible API at: {base_url}"
                )
                logger.info(f"Model: {self.model_name}")
                logger.info(
                    "This will use /v1/chat/completions endpoint (OpenAI format)"
                )

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
                    logger.debug(
                        f"🔧 Applied role mapping fix to LMStudio model: {self.model_name}"
                    )

                return model
            else:
                # Standard OpenAI API - uses OPENAI_API_KEY from environment
                logger.info(f"Using standard OpenAI API with model: {self.model_name}")
                if self.openai_base_url:
                    logger.info(f"Using custom OpenAI base URL: {self.openai_base_url}")
                else:
                    logger.info("Using default OpenAI API endpoint.")
                logger.info(
                    "API Key will be read from OPENAI_API_KEY environment variable"
                )

                model = OpenAIChat(id=self.model_name, base_url=self.openai_base_url)

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
                    logger.info(
                        f"🔧 Applied role mapping fix to OpenAI model: {self.model_name}"
                    )

                return model
        elif self.model_provider == "ollama":
            # Get unified model configuration (parameters + context size)
            model_config = get_model_parameters_dict(self.model_name)

            logger.debug(
                "Using unified model configuration for %s: %s",
                self.model_name,
                model_config,
            )

            # Build model options from unified configuration
            model_options = {
                "num_ctx": model_config.get("context_size", 4096),
                "temperature": model_config.get("temperature", 0.7),
                "top_k": model_config.get("top_k", 40),
                "top_p": model_config.get("top_p", 0.9),
                "repeat_penalty": model_config.get("repetition_penalty", 1.0),
                "num_predict": -1,  # Allow unlimited prediction length
                "seed": self.seed,
            }

            # Special handling for Qwen models - add min_p and adjust num_predict
            if "qwen" in self.model_name.lower():
                logger.debug(
                    "Applying Qwen-specific optimizations for model: %s",
                    self.model_name,
                )
                model_options.update(
                    {
                        "num_predict": 32768,  # Set specific prediction length for Qwen
                        "min_p": 0,  # Qwen-specific parameter
                    }
                )

            # Special handling for Llama 3.x models - add stop tokens
            """
            if (
                "llama3.1" in self.model_name.lower()
                or "llama3.2" in self.model_name.lower()
                or "llama3.3" in self.model_name.lower()
            ):
                logger.debug(
                    "Applying Llama 3.x-specific optimizations for model: %s",
                    self.model_name,
                )
                model_options.update({
                    "stop": [
                        "<|start_header_id|>",
                        "<|end_header_id|>",
                        "<|eot_id|>",
                    ],
                })
            """
            # Add reasoning support for compatible models
            reasoning_models = [
                "o1",
                "o1-preview",
                "o1-mini",  # OpenAI reasoning models
                "qwen3:8b",
                "qwen3:1.7b",
                "qwen3:4b",
                "qwen3-4b-instruct",  # Qwen model variants
                "hf.co/unsloth/qwen3-30b-a3b-thinking-2507-gguf:Q4_K_M",
                "hf.co/unsloth/qwen3-4b-instruct",  # HuggingFace Qwen models
                "qwq",  # Qwen reasoning models
                "deepseek-r1",
                "deepseek-reasoner",  # DeepSeek reasoning models
                "llama3.2",
                "llama3.3",  # Recent Llama models with reasoning
                "mistral",
                "mixtral",  # Mistral models with reasoning capabilities
            ]

            # Check if current model supports reasoning
            model_supports_reasoning = any(
                reasoning_model in self.model_name.lower()
                for reasoning_model in reasoning_models
            )

            if model_supports_reasoning:
                logger.debug(f"Model {self.model_name} supports reasoning capabilities")

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
                logger.debug(
                    f"🔧 Applied role mapping fix to Ollama model: {self.model_name}"
                )

            return model
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")
