#!/usr/bin/env python3
"""
Script to extract model parameters from Ollama models using 'ollama show'.

This script will:
1. Get a list of all available Ollama models
2. Extract parameters from each model using 'ollama show'
3. Generate updated MODEL_PARAMETERS dictionary for model_contexts.py
"""

import subprocess
import json
import re
import sys
from typing import Dict, Any, Optional

def run_command(command: str) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def get_ollama_models() -> list[str]:
    """Get list of all available Ollama models."""
    success, output = run_command("ollama list")
    if not success:
        print(f"Failed to get Ollama models: {output}")
        return []
    
    models = []
    lines = output.split('\n')[1:]  # Skip header line
    for line in lines:
        if line.strip():
            # Extract model name (first column)
            parts = line.split()
            if parts:
                model_name = parts[0]
                # Remove :latest suffix if present for cleaner names
                if model_name.endswith(':latest'):
                    model_name = model_name[:-7]
                models.append(model_name)
    
    return models

def extract_parameters_from_modelfile(modelfile_content: str) -> Dict[str, Any]:
    """Extract parameters from Ollama modelfile content."""
    parameters = {}
    
    # Look for PARAMETER lines in the modelfile
    parameter_patterns = {
        'temperature': r'PARAMETER\s+temperature\s+([\d.]+)',
        'top_p': r'PARAMETER\s+top_p\s+([\d.]+)',
        'top_k': r'PARAMETER\s+top_k\s+(\d+)',
        'repetition_penalty': r'PARAMETER\s+(?:repeat_penalty|repetition_penalty)\s+([\d.]+)',
        'num_ctx': r'PARAMETER\s+num_ctx\s+(\d+)',
    }
    
    for param_name, pattern in parameter_patterns.items():
        match = re.search(pattern, modelfile_content, re.IGNORECASE)
        if match:
            value = match.group(1)
            try:
                if param_name in ['top_k', 'num_ctx']:
                    parameters[param_name] = int(value)
                else:
                    parameters[param_name] = float(value)
            except ValueError:
                print(f"Warning: Could not parse {param_name} value: {value}")
    
    return parameters

def get_model_parameters(model_name: str) -> Optional[Dict[str, Any]]:
    """Get parameters for a specific model using 'ollama show'."""
    print(f"Extracting parameters for {model_name}...")
    
    success, output = run_command(f"ollama show {model_name}")
    if not success:
        print(f"  Failed to get info for {model_name}: {output}")
        return None
    
    # Parse the text output from ollama show
    parameters = {}
    
    # Look for the Parameters section
    lines = output.split('\n')
    in_parameters_section = False
    
    for line in lines:
        line = line.strip()
        
        # Check if we're entering the Parameters section
        if line == "Parameters":
            in_parameters_section = True
            continue
        
        # Check if we're leaving the Parameters section (next major section)
        if in_parameters_section and line and not line.startswith(' ') and ':' not in line:
            # This might be the start of a new section like "License"
            if line in ["License", "System", "Template", "Model"]:
                break
        
        # Parse parameter lines
        if in_parameters_section and line:
            # Look for parameter patterns like "temperature       0.6"
            if 'temperature' in line.lower():
                match = re.search(r'temperature\s+([\d.]+)', line, re.IGNORECASE)
                if match:
                    parameters['temperature'] = float(match.group(1))
            
            elif 'top_p' in line.lower():
                match = re.search(r'top_p\s+([\d.]+)', line, re.IGNORECASE)
                if match:
                    parameters['top_p'] = float(match.group(1))
            
            elif 'top_k' in line.lower():
                match = re.search(r'top_k\s+(\d+)', line, re.IGNORECASE)
                if match:
                    parameters['top_k'] = int(match.group(1))
            
            elif 'repeat_penalty' in line.lower() or 'repetition_penalty' in line.lower():
                match = re.search(r'(?:repeat_penalty|repetition_penalty)\s+([\d.]+)', line, re.IGNORECASE)
                if match:
                    parameters['repetition_penalty'] = float(match.group(1))
    
    # Also look for context length in the Model section
    for line in lines:
        if 'context length' in line.lower():
            match = re.search(r'context length\s+(\d+)', line, re.IGNORECASE)
            if match:
                parameters['num_ctx'] = int(match.group(1))
    
    return parameters if parameters else None

def generate_model_parameters_code(model_params: Dict[str, Dict[str, Any]]) -> str:
    """Generate Python code for the MODEL_PARAMETERS dictionary."""
    
    # Group models by parameter signature for cleaner code
    param_groups = {}
    for model, params in model_params.items():
        # Create a signature from the parameters
        signature = tuple(sorted(params.items()))
        if signature not in param_groups:
            param_groups[signature] = []
        param_groups[signature].append(model)
    
    code_lines = []
    code_lines.append("# Model parameter database - extracted from Ollama models")
    code_lines.append("MODEL_PARAMETERS: Dict[str, ModelParameters] = {")
    
    # Process each group
    for signature, models in param_groups.items():
        params_dict = dict(signature)
        
        # Create ModelParameters constructor call
        param_args = []
        if 'temperature' in params_dict:
            param_args.append(f"temperature={params_dict['temperature']}")
        if 'top_p' in params_dict:
            param_args.append(f"top_p={params_dict['top_p']}")
        if 'top_k' in params_dict:
            param_args.append(f"top_k={params_dict['top_k']}")
        if 'repetition_penalty' in params_dict:
            param_args.append(f"repetition_penalty={params_dict['repetition_penalty']}")
        
        constructor = f"ModelParameters({', '.join(param_args)})"
        
        # Add comment for the group
        if len(models) > 1:
            code_lines.append(f"    # Models with {constructor}")
        
        # Add each model in the group
        for model in sorted(models):
            code_lines.append(f'    "{model}": {constructor},')
    
    # Add default fallback
    code_lines.append('    # Default fallback parameters for unknown models')
    code_lines.append('    "default": ModelParameters(temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1),')
    code_lines.append("}")
    
    return '\n'.join(code_lines)

def main():
    print("Extracting Model Parameters from Ollama")
    print("=" * 50)
    
    # Get list of models
    print("Getting list of Ollama models...")
    models = get_ollama_models()
    if not models:
        print("No models found or failed to get model list")
        return
    
    print(f"Found {len(models)} models: {', '.join(models)}")
    print()
    
    # Extract parameters for each model
    model_params = {}
    for model in models:
        params = get_model_parameters(model)
        if params:
            # Filter out num_ctx as that's handled separately
            filtered_params = {k: v for k, v in params.items() if k != 'num_ctx'}
            if filtered_params:
                model_params[model] = filtered_params
                print(f"  ✅ Extracted: {filtered_params}")
            else:
                print(f"  ⚠️  No relevant parameters found")
        else:
            print(f"  ❌ Failed to extract parameters")
        print()
    
    if not model_params:
        print("No parameters extracted from any models")
        return
    
    # Generate the code
    print("Generating MODEL_PARAMETERS code...")
    code = generate_model_parameters_code(model_params)
    
    # Write to file
    output_file = "extracted_model_parameters.py"
    with open(output_file, 'w') as f:
        f.write("# Generated model parameters from Ollama models\n")
        f.write("# Run this script to extract parameters: python extract_model_parameters.py\n\n")
        f.write("from typing import Dict\n")
        f.write("from personal_agent.config.model_contexts import ModelParameters\n\n")
        f.write(code)
        f.write("\n")
    
    print(f"✅ Generated code saved to {output_file}")
    print("\nYou can now copy the MODEL_PARAMETERS dictionary from this file")
    print("and replace the one in src/personal_agent/config/model_contexts.py")
    
    # Also print a summary
    print(f"\nSummary:")
    print(f"- Processed {len(models)} models")
    print(f"- Successfully extracted parameters from {len(model_params)} models")
    print(f"- Parameters found: {set().union(*[set(params.keys()) for params in model_params.values()])}")

if __name__ == "__main__":
    main()
