"""
Model context size configuration and detection.

This module provides dynamic context size detection for different LLM models,
ensuring optimal performance by using each model's full context window capacity.
It also provides model-specific parameter configurations for temperature, top_p,
top_k, and repetition_penalty settings.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import requests

from ..utils import setup_logging
from .settings import OLLAMA_URL, get_env_var

logger = setup_logging(__name__)


@dataclass
class ModelParameters:
    """Container for complete model configuration including parameters and context size."""

    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repetition_penalty: float = 1.1
    context_size: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repetition_penalty": self.repetition_penalty,
        }
        if self.context_size is not None:
            result["context_size"] = self.context_size
        return result

    def __post_init__(self):
        """Validate parameters after initialization."""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(
                f"Temperature must be between 0.0 and 2.0, got {self.temperature}"
            )
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError(f"Top P must be between 0.0 and 1.0, got {self.top_p}")
        if not 1 <= self.top_k <= 1000:
            raise ValueError(f"Top K must be between 1 and 1000, got {self.top_k}")
        if not 0.0 <= self.repetition_penalty <= 2.0:
            raise ValueError(
                f"Repetition penalty must be between 0.0 and 2.0, got {self.repetition_penalty}"
            )
        if self.context_size is not None and self.context_size <= 0:
            raise ValueError(f"Context size must be positive, got {self.context_size}")


# Unified model configuration database - includes both parameters and context sizes
MODEL_PARAMETERS: Dict[str, ModelParameters] = {
    # Qwen models - extracted from actual Ollama installations
    "qwen3": ModelParameters(
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=40960,
    ),
    "qwen3:1.7b": ModelParameters(
        temperature=0.2,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.05,
        context_size=40960,
    ),
    "qwen3:4b": ModelParameters(
        temperature=0.2,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.05,
        context_size=40960,
    ),
    "qwen3:7b": ModelParameters(
        temperature=0.2,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=40960,
    ),
    "qwen3:8b": ModelParameters(
        temperature=0.2,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.05,
        context_size=12232,
    ),
    "qwen3:14b": ModelParameters(
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=40960,
    ),
    "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M": ModelParameters(
        temperature=0.7,
        top_p=0.8,
        top_k=20,
        repetition_penalty=1.0,
        context_size=12232,
    ),
    "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:q8_0": ModelParameters(
        temperature=0.7,
        top_p=0.8,
        top_k=20,
        repetition_penalty=1.05,
        context_size=12232,
    ),
    "hf.co/unsloth/Qwen3-4B-Thinking-2507-GGUF:q8_0": ModelParameters(
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.05,
        context_size=12232,
    ),
    # Lowercase variant for case-insensitive matching
    "hf.co/unsloth/qwen3-4b-instruct-2507-gguf:q8_0": ModelParameters(
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.05,
        context_size=12232,
    ),
    "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K": ModelParameters(
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=12232,
    ),
    "hf.co/unsloth/qwen3-30b-a3b-thinking-2507-gguf:Q4_K_M": ModelParameters(
        temperature=0.7,
        top_p=0.8,
        top_k=20,
        context_size=12232,
        repetition_penalty=1.05,
    ),
    # LM Studio Qwen models - using LM Studio defaults with increased context
    "qwen3-4b-mlx": ModelParameters(
        temperature=0.8,
        top_p=0.9,  # Default top_p when not specified
        top_k=100,
        repetition_penalty=1.1,
        context_size=131072,  # Increased to 128K context for LM Studio
    ),
    "qwen3-4b-instruct-2507-mlx": ModelParameters(
        temperature=0.8,
        top_p=0.9,  # Default top_p when not specified
        top_k=100,
        repetition_penalty=1.1,
        context_size=131072,  # Increased to 128K context for LM Studio
    ),
    "qwen3-8b-mlx@4bit": ModelParameters(
        temperature=0.8,
        top_p=0.9,  # Default top_p when not specified
        top_k=100,
        repetition_penalty=1.1,
        context_size=131072,  # Increased to 128K context for LM Studio
    ),
    "sam860/qwen3-embedding:0.6b-F16": ModelParameters(
        temperature=0.1,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=40960,
    ),
    # Qwen 2.5 models - using similar parameters to Qwen 3
    "qwen2.5:0.5b": ModelParameters(
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=12232,
    ),
    "qwen2.5:1.5b": ModelParameters(
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=12232,
    ),
    "qwen2.5:3b": ModelParameters(
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=12232,
    ),
    "qwen2.5:7b": ModelParameters(
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=12232,
    ),
    "qwen2.5:14b": ModelParameters(
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=12232,
    ),
    "qwen2.5:32b": ModelParameters(
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=12232,
    ),
    "qwen2.5:72b": ModelParameters(
        temperature=0.6,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=12232,
    ),
    "qwen2.5-coder:3b": ModelParameters(
        temperature=0.2,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=12232,
    ),  # Lower temp for coding
    "hf.co/qwen/qwen2.5-coder-7b-instruct-gguf": ModelParameters(
        temperature=0.2,
        top_p=0.95,
        top_k=20,
        repetition_penalty=1.0,
        context_size=12232,
    ),
    "myaniu/qwen2.5-1m:latest": ModelParameters(
        temperature=0.5, top_p=0.95, context_size=12232
    ),  # 1M context
    # Llama models - balanced parameters for instruction following
    "llama3.1:8b": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=12232,
    ),
    "llama3.1:8b-instruct-q8_0": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=12232,
    ),
    "llama3.1:70b": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=12232,
    ),
    "llama3.1:405b": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=12232,
    ),
    "llama3.2": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=12232,
    ),
    "llama3.2:1b": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=12232,
    ),
    "llama3.2:3b": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=12232,
    ),
    "llama3.2:11b": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=12232,
    ),
    "llama3.2:90b": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=12232,
    ),
    "llama3.3:latest": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=12232,
    ),
    "llama3.3:70b": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=12232,
    ),
    "llama3:8b": ModelParameters(
        temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1, context_size=12232
    ),
    "llama3:70b": ModelParameters(
        temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1, context_size=12232
    ),
    "llama3-groq-tool-use": ModelParameters(
        temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1, context_size=12232
    ),
    "hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=12232,
    ),
    # Mistral models - slightly more creative parameters
    "mistral:7b": ModelParameters(
        temperature=0.8, top_p=0.9, top_k=50, repetition_penalty=1.1, context_size=12232
    ),
    "mistral:instruct": ModelParameters(
        temperature=0.8, top_p=0.9, top_k=50, repetition_penalty=1.1, context_size=12232
    ),
    "mistral-nemo": ModelParameters(
        temperature=0.8, top_p=0.9, top_k=50, repetition_penalty=1.1, context_size=12232
    ),
    "mixtral:8x7b": ModelParameters(
        temperature=0.8, top_p=0.9, top_k=50, repetition_penalty=1.1, context_size=12232
    ),
    "mixtral:8x22b": ModelParameters(
        temperature=0.8, top_p=0.9, top_k=50, repetition_penalty=1.1, context_size=65536
    ),
    # Gemma models - extracted and balanced parameters
    "gemma3:1b": ModelParameters(
        temperature=1.0, top_p=0.95, top_k=64, context_size=12232
    ),
    "orieg/gemma3-tools:4b": ModelParameters(
        temperature=1.0, top_p=0.9, top_k=64, context_size=12232
    ),
    "gemma:2b": ModelParameters(
        temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1, context_size=12232
    ),
    "gemma:7b": ModelParameters(
        temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1, context_size=12232
    ),
    "gemma2:9b": ModelParameters(
        temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1, context_size=12232
    ),
    "gemma2:27b": ModelParameters(
        temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1, context_size=12232
    ),
    # CodeLlama models - focused parameters for code generation
    "codellama:7b": ModelParameters(
        temperature=0.2,
        top_p=0.95,
        top_k=50,
        repetition_penalty=1.05,
        context_size=16384,
    ),
    "codellama:13b": ModelParameters(
        temperature=0.2,
        top_p=0.95,
        top_k=50,
        repetition_penalty=1.05,
        context_size=16384,
    ),
    "codellama:34b": ModelParameters(
        temperature=0.2,
        top_p=0.95,
        top_k=50,
        repetition_penalty=1.05,
        context_size=16384,
    ),
    # Phi models - optimized for reasoning
    "phi3:3.8b": ModelParameters(
        temperature=0.6,
        top_p=0.9,
        top_k=30,
        repetition_penalty=1.1,
        context_size=128000,
    ),
    "phi3:14b": ModelParameters(
        temperature=0.6,
        top_p=0.9,
        top_k=30,
        repetition_penalty=1.1,
        context_size=128000,
    ),
    "phi3.5:3.8b": ModelParameters(
        temperature=0.6,
        top_p=0.9,
        top_k=30,
        repetition_penalty=1.1,
        context_size=128000,
    ),
    # Granite models - IBM's open-source models
    "granite3.1-dense:2b": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=65536,  # 64K context (128K capable, reduced for 24GB systems)
    ),
    "granite3.1-dense:8b": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=65536,  # 64K context (128K capable, reduced for 24GB systems)
    ),
    "granite3.1-moe:1b": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=65536,  # 64K context (128K capable, reduced for 24GB systems)
    ),
    "granite3.1-moe:3b": ModelParameters(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        repetition_penalty=1.1,
        context_size=65536,  # 64K context (128K capable, reduced for 24GB systems)
    ),
    # SmolLM models
    "smollm2:1.7B": ModelParameters(
        temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1, context_size=12232
    ),
    # Other specialized models
    "gpt-oss:20b": ModelParameters(temperature=1.0, context_size=12232),
    "nomic-embed-text": ModelParameters(
        temperature=0.1, top_p=0.9, top_k=10, repetition_penalty=1.0, context_size=8192
    ),  # Embedding model - low temp
    # Neural Chat models
    "neural-chat:7b": ModelParameters(
        temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1, context_size=12232
    ),
    # Orca models - conservative parameters for smaller models
    "orca-mini:3b": ModelParameters(
        temperature=0.6, top_p=0.8, top_k=30, repetition_penalty=1.15, context_size=2048
    ),
    "orca-mini:7b": ModelParameters(
        temperature=0.6, top_p=0.8, top_k=30, repetition_penalty=1.15, context_size=2048
    ),
    "orca-mini:13b": ModelParameters(
        temperature=0.6, top_p=0.8, top_k=30, repetition_penalty=1.15, context_size=2048
    ),
    # Vicuna models - conservative parameters for smaller models
    "vicuna:7b": ModelParameters(
        temperature=0.6, top_p=0.8, top_k=30, repetition_penalty=1.15, context_size=2048
    ),
    "vicuna:13b": ModelParameters(
        temperature=0.6, top_p=0.8, top_k=30, repetition_penalty=1.15, context_size=2048
    ),
    "vicuna:33b": ModelParameters(
        temperature=0.6, top_p=0.8, top_k=30, repetition_penalty=1.15, context_size=2048
    ),
    # Default fallback parameters for unknown models
    "default": ModelParameters(
        temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1, context_size=8192
    ),
}

# Model context size database - curated list of known models and their context windows
MODEL_CONTEXT_SIZES: Dict[str, int] = {
    # Qwen models
    "qwen3:1.7b": 40960,  # Updated from 12232 via ollama show verification
    "qwen3:7b": 40960,  # Updated to match other qwen3 models
    "qwen3:8b": 40960,  # Updated from 12232 via ollama show verification
    "qwen3:14b": 40960,  # Updated from 12232 via ollama show verification
    "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M": 262144,
    "qwen2.5:0.5b": 12232,
    "qwen2.5:1.5b": 12232,
    "qwen2.5:3b": 12232,
    "qwen2.5:7b": 12232,
    "qwen2.5:14b": 12232,
    "qwen2.5:32b": 12232,
    "qwen2.5:72b": 12232,
    "hf.co/unsloth/qwen3-30b-a3b-thinking-2507-gguf:q4_k_m": 262144,
    # Llama 3.1 models (128K context) - Updated via ollama show verification
    "llama3.1:8b": 12232,  # Updated from 12232
    "llama3.1:8b-instruct-q8_0": 12232,  # Updated from 12232
    "llama3.1:70b": 12232,  # Updated from 12232 (estimated based on verified models)
    "llama3.1:405b": 12232,  # Updated from 12232 (estimated based on verified models)
    # Llama 3.2 models (128K context) - Updated via ollama show verification
    "llama3.2:1b": 12232,  # Updated from 12232 (estimated based on verified models)
    "llama3.2:3b": 12232,  # Updated from 12232
    "llama3.2:11b": 12232,  # Updated from 12232 (estimated based on verified models)
    "llama3.2:90b": 12232,  # Updated from 12232 (estimated based on verified models)
    # Llama 3.3 models (131K context)
    "llama3.3:latest": 12232,
    "llama3.3:70b": 12232,
    # Llama 3 models (8K context)
    "llama3:8b": 12232,
    "llama3:70b": 12232,
    # Mistral models
    "mistral:7b": 12232,
    "mistral:instruct": 12232,
    "mixtral:8x7b": 12232,
    "mixtral:8x22b": 65536,
    # CodeLlama models
    "codellama:7b": 16384,
    "codellama:13b": 16384,
    "codellama:34b": 16384,
    # Gemma models
    "gemma:2b": 12232,
    "gemma:7b": 12232,
    "gemma2:9b": 12232,
    "gemma2:27b": 12232,
    # Phi models
    "phi3:3.8b": 128000,
    "phi3:14b": 128000,
    "phi3.5:3.8b": 128000,
    # Granite models - IBM's open-source models
    "granite3.1-dense:2b": 65536,  # 64K context (128K capable, reduced for 24GB systems)
    "granite3.1-dense:8b": 65536,  # 64K context (128K capable, reduced for 24GB systems)
    "granite3.1-moe:1b": 65536,  # 64K context (128K capable, reduced for 24GB systems)
    "granite3.1-moe:3b": 65536,  # 64K context (128K capable, reduced for 24GB systems)
    # Neural Chat models
    "neural-chat:7b": 12232,
    # Orca models
    "orca-mini:3b": 2048,
    "orca-mini:7b": 2048,
    "orca-mini:13b": 2048,
    # Vicuna models
    "vicuna:7b": 2048,
    "vicuna:13b": 2048,
    "vicuna:33b": 2048,
    # Default fallback for unknown models
    "default": 4096,
}

# Environment variable overrides
MODEL_CONTEXT_OVERRIDES: Dict[str, str] = {
    # Format: "MODEL_NAME_CTX_SIZE" -> model_name
    # Example: QWEN3_1_7B_CTX_SIZE=16384 would override qwen3:1.7b
}


def normalize_model_name(model_name: str) -> str:
    """
    Normalize model name for consistent lookup.

    Args:
        model_name: Raw model name from configuration

    Returns:
        Normalized model name for database lookup
    """
    # Convert to lowercase and handle common variations
    normalized = model_name.lower().strip()

    # Handle common naming variations
    variations = {
        "qwen3:1.7": "qwen3:1.7b",
        "llama3.1:8b-instruct": "llama3.1:8b-instruct-q8_0",
        "llama-3.1:8b": "llama3.1:8b",
        "llama-3.2:3b": "llama3.2:3b",
    }

    return variations.get(normalized, normalized)


def extract_context_from_model_name(model_name: str) -> Optional[int]:
    """
    Try to extract context size from model name patterns.

    Some models include context size in their names like "model-32k" or "model-128k".

    Args:
        model_name: Model name to analyze

    Returns:
        Context size in tokens if found, None otherwise
    """
    # Look for patterns like "32k", "128k", "4096", etc.
    patterns = [
        r"(\d+)k(?:_ctx|_context)?",  # Matches "32k", "128k_ctx", etc.
        r"(\d+)_ctx",  # Matches "4096_ctx"
        r"ctx_?(\d+)",  # Matches "ctx4096", "ctx_4096"
        r"context_?(\d+)",  # Matches "context4096"
    ]

    for pattern in patterns:
        match = re.search(pattern, model_name.lower())
        if match:
            size_str = match.group(1)
            try:
                size = int(size_str)
                # If it's in "k" format, multiply by 1024
                if "k" in pattern:
                    size *= 1024
                return size
            except ValueError:
                continue

    return None


async def query_ollama_model_info(
    model_name: str, ollama_url: str = OLLAMA_URL
) -> Optional[Dict]:
    """
    Query Ollama API for model information including context size.

    Args:
        model_name: Name of the model to query
        ollama_url: Ollama server URL

    Returns:
        Model info dict if successful, None otherwise
    """
    try:
        # Try to get model info from Ollama API
        response = requests.get(
            f"{ollama_url}/api/show", json={"name": model_name}, timeout=5
        )

        if response.status_code == 200:
            model_info = response.json()
            logger.debug("Retrieved model info for %s: %s", model_name, model_info)
            return model_info
        else:
            logger.debug(
                "Failed to get model info for %s: HTTP %d",
                model_name,
                response.status_code,
            )
            return None

    except Exception as e:
        logger.debug("Error querying Ollama for model %s: %s", model_name, e)
        return None


def extract_context_from_ollama_info(model_info: Dict) -> Optional[int]:
    """
    Extract context size from Ollama model info response.

    Args:
        model_info: Model info dict from Ollama API

    Returns:
        Context size if found, None otherwise
    """
    try:
        # Check various possible locations for context size in the response

        # Check parameters section
        if "parameters" in model_info:
            params = model_info["parameters"]

            # Look for num_ctx parameter
            if "num_ctx" in params:
                return int(params["num_ctx"])

            # Look for context_length parameter
            if "context_length" in params:
                return int(params["context_length"])

        # Check model details
        if "details" in model_info:
            details = model_info["details"]

            # Look for context size in details
            for key in ["context_size", "context_length", "num_ctx", "max_context"]:
                if key in details:
                    return int(details[key])

        # Check template or config sections
        for section in ["template", "config", "modelfile"]:
            if section in model_info:
                section_data = model_info[section]
                if isinstance(section_data, str):
                    # Look for PARAMETER num_ctx in modelfile
                    match = re.search(r"PARAMETER\s+num_ctx\s+(\d+)", section_data)
                    if match:
                        return int(match.group(1))

        return None

    except (ValueError, KeyError, TypeError) as e:
        logger.debug("Error extracting context from model info: %s", e)
        return None


def get_env_override_for_model(model_name: str) -> Optional[int]:
    """
    Check for environment variable override for specific model.

    Args:
        model_name: Model name to check

    Returns:
        Override context size if found, None otherwise
    """
    # Convert model name to env var format
    # qwen3:1.7b -> QWEN3_1_7B_CTX_SIZE
    env_name = model_name.upper().replace(":", "_").replace(".", "_").replace("-", "_")
    env_var = f"{env_name}_CTX_SIZE"

    override_value = get_env_var(env_var)
    if override_value:
        try:
            return int(override_value)
        except ValueError:
            logger.warning(
                "Invalid context size override for %s: %s", model_name, override_value
            )

    # Also check for a general override
    general_override = get_env_var("DEFAULT_MODEL_CTX_SIZE")
    if general_override:
        try:
            return int(general_override)
        except ValueError:
            logger.warning(
                "Invalid default context size override: %s", general_override
            )

    return None


async def get_model_context_size(
    model_name: str, ollama_url: str = OLLAMA_URL
) -> Tuple[int, str]:
    """
    Get the optimal context size for a given model using multiple detection methods.

    Detection priority:
    1. Environment variable override
    2. Ollama API query
    3. Model name pattern extraction
    4. Database lookup
    5. Default fallback

    Args:
        model_name: Name of the model
        ollama_url: Ollama server URL for API queries

    Returns:
        Tuple of (context_size, detection_method)
    """
    logger.debug("Determining context size for model: %s", model_name)

    # 1. Check environment variable override first
    env_override = get_env_override_for_model(model_name)
    if env_override:
        logger.debug(
            "Using environment override for %s: %d tokens", model_name, env_override
        )
        return env_override, "environment_override"

    # 2. Try querying Ollama API for model info
    try:
        model_info = await query_ollama_model_info(model_name, ollama_url)
        if model_info:
            ollama_context = extract_context_from_ollama_info(model_info)
            if ollama_context:
                logger.debug(
                    "Detected context size from Ollama API for %s: %d tokens",
                    model_name,
                    ollama_context,
                )
                return ollama_context, "ollama_api"
    except Exception as e:
        logger.debug("Failed to query Ollama API: %s", e)

    # 3. Try extracting from model name patterns
    name_context = extract_context_from_model_name(model_name)
    if name_context:
        logger.debug(
            "Extracted context size from model name %s: %d tokens",
            model_name,
            name_context,
        )
        return name_context, "model_name_pattern"

    # 4. Look up in our curated database
    # First try the original model name (for case-sensitive models like HuggingFace)
    if model_name in MODEL_CONTEXT_SIZES:
        db_context = MODEL_CONTEXT_SIZES[model_name]
        logger.debug(
            "Found context size in database for %s: %d tokens", model_name, db_context
        )
        return db_context, "database_lookup"

    # Then try the normalized name for standard models
    normalized_name = normalize_model_name(model_name)
    if normalized_name in MODEL_CONTEXT_SIZES:
        db_context = MODEL_CONTEXT_SIZES[normalized_name]
        logger.debug(
            "Found context size in database for %s: %d tokens", model_name, db_context
        )
        return db_context, "database_lookup"

    # 5. Use default fallback
    default_context = MODEL_CONTEXT_SIZES["default"]
    logger.warning(
        "Using default context size for unknown model %s: %d tokens",
        model_name,
        default_context,
    )
    return default_context, "default_fallback"


def get_model_context_size_sync(
    model_name: str, ollama_url: str = OLLAMA_URL
) -> Tuple[int, str]:
    """
    Synchronous version of get_model_context_size for compatibility.

    This version skips the Ollama API query and uses other detection methods.
    Now prioritizes the unified ModelParameters database.

    Args:
        model_name: Name of the model
        ollama_url: Ollama server URL (unused in sync version)

    Returns:
        Tuple of (context_size, detection_method)
    """
    logger.debug("Determining context size for model (sync): %s", model_name)

    # 1. Check environment variable override first
    env_override = get_env_override_for_model(model_name)
    if env_override:
        logger.debug(
            "Using environment override for %s: %d tokens", model_name, env_override
        )
        return env_override, "environment_override"

    # 2. Try extracting from model name patterns
    name_context = extract_context_from_model_name(model_name)
    if name_context:
        logger.debug(
            "Extracted context size from model name %s: %d tokens",
            model_name,
            name_context,
        )
        return name_context, "model_name_pattern"

    # 3. Look up in our unified ModelParameters database first
    # First try the original model name (for case-sensitive models like HuggingFace)
    if model_name in MODEL_PARAMETERS:
        model_params = MODEL_PARAMETERS[model_name]
        if model_params.context_size is not None:
            logger.debug(
                "Found context size in unified database for %s: %d tokens",
                model_name,
                model_params.context_size,
            )
            return model_params.context_size, "database_lookup"

    # Then try the normalized name for standard models
    normalized_name = normalize_model_name(model_name)
    if normalized_name in MODEL_PARAMETERS:
        model_params = MODEL_PARAMETERS[normalized_name]
        if model_params.context_size is not None:
            logger.debug(
                "Found context size in unified database for %s: %d tokens",
                model_name,
                model_params.context_size,
            )
            return model_params.context_size, "database_lookup"

    # 4. Fallback to legacy context size database
    # First try the original model name
    if model_name in MODEL_CONTEXT_SIZES:
        db_context = MODEL_CONTEXT_SIZES[model_name]
        logger.debug(
            "Found context size in legacy database for %s: %d tokens",
            model_name,
            db_context,
        )
        return db_context, "database_lookup"

    # Then try the normalized name
    if normalized_name in MODEL_CONTEXT_SIZES:
        db_context = MODEL_CONTEXT_SIZES[normalized_name]
        logger.debug(
            "Found context size in legacy database for %s: %d tokens",
            model_name,
            db_context,
        )
        return db_context, "database_lookup"

    # 5. Use default fallback from unified database
    default_params = MODEL_PARAMETERS["default"]
    if default_params.context_size is not None:
        logger.warning(
            "Using default context size for unknown model %s: %d tokens",
            model_name,
            default_params.context_size,
        )
        return default_params.context_size, "default_fallback"

    # Final fallback to legacy default
    default_context = MODEL_CONTEXT_SIZES["default"]
    logger.warning(
        "Using legacy default context size for unknown model %s: %d tokens",
        model_name,
        default_context,
    )
    return default_context, "default_fallback"


def add_model_to_database(model_name: str, context_size: int) -> None:
    """
    Add a new model to the context size database.

    Args:
        model_name: Name of the model
        context_size: Context size in tokens
    """
    normalized_name = normalize_model_name(model_name)
    MODEL_CONTEXT_SIZES[normalized_name] = context_size
    logger.debug(
        "Added model %s to context database: %d tokens", normalized_name, context_size
    )


def list_supported_models() -> Dict[str, int]:
    """
    Get a list of all models in the context size database.

    Returns:
        Dictionary mapping model names to context sizes
    """
    return MODEL_CONTEXT_SIZES.copy()


def get_context_size_summary(model_name: str, ollama_url: str = OLLAMA_URL) -> str:
    """
    Get a human-readable summary of context size detection for a model.

    Args:
        model_name: Name of the model
        ollama_url: Ollama server URL

    Returns:
        Formatted summary string
    """
    context_size, method = get_model_context_size_sync(model_name, ollama_url)

    method_descriptions = {
        "environment_override": "Environment variable override",
        "ollama_api": "Ollama API query",
        "model_name_pattern": "Model name pattern extraction",
        "database_lookup": "Curated database lookup",
        "default_fallback": "Default fallback (unknown model)",
    }

    method_desc = method_descriptions.get(method, method)

    return f"Model: {model_name}\nContext Size: {context_size:,} tokens\nDetection Method: {method_desc}"


# Model parameter functions


def get_env_parameter_overrides_for_model(model_name: str) -> Dict[str, Any]:
    """
    Check for environment variable overrides for model parameters.

    Args:
        model_name: Model name to check

    Returns:
        Dictionary of parameter overrides found in environment variables
    """
    # Convert model name to env var format
    # qwen3:1.7b -> QWEN3_1_7B
    env_name = model_name.upper().replace(":", "_").replace(".", "_").replace("-", "_")

    overrides = {}

    # Check for specific parameter overrides
    param_mappings = {
        "TEMPERATURE": "temperature",
        "TOP_P": "top_p",
        "TOP_K": "top_k",
        "REPETITION_PENALTY": "repetition_penalty",
    }

    for env_suffix, param_name in param_mappings.items():
        env_var = f"{env_name}_{env_suffix}"
        override_value = get_env_var(env_var)
        if override_value:
            try:
                if param_name == "top_k":
                    overrides[param_name] = int(override_value)
                else:
                    overrides[param_name] = float(override_value)
            except ValueError:
                logger.warning(
                    "Invalid %s override for %s: %s",
                    param_name,
                    model_name,
                    override_value,
                )

    # Also check for general default overrides
    general_mappings = {
        "DEFAULT_TEMPERATURE": "temperature",
        "DEFAULT_TOP_P": "top_p",
        "DEFAULT_TOP_K": "top_k",
        "DEFAULT_REPETITION_PENALTY": "repetition_penalty",
    }

    for env_var, param_name in general_mappings.items():
        if param_name not in overrides:  # Don't override specific model settings
            general_override = get_env_var(env_var)
            if general_override:
                try:
                    if param_name == "top_k":
                        overrides[param_name] = int(general_override)
                    else:
                        overrides[param_name] = float(general_override)
                except ValueError:
                    logger.warning(
                        "Invalid default %s override: %s", param_name, general_override
                    )

    return overrides


def get_model_parameters(model_name: str) -> Tuple[ModelParameters, str]:
    """
    Get the optimal parameters for a given model using multiple detection methods.

    Detection priority:
    1. Environment variable override
    2. Database lookup
    3. Default fallback

    Args:
        model_name: Name of the model

    Returns:
        Tuple of (ModelParameters, detection_method)
    """
    logger.debug("Determining parameters for model: %s", model_name)

    # 1. Check environment variable overrides first
    env_overrides = get_env_parameter_overrides_for_model(model_name)

    # 2. Look up in our curated database
    base_params = None
    detection_method = "default_fallback"

    # First try the original model name (for case-sensitive models like HuggingFace)
    if model_name in MODEL_PARAMETERS:
        base_params = MODEL_PARAMETERS[model_name]
        detection_method = "database_lookup"
        logger.debug("Found parameters in database for %s", model_name)
    else:
        # Then try the normalized name for standard models
        normalized_name = normalize_model_name(model_name)
        if normalized_name in MODEL_PARAMETERS:
            base_params = MODEL_PARAMETERS[normalized_name]
            detection_method = "database_lookup"
            logger.debug("Found parameters in database for %s (normalized)", model_name)
        else:
            # Use default fallback
            base_params = MODEL_PARAMETERS["default"]
            logger.warning("Using default parameters for unknown model %s", model_name)

    # 3. Apply environment overrides if any
    if env_overrides:
        logger.debug(
            "Applying environment overrides for %s: %s", model_name, env_overrides
        )
        # Create new parameters with overrides applied
        params_dict = base_params.to_dict()
        params_dict.update(env_overrides)
        final_params = ModelParameters(**params_dict)
        detection_method = "environment_override" if env_overrides else detection_method
        return final_params, detection_method

    return base_params, detection_method


def get_model_parameters_dict(model_name: str) -> Dict[str, Any]:
    """
    Get model parameters as a dictionary for easy integration.

    Args:
        model_name: Name of the model

    Returns:
        Dictionary containing the model parameters
    """
    params, _ = get_model_parameters(model_name)
    return params.to_dict()


def add_model_parameters_to_database(
    model_name: str, parameters: ModelParameters
) -> None:
    """
    Add a new model's parameters to the parameter database.

    Args:
        model_name: Name of the model
        parameters: ModelParameters object with the model's optimal settings
    """
    normalized_name = normalize_model_name(model_name)
    MODEL_PARAMETERS[normalized_name] = parameters
    logger.debug(
        "Added model %s to parameter database: %s", normalized_name, parameters
    )


def list_supported_model_parameters() -> Dict[str, ModelParameters]:
    """
    Get a list of all models in the parameter database.

    Returns:
        Dictionary mapping model names to ModelParameters objects
    """
    return MODEL_PARAMETERS.copy()


def get_model_config_summary(model_name: str, ollama_url: str = OLLAMA_URL) -> str:
    """
    Get a comprehensive summary of both context size and parameters for a model.

    Args:
        model_name: Name of the model
        ollama_url: Ollama server URL

    Returns:
        Formatted summary string with both context and parameter information
    """
    # Get context size info
    context_size, context_method = get_model_context_size_sync(model_name, ollama_url)

    # Get parameter info
    parameters, param_method = get_model_parameters(model_name)

    method_descriptions = {
        "environment_override": "Environment variable override",
        "ollama_api": "Ollama API query",
        "model_name_pattern": "Model name pattern extraction",
        "database_lookup": "Curated database lookup",
        "default_fallback": "Default fallback (unknown model)",
    }

    context_method_desc = method_descriptions.get(context_method, context_method)
    param_method_desc = method_descriptions.get(param_method, param_method)

    return f"""Model: {model_name}
Context Size: {context_size:,} tokens (Detection: {context_method_desc})
Parameters:
  - Temperature: {parameters.temperature}
  - Top P: {parameters.top_p}
  - Top K: {parameters.top_k}
  - Repetition Penalty: {parameters.repetition_penalty}
  (Detection: {param_method_desc})"""


def get_model_config_dict(
    model_name: str, ollama_url: str = OLLAMA_URL
) -> Dict[str, Any]:
    """
    Get complete model configuration as a dictionary.

    Args:
        model_name: Name of the model
        ollama_url: Ollama server URL

    Returns:
        Dictionary containing both context size and parameters
    """
    context_size, context_method = get_model_context_size_sync(model_name, ollama_url)
    parameters, param_method = get_model_parameters(model_name)

    return {
        "model_name": model_name,
        "context_size": context_size,
        "context_detection_method": context_method,
        "parameters": parameters.to_dict(),
        "parameter_detection_method": param_method,
    }
