#!/usr/bin/env python3
"""
Fix LightRAG File Paths - Permanent Solution
This script fixes null file_path entries in the document status file
to prevent Pydantic validation errors.
"""

import json
import os
from pathlib import Path

def fix_document_status_file(file_path: str) -> bool:
    """
    Fix null file_path entries in the document status JSON file.
    
    Args:
        file_path: Path to the kv_store_doc_status.json file
        
    Returns:
        True if fixes were applied, False if no fixes needed
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    try:
        # Read the current file
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Track changes
        changes_made = 0
        
        # Fix null file_path entries
        for doc_id, doc_data in data.items():
            if doc_data.get('file_path') is None:
                doc_data['file_path'] = 'text_memory'
                changes_made += 1
                print(f"Fixed null file_path for document: {doc_id}")
        
        # Write back if changes were made
        if changes_made > 0:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✅ Fixed {changes_made} document(s) with null file_path")
            return True
        else:
            print("✅ No fixes needed - all file_path entries are valid")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing file: {e}")
        return False

def main():
    """Main function to fix LightRAG document status files."""
    print("🔧 LightRAG File Path Fixer")
    print("=" * 50)
    
    # Default path for the document status file
    default_path = "/Users/Shared/personal_agent_data/agno/Eric/memory_rag_storage/kv_store_doc_status.json"
    
    # Check if file exists
    if os.path.exists(default_path):
        print(f"Found document status file: {default_path}")
        fix_document_status_file(default_path)
    else:
        print(f"Document status file not found at: {default_path}")
        print("Please check if the LightRAG server is running and has created documents.")
    
    print("\n" + "=" * 50)
    print("🎉 File path fix completed!")

if __name__ == "__main__":
    main()
