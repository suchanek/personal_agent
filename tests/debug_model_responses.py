#!/usr/bin/env python3
"""
Debug script to analyze responses from different Ollama models.

This script queries specified LLMs with a set of prompts and prints their responses
to help analyze and compare their performance and output style.
"""

import json
import subprocess
import sys
import time

# Configuration
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
MODELS_TO_TEST = ["llama3.1:8b-instruct-q8_0", "qwen3:1.7B"]
PROMPTS_TO_TEST = [
    "hello",
    "summarize the top news stories in AI",
    "summarize the top news stories about the war in Ukraine",
]


def get_model_response(model_name, prompt):
    """
    Queries a specific Ollama model with a given prompt and prints the response.

    Args:
        model_name (str): The name of the model to query.
        prompt (str): The prompt to send to the model.

    Returns:
        tuple: A tuple containing the response text and the elapsed time.
    """
    print(f"--- Querying {model_name} for: '{prompt}' ---")
    start_time = time.time()
    response_text = ""
    try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,  # We want the full response at once
        }
        command = ["curl", "-s", OLLAMA_ENDPOINT, "-d", json.dumps(payload)]

        # Execute the curl command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=300,  # 5-minute timeout for potentially long responses
        )

        # Parse the JSON response
        response_data = json.loads(result.stdout)

        # Print the main response content
        if "response" in response_data:
            response_text = response_data["response"]
            print(response_text)
        else:
            response_text = "No 'response' key found in the output."
            print(response_text)
            print("Full response:")
            print(response_data)

    except FileNotFoundError:
        response_text = "Error: 'curl' command not found. Please ensure curl is installed and in your PATH."
        print(response_text)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        response_text = f"Error calling Ollama API: {e}\nStderr: {e.stderr}"
        print(response_text)
    except subprocess.TimeoutExpired:
        response_text = "Error: The request to the Ollama API timed out."
        print(response_text)
    except json.JSONDecodeError:
        response_text = f"Error: Failed to decode JSON response from the server.\nRaw response: {result.stdout}"
        print(response_text)
    except Exception as e:
        response_text = f"An unexpected error occurred: {e}"
        print(response_text)
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Time taken: {elapsed_time:.2f} seconds")
        print("-" * (len(model_name) + len(prompt) + 14))
        print("\n")
        return response_text, elapsed_time


def main():
    """
    Main function to iterate through models and prompts, get responses, and print a summary.
    """
    print("Starting model response analysis...")
    results = []
    for model in MODELS_TO_TEST:
        for prompt in PROMPTS_TO_TEST:
            response, r_time = get_model_response(model, prompt)
            results.append({"model": model, "prompt": prompt, "time": r_time})

    print("\n--- Analysis Summary ---")
    print(f"{'Model':<30} | {'Prompt':<50} | {'Response Time (s)':<20}")
    print("-" * 100)
    for result in results:
        prompt_short = (
            result["prompt"][:47] + "..."
            if len(result["prompt"]) > 50
            else result["prompt"]
        )
        print(f"{result['model']:<30} | {prompt_short:<50} | {result['time']:<20.2f}")
    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
