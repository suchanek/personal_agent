"""
Agent Model Manager for the Personal AI Agent.

This module provides a dedicated class for managing model creation and configuration,
extracted from the AgnoPersonalAgent class to improve modularity and maintainability.
"""

from typing import Union, Optional, Dict, Any

from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat

from ..config.model_contexts import get_model_context_size_sync

# Configure logging
import logging
logger = logging.getLogger(__name__)


class AgentModelManager:
    """Manages model creation and configuration."""
    
    def __init__(self, model_provider: str, model_name: str, ollama_base_url: str, seed: Optional[int] = None):
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
            Configured model instance
            
        Raises:
            ValueError: If unsupported model provider is specified
        """
        if self.model_provider == "openai":
            return OpenAIChat(id=self.model_name)
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

            # Use Ollama-compatible interface with optimized configuration
            return Ollama(
                id=self.model_name,
                host=self.ollama_base_url,  # Use host parameter for Ollama
                options={
                    "num_ctx": context_size,  # Use dynamically detected context window
                    "temperature": 0.7,  # Optional: set temperature for consistency
                    "num_predict": -1,  # Allow unlimited prediction length
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "seed": self.seed,
                },
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")