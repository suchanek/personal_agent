# Qwen3-8B Large Language Model

## Overview

Qwen3-8B is a large language model from the Qwen series, featuring 8.2 billion parameters. It is designed to be a versatile and powerful model with a focus on reasoning, multilingual capabilities, and integration with external tools.

## Key Features

*   **Parameters:** 8.2 billion
*   **Context Length:** Supports a context length of up to 32,768 tokens, which can be extended to 131,072 tokens using YaRN.
*   **Dual Modes:** The model can operate in two distinct modes:
    *   **Thinking Mode:** Optimized for complex tasks that require reasoning and coding abilities.
    *   **Non-thinking Mode:** Designed for general conversation and less computationally intensive tasks.
*   **Improved Reasoning:** Qwen3-8B shows significant improvements in mathematical, coding, and logical reasoning tasks compared to previous Qwen models.
*   **Multilingual Support:** The model has been trained on a diverse dataset and supports over 100 languages and dialects.
*   **Agent Capabilities:** It can be integrated with external tools and APIs to perform complex, multi-step tasks.

## Usage

Qwen3-8B can be used with the Hugging Face `transformers` library. It is also supported by various other tools and platforms, including:

*   `sglang`
*   `vllm`
*   `Ollama`
*   `LMStudio`

The model card on Hugging Face provides detailed code examples and best practices for using the model effectively, including how to switch between modes and process long text inputs.
