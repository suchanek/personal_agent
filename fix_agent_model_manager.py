"""
Simple fix: Replace OllamaTools with regular Ollama class in AgentModelManager
"""

from agno.models.ollama import Ollama  # Use regular Ollama instead of OllamaTools
from agno.models.openai import OpenAIChat
from src.personal_agent.config.model_contexts import get_model_context_size_sync
import logging

logger = logging.getLogger(__name__)

class FixedAgentModelManager:
    """Fixed version that uses regular Ollama instead of OllamaTools."""

    def __init__(
        self,
        model_provider: str,
        model_name: str,
        ollama_base_url: str,
        seed: Optional[int] = None,
    ):
        self.model_provider = model_provider
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url
        self.seed = seed

    def create_model(self):
        """Create model using regular Ollama class for Qwen3 compatibility."""
        if self.model_provider == "openai":
            return OpenAIChat(id=self.model_name)
        elif self.model_provider == "ollama":
            # Get dynamic context size
            context_size, detection_method = get_model_context_size_sync(
                self.model_name, self.ollama_base_url
            )

            logger.info(
                "Using context size %d for model %s (detected via: %s)",
                context_size,
                self.model_name,
                detection_method,
            )

            # Use regular Ollama class instead of OllamaTools
            model_options = {
                "num_ctx": context_size,
                "temperature": 0.7,
                "num_predict": -1,
                "top_k": 40,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "seed": self.seed,
            }

            # Special handling for qwen3 models
            if "qwen3" in self.model_name.lower():
                logger.info(
                    "Using optimized configuration for Qwen3 model: %s",
                    self.model_name,
                )
                model_options.update({
                    "num_predict": 32768,
                    "temperature": 0.6,
                    "top_k": 20,
                    "top_p": 0.95,
                    "min_p": 0,
                    "repeat_penalty": 1.1,
                })

            # Use regular Ollama class - this should work with Qwen3
            return Ollama(
                id=self.model_name,
                host=self.ollama_base_url,
                options=model_options,
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

# Test the fix
if __name__ == "__main__":
    from typing import Optional
    
    # Test with Qwen3
    manager = FixedAgentModelManager(
        model_provider="ollama",
        model_name="qwen3:8b",
        ollama_base_url="http://localhost:11434",
        seed=42
    )
    
    model = manager.create_model()
    print(f"Created model: {type(model).__name__}")
    print(f"Model ID: {model.id}")
    print(f"Model host: {model.host}")
    print("✓ Successfully created regular Ollama model instead of OllamaTools")