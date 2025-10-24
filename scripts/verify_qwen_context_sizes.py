#!/usr/bin/env python3
"""
Script to verify and update Qwen model context sizes using ollama show command.

This script checks all Qwen models in the MODEL_CONTEXT_SIZES dictionary
against their actual context sizes reported by Ollama, and suggests updates
if there are discrepancies.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config.model_contexts import MODEL_CONTEXT_SIZES


def run_ollama_show(model_name: str) -> Optional[Dict]:
    """
    Run 'ollama show' command for a model and return the parsed JSON output.
    
    Args:
        model_name: Name of the model to query
        
    Returns:
        Parsed JSON output or None if command failed
    """
    try:
        result = subprocess.run(
            ["ollama", "show", model_name],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to get info for {model_name}: {result.stderr.strip()}")
            return None
            
        # Parse the output - ollama show returns structured text, not JSON
        # We need to parse the text output
        return parse_ollama_show_output(result.stdout)
        
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout querying {model_name}")
        return None
    except Exception as e:
        print(f"❌ Error querying {model_name}: {e}")
        return None


def parse_ollama_show_output(output: str) -> Dict:
    """
    Parse the text output from 'ollama show' command.
    
    Args:
        output: Raw text output from ollama show
        
    Returns:
        Dictionary with parsed information
    """
    info = {}
    current_section = None
    
    for line in output.split('\n'):
        original_line = line
        line = line.strip()
        if not line:
            continue
            
        # Check for section headers (lines that start at column 2 and don't contain colons)
        if original_line.startswith('  ') and not original_line.startswith('    ') and ':' not in line:
            current_section = line.lower().replace(' ', '_')
            info[current_section] = {}
            continue
            
        # Parse key-value pairs (lines that start at column 4)
        if current_section and original_line.startswith('    '):
            # Split on multiple spaces to separate key from value
            parts = line.split()
            if len(parts) >= 2:
                # Join the first part(s) as key, last part as value
                # Handle cases like "context length" -> "context_length"
                if len(parts) == 2:
                    key = parts[0].lower().replace(' ', '_')
                    value = parts[1]
                else:
                    # Find where the value starts (look for the last contiguous group)
                    # This handles cases like "context length      40960"
                    key_parts = []
                    value_parts = []
                    
                    # Split the original line to preserve spacing
                    stripped = line.strip()
                    # Find the last word (value) by splitting on whitespace
                    words = stripped.split()
                    if len(words) >= 2:
                        value = words[-1]
                        key = ' '.join(words[:-1]).lower().replace(' ', '_')
                    else:
                        key = stripped.lower().replace(' ', '_')
                        value = ''
                
                if key and value:
                    info[current_section][key] = value
            elif line.strip():
                # Single word entries (like "completion", "tools", "thinking")
                key = line.strip().lower().replace(' ', '_')
                info[current_section][key] = True
    
    return info


def extract_context_length(model_info: Dict) -> Optional[int]:
    """
    Extract context length from parsed ollama show output.
    
    Args:
        model_info: Parsed model information
        
    Returns:
        Context length in tokens or None if not found
    """
    # Check in model section
    if 'model' in model_info:
        model_section = model_info['model']
        if 'context_length' in model_section:
            try:
                context_str = model_section['context_length']
                # Remove any non-numeric characters and convert to int
                context_num = ''.join(filter(str.isdigit, context_str))
                if context_num:
                    return int(context_num)
            except ValueError:
                pass
    
    # Check in parameters section
    if 'parameters' in model_info:
        params_section = model_info['parameters']
        for key, value in params_section.items():
            if 'ctx' in key.lower() or 'context' in key.lower():
                try:
                    # Remove any non-numeric characters and convert to int
                    context_num = ''.join(filter(str.isdigit, str(value)))
                    if context_num:
                        return int(context_num)
                except ValueError:
                    pass
    
    return None


def get_qwen_models() -> Dict[str, int]:
    """
    Get all Qwen models from the MODEL_CONTEXT_SIZES dictionary.
    
    Returns:
        Dictionary of Qwen model names and their configured context sizes
    """
    qwen_models = {}
    for model_name, context_size in MODEL_CONTEXT_SIZES.items():
        if 'qwen' in model_name.lower():
            qwen_models[model_name] = context_size
    return qwen_models


def check_model_availability() -> list:
    """
    Get list of available models from ollama.
    
    Returns:
        List of available model names
    """
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to list models: {result.stderr.strip()}")
            return []
            
        # Parse the output to get model names
        lines = result.stdout.strip().split('\n')[1:]  # Skip header
        models = []
        for line in lines:
            if line.strip():
                # Model name is the first column
                model_name = line.split()[0]
                models.append(model_name)
        
        return models
        
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        return []


def normalize_model_name_for_comparison(model_name: str) -> str:
    """
    Normalize model name for comparison with available models.
    
    Args:
        model_name: Model name to normalize
        
    Returns:
        Normalized model name
    """
    # Handle case differences (e.g., qwen3:1.7B vs qwen3:1.7b)
    normalized = model_name.lower()
    
    # Handle variations like qwen3:1.7b vs qwen3:1.7B
    if normalized.endswith('b') and not normalized.endswith('gb'):
        # Try both lowercase and uppercase B
        return normalized
    
    return normalized


def find_matching_available_model(config_model: str, available_models: list) -> Optional[str]:
    """
    Find a matching available model for a configured model name.
    
    Args:
        config_model: Model name from configuration
        available_models: List of available model names
        
    Returns:
        Matching available model name or None
    """
    # Direct match first
    if config_model in available_models:
        return config_model
    
    # Normalize and try case-insensitive matching
    config_normalized = normalize_model_name_for_comparison(config_model)
    
    for available in available_models:
        available_normalized = normalize_model_name_for_comparison(available)
        if config_normalized == available_normalized:
            return available
        
        # Handle B vs b differences (e.g., qwen3:1.7B vs qwen3:1.7b)
        if config_normalized.replace('b', 'B') == available_normalized.replace('b', 'B'):
            return available
    
    return None


def main():
    """Main function to verify Qwen model context sizes."""
    print("🔍 Verifying Qwen model context sizes...")
    print("=" * 60)
    
    # Get available models
    print("📋 Checking available models...")
    available_models = check_model_availability()
    if not available_models:
        print("❌ No models found or ollama not available")
        return
    
    print(f"✅ Found {len(available_models)} available models")
    
    # Get Qwen models from our configuration
    qwen_models = get_qwen_models()
    print(f"📊 Found {len(qwen_models)} Qwen models in configuration")
    
    # Check each Qwen model
    discrepancies = []
    verified_models = []
    unavailable_models = []
    
    for model_name, configured_context in qwen_models.items():
        print(f"\n🔍 Checking {model_name}...")
        
        # Find matching available model
        matching_model = find_matching_available_model(model_name, available_models)
        if not matching_model:
            print(f"⚠️  Model not available locally")
            unavailable_models.append(model_name)
            continue
        
        if matching_model != model_name:
            print(f"📝 Found as: {matching_model}")
        
        # Get actual context size from ollama
        model_info = run_ollama_show(matching_model)
        if not model_info:
            continue
            
        actual_context = extract_context_length(model_info)
        
        if actual_context is None:
            print(f"⚠️  Could not determine context length from ollama output")
            print(f"🔍 Debug: Model info structure: {model_info}")
            continue
            
        # Compare with configured value
        if actual_context == configured_context:
            print(f"✅ Context size matches: {actual_context:,} tokens")
            verified_models.append((model_name, actual_context))
        else:
            print(f"❌ Context size mismatch!")
            print(f"   Configured: {configured_context:,} tokens")
            print(f"   Actual:     {actual_context:,} tokens")
            discrepancies.append((model_name, configured_context, actual_context))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    if verified_models:
        print(f"✅ Verified models ({len(verified_models)}):")
        for model_name, context_size in verified_models:
            print(f"   {model_name}: {context_size:,} tokens")
    
    if unavailable_models:
        print(f"\n⚠️  Unavailable models ({len(unavailable_models)}):")
        for model_name in unavailable_models:
            print(f"   {model_name}")
    
    if discrepancies:
        print(f"\n❌ Models with context size discrepancies ({len(discrepancies)}):")
        for model_name, configured, actual in discrepancies:
            print(f"   {model_name}:")
            print(f"     Configured: {configured:,} tokens")
            print(f"     Actual:     {actual:,} tokens")
        
        print("\n🔧 Suggested updates for model_contexts.py:")
        for model_name, configured, actual in discrepancies:
            print(f'    "{model_name}": {actual},  # Updated from {configured}')
    
    if not discrepancies and verified_models:
        print("\n🎉 All available Qwen models have correct context sizes!")
    
    print(f"\nTotal models checked: {len(verified_models) + len(discrepancies)}")
    print(f"Models with correct context: {len(verified_models)}")
    print(f"Models with incorrect context: {len(discrepancies)}")
    print(f"Unavailable models: {len(unavailable_models)}")


if __name__ == "__main__":
    main()