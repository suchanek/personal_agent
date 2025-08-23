import re
import time
import os
from dotenv import load_dotenv

import ollama
from langfuse import Langfuse, observe

# Load environment variables
load_dotenv()

# Debug: Print environment variables to validate they're loaded
print("=== LANGFUSE ENVIRONMENT VARIABLES DEBUG ===")
print(f"LANGFUSE_HOST: {os.getenv('LANGFUSE_HOST', 'NOT SET')}")
print(f"LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY', 'NOT SET')}")
print(f"LANGFUSE_SECRET_KEY: {'SET' if os.getenv('LANGFUSE_SECRET_KEY') else 'NOT SET'}")
print("=" * 50)

# Initialize Langfuse client using environment variables
langfuse = Langfuse()  # Will automatically use LANGFUSE_* environment variables

# Debug: Print Langfuse client configuration
print("=== LANGFUSE CLIENT CONFIGURATION DEBUG ===")
print(f"Langfuse client host: {getattr(langfuse, 'base_url', 'UNKNOWN')}")
print(f"Langfuse client public key: {getattr(langfuse, 'public_key', 'UNKNOWN')}")
print("=" * 50)

# Define constants
MODEL = "llama3.1:8b"


@observe(name="Model Interaction", as_type="generation")
def call_ollama(messages, model):
    """Call Ollama with tracing"""
    response = ollama.chat(model=model, messages=messages)
    return response["message"]["content"]


@observe(name="ISCO Code Prediction")
def predict_isco_code(title):
    """Function to predict ISCO code with tracing and printing"""
    print(f"Processing title: {title}")

    # Prepare the prompt
    prompt = f"Given a dataset with ISCO titles and codes, predict the ISCO code for the title: '{title}'. Provide the code and a brief explanation."
    messages = [{"role": "user", "content": prompt}]

    prediction_inputs = {"title": title, "prompt": prompt}
    print(f"Prediction Inputs to Log: {prediction_inputs}")

    try:
        # Call Ollama with tracing
        result = call_ollama(messages, MODEL)
        
        # Check for ISCO code pattern
        isco_code_match = re.search(r"\b\d{4}\b", result)
        score_value = 1.0 if isco_code_match else 0.5
        print(f"ISCO Code Pattern Found: {bool(isco_code_match)}, Confidence: {score_value}")
        
        return result
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"Error occurred: {error_msg}")
        raise


# Test it
if __name__ == "__main__":
    job_title = "Software Developer"
    try:
        print("Calling Ollama with Langfuse tracing...")
        prediction = predict_isco_code(job_title)
        print(f"Predicted ISCO Code for '{job_title}':\n{prediction}")
        print("Check Langfuse at http://localhost:3000 for traces and scores.")
        
        # Debug: Test Langfuse connection before flushing
        print("\n🔍 CREDENTIAL DIAGNOSIS:")
        print("The 401 error indicates your API keys don't match the Langfuse server.")
        print("To fix this:")
        print("1. Go to http://localhost:3000 → Settings → API Keys")
        print("2. Generate new API keys")
        print("3. Update your .env file with the new keys")
        print("4. Restart this script")
        print("\nCurrent keys in .env:")
        print(f"  LANGFUSE_PUBLIC_KEY: {os.getenv('LANGFUSE_PUBLIC_KEY', 'NOT SET')}")
        print(f"  LANGFUSE_SECRET_KEY: {'SET' if os.getenv('LANGFUSE_SECRET_KEY') else 'NOT SET'}")
        print("=" * 50)
        
        # Flush to ensure data is sent
        print("Attempting to flush traces to Langfuse...")
        langfuse.flush()
        print("Trace flushed to Langfuse server.")
        
        time.sleep(2)  # Wait for flush to complete
    except Exception as e:
        print(f"Error: {e}")
