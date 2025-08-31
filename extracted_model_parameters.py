# Generated model parameters from Ollama models
# Run this script to extract parameters: python extract_model_parameters.py

from typing import Dict
from personal_agent.config.model_contexts import ModelParameters

# Model parameter database - extracted from Ollama models
MODEL_PARAMETERS: Dict[str, ModelParameters] = {
    "hf.co/unsloth/qwen3-30b-a3b-thinking-2507-gguf:Q4_K_M": ModelParameters(temperature=0.6, top_p=0.95, top_k=20),
    "gemma3:1b": ModelParameters(temperature=1.0, top_p=0.95, top_k=64),
    # Models with ModelParameters(temperature=0.6, top_p=0.95, top_k=20, repetition_penalty=1.0)
    "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M": ModelParameters(temperature=0.6, top_p=0.95, top_k=20, repetition_penalty=1.0),
    "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K": ModelParameters(temperature=0.6, top_p=0.95, top_k=20, repetition_penalty=1.0),
    "qwen3": ModelParameters(temperature=0.6, top_p=0.95, top_k=20, repetition_penalty=1.0),
    "qwen3:1.7B": ModelParameters(temperature=0.6, top_p=0.95, top_k=20, repetition_penalty=1.0),
    "qwen3:4b": ModelParameters(temperature=0.6, top_p=0.95, top_k=20, repetition_penalty=1.0),
    "qwen3:8b": ModelParameters(temperature=0.6, top_p=0.95, top_k=20, repetition_penalty=1.0),
    "sam860/qwen3-embedding:0.6b-F16": ModelParameters(temperature=0.6, top_p=0.95, top_k=20, repetition_penalty=1.0),
    "gpt-oss:20b": ModelParameters(temperature=1.0),
    "orieg/gemma3-tools:4b": ModelParameters(temperature=1.0, top_p=0.9, top_k=64),
    "myaniu/qwen2.5-1m": ModelParameters(temperature=0.5, top_p=0.95),
    # Default fallback parameters for unknown models
    "default": ModelParameters(temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1),
}
