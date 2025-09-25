#!/usr/bin/env python3
"""
Test script to determine the actual embedding dimensions produced by different models
"""
import requests
import json
import sys

def test_embedding_dimensions(model_name, ollama_url="http://localhost:11434"):
    """Test the embedding dimensions for a given model"""
    print(f"Testing embedding dimensions for: {model_name}")
    
    try:
        response = requests.post(f'{ollama_url}/api/embeddings', 
            json={
                'model': model_name,
                'prompt': 'This is a test text to check embedding dimensions.'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'embedding' in data:
                embedding = data['embedding']
                dimensions = len(embedding)
                print(f"✅ {model_name} produces {dimensions} dimensions")
                return dimensions
            else:
                print(f"❌ No embedding found in response for {model_name}")
                print(f"Response: {data}")
                return None
        else:
            print(f"❌ Error {response.status_code} for {model_name}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error for {model_name}: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error for {model_name}: {e}")
        return None

def main():
    print("=== Embedding Dimension Test ===\n")
    
    # Test both models
    models_to_test = [
        'qwen3-embedding:4b',
        'nomic-embed-text:latest'
    ]
    
    results = {}
    
    for model in models_to_test:
        dimensions = test_embedding_dimensions(model)
        results[model] = dimensions
        print()
    
    print("=== Summary ===")
    for model, dims in results.items():
        if dims:
            print(f"{model}: {dims} dimensions")
        else:
            print(f"{model}: Failed to get dimensions")
    
    # Check for mismatches
    valid_dims = [dims for dims in results.values() if dims is not None]
    if len(set(valid_dims)) > 1:
        print(f"\n⚠️  WARNING: Dimension mismatch detected!")
        print(f"Different models produce different dimensions: {set(valid_dims)}")
        print(f"This will cause the LightRAG vector database errors you're seeing.")
    elif len(valid_dims) > 0:
        print(f"\n✅ All models produce consistent {valid_dims[0]} dimensions")

if __name__ == "__main__":
    main()
