"""
Model context size configuration and detection.

This module provides dynamic context size detection for different LLM models,
ensuring optimal performance by using each model's full context window capacity.
"""

import json
import logging
import re
from typing import Dict, Optional, Tuple

import requests

from .settings import OLLAMA_URL, get_env_var

logger = logging.getLogger(__name__)

# Model context size database - curated list of known models and their context windows
MODEL_CONTEXT_SIZES: Dict[str, int] = {
    # Qwen models
    "qwen3:1.7b": 32768,
    "qwen3:7b": 32768,
    "qwen3:8b": 32768,
    "qwen3:14b": 32768,
    "qwen2.5:0.5b": 32768,
    "qwen2.5:1.5b": 32768,
    "qwen2.5:3b": 32768,
    "qwen2.5:7b": 32768,
    "qwen2.5:14b": 32768,
    "qwen2.5:32b": 32768,
    "qwen2.5:72b": 32768,
    # Llama 3.1 models (128K context)
    "llama3.1:8b": 32768,
    "llama3.1:8b-instruct-q8_0": 32768,
    "llama3.1:70b": 32768,
    "llama3.1:405b": 32768,
    # Llama 3.2 models (128K context)
    "llama3.2:1b": 32768,
    "llama3.2:3b": 32768,
    "llama3.2:11b": 32768,
    "llama3.2:90b": 32768,
    # Llama 3.3 models (131K context)
    "llama3.3:latest": 131072,
    "llama3.3:70b": 131072,
    # Llama 3 models (8K context)
    "llama3:8b": 32768,
    "llama3:70b": 32768,
    # Mistral models
    "mistral:7b": 32768,
    "mistral:instruct": 32768,
    "mixtral:8x7b": 32768,
    "mixtral:8x22b": 65536,
    # CodeLlama models
    "codellama:7b": 16384,
    "codellama:13b": 16384,
    "codellama:34b": 16384,
    # Gemma models
    "gemma:2b": 32768,
    "gemma:7b": 32768,
    "gemma2:9b": 32768,
    "gemma2:27b": 32768,
    # Phi models
    "phi3:3.8b": 128000,
    "phi3:14b": 128000,
    "phi3.5:3.8b": 128000,
    # Neural Chat models
    "neural-chat:7b": 32768,
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
        logger.info(
            "Using environment override for %s: %d tokens", model_name, env_override
        )
        return env_override, "environment_override"

    # 2. Try querying Ollama API for model info
    try:
        model_info = await query_ollama_model_info(model_name, ollama_url)
        if model_info:
            ollama_context = extract_context_from_ollama_info(model_info)
            if ollama_context:
                logger.info(
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
        logger.info(
            "Extracted context size from model name %s: %d tokens",
            model_name,
            name_context,
        )
        return name_context, "model_name_pattern"

    # 4. Look up in our curated database
    normalized_name = normalize_model_name(model_name)
    if normalized_name in MODEL_CONTEXT_SIZES:
        db_context = MODEL_CONTEXT_SIZES[normalized_name]
        logger.info(
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
        logger.info(
            "Using environment override for %s: %d tokens", model_name, env_override
        )
        return env_override, "environment_override"

    # 2. Try extracting from model name patterns
    name_context = extract_context_from_model_name(model_name)
    if name_context:
        logger.info(
            "Extracted context size from model name %s: %d tokens",
            model_name,
            name_context,
        )
        return name_context, "model_name_pattern"

    # 3. Look up in our curated database
    normalized_name = normalize_model_name(model_name)
    if normalized_name in MODEL_CONTEXT_SIZES:
        db_context = MODEL_CONTEXT_SIZES[normalized_name]
        logger.info(
            "Found context size in database for %s: %d tokens", model_name, db_context
        )
        return db_context, "database_lookup"

    # 4. Use default fallback
    default_context = MODEL_CONTEXT_SIZES["default"]
    logger.warning(
        "Using default context size for unknown model %s: %d tokens",
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
    logger.info(
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
