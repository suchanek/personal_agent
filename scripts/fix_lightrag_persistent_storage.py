#!/usr/bin/env python3
"""
LightRAG Persistent Storage Fix Script

This script helps permanently delete documents from LightRAG by removing them
from the persistent storage files, not just the in-memory API.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List

class LightRAGStorageFixer:
    def __init__(self, storage_path: str = "/Users/Shared/personal_agent_data/agno/rag_storage"):
        self.storage_path = storage_path
        self.doc_status_file = os.path.join(storage_path, "kv_store_doc_status.json")
        self.full_docs_file = os.path.join(storage_path, "kv_store_full_docs.json")
        self.text_chunks_file = os.path.join(storage_path, "kv_store_text_chunks.json")
        
    def backup_files(self) -> str:
        """Create backups of all storage files before modification"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"{self.storage_path}_backup_{timestamp}"
        
        print(f"Creating backup at: {backup_dir}")
        shutil.copytree(self.storage_path, backup_dir)
        return backup_dir
    
    def load_json_file(self, filepath: str) -> Dict[str, Any]:
        """Safely load a JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}
    
    def save_json_file(self, filepath: str, data: Dict[str, Any]) -> bool:
        """Safely save a JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving {filepath}: {e}")
            return False
    
    def list_documents_by_status(self, status: str = None) -> List[Dict[str, Any]]:
        """List documents, optionally filtered by status"""
        doc_status_data = self.load_json_file(self.doc_status_file)
        
        documents = []
        for doc_id, doc_info in doc_status_data.items():
            if status is None or doc_info.get('status') == status:
                doc_info['id'] = doc_id
                documents.append(doc_info)
        
        return documents
    
    def find_document_by_filename(self, filename: str) -> List[Dict[str, Any]]:
        """Find documents by filename"""
        doc_status_data = self.load_json_file(self.doc_status_file)
        
        matches = []
        for doc_id, doc_info in doc_status_data.items():
            if doc_info.get('file_path', '').endswith(filename):
                doc_info['id'] = doc_id
                matches.append(doc_info)
        
        return matches
    
    def remove_document_from_storage(self, doc_id: str) -> bool:
        """Permanently remove a document from all storage files"""
        success = True
        
        # Remove from doc status
        doc_status_data = self.load_json_file(self.doc_status_file)
        if doc_id in doc_status_data:
            del doc_status_data[doc_id]
            if not self.save_json_file(self.doc_status_file, doc_status_data):
                success = False
            else:
                print(f"✅ Removed {doc_id} from doc_status")
        else:
            print(f"⚠️  Document {doc_id} not found in doc_status")
        
        # Remove from full docs
        full_docs_data = self.load_json_file(self.full_docs_file)
        if doc_id in full_docs_data:
            del full_docs_data[doc_id]
            if not self.save_json_file(self.full_docs_file, full_docs_data):
                success = False
            else:
                print(f"✅ Removed {doc_id} from full_docs")
        else:
            print(f"⚠️  Document {doc_id} not found in full_docs")
        
        # Remove from text chunks
        text_chunks_data = self.load_json_file(self.text_chunks_file)
        chunks_removed = 0
        chunks_to_remove = []
        
        for chunk_id, chunk_data in text_chunks_data.items():
            if chunk_data.get('full_doc_id') == doc_id:
                chunks_to_remove.append(chunk_id)
        
        for chunk_id in chunks_to_remove:
            del text_chunks_data[chunk_id]
            chunks_removed += 1
        
        if chunks_removed > 0:
            if not self.save_json_file(self.text_chunks_file, text_chunks_data):
                success = False
            else:
                print(f"✅ Removed {chunks_removed} chunks for {doc_id} from text_chunks")
        else:
            print(f"⚠️  No chunks found for document {doc_id}")
        
        return success
    
    def show_processing_documents(self):
        """Show all documents with processing status"""
        processing_docs = self.list_documents_by_status("processing")
        
        if not processing_docs:
            print("No processing documents found.")
            return
        
        print(f"Found {len(processing_docs)} processing documents:")
        print("-" * 80)
        
        for doc in processing_docs:
            doc_id = doc.get('id', 'Unknown ID')
            file_path = doc.get('file_path', 'Unknown')
            content_length = doc.get('content_length', 'Unknown')
            chunks_count = doc.get('chunks_count', 'Unknown')
            created_at = doc.get('created_at', 'Unknown')
            
            print(f"🔄 {doc_id}")
            print(f"   File: {file_path}")
            print(f"   Length: {content_length} | Chunks: {chunks_count}")
            print(f"   Created: {created_at}")
            print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix LightRAG persistent storage")
    parser.add_argument("--storage-path", default="/Users/Shared/personal_agent_data/agno/rag_storage",
                       help="Path to LightRAG storage directory")
    parser.add_argument("--list-processing", action="store_true",
                       help="List all processing documents")
    parser.add_argument("--remove-doc", type=str,
                       help="Remove specific document by ID")
    parser.add_argument("--remove-file", type=str,
                       help="Remove document by filename")
    parser.add_argument("--backup", action="store_true", default=True,
                       help="Create backup before making changes (default: True)")
    parser.add_argument("--no-backup", action="store_true",
                       help="Skip backup creation")
    
    args = parser.parse_args()
    
    fixer = LightRAGStorageFixer(args.storage_path)
    
    # Check if storage path exists
    if not os.path.exists(args.storage_path):
        print(f"❌ Storage path does not exist: {args.storage_path}")
        return
    
    if args.list_processing:
        fixer.show_processing_documents()
        return
    
    # Create backup unless explicitly disabled
    if not args.no_backup and (args.remove_doc or args.remove_file):
        backup_dir = fixer.backup_files()
        print(f"📁 Backup created at: {backup_dir}")
        print()
    
    if args.remove_doc:
        print(f"Removing document: {args.remove_doc}")
        if fixer.remove_document_from_storage(args.remove_doc):
            print(f"✅ Successfully removed document {args.remove_doc}")
        else:
            print(f"❌ Failed to remove document {args.remove_doc}")
    
    if args.remove_file:
        matches = fixer.find_document_by_filename(args.remove_file)
        if not matches:
            print(f"❌ No documents found with filename: {args.remove_file}")
            return
        
        print(f"Found {len(matches)} documents with filename '{args.remove_file}':")
        for i, doc in enumerate(matches):
            print(f"  {i+1}. {doc['id']} - {doc.get('file_path', 'Unknown')}")
        
        if len(matches) == 1:
            doc_id = matches[0]['id']
            print(f"\nRemoving document: {doc_id}")
            if fixer.remove_document_from_storage(doc_id):
                print(f"✅ Successfully removed document {doc_id}")
            else:
                print(f"❌ Failed to remove document {doc_id}")
        else:
            print("\nMultiple matches found. Use --remove-doc with specific document ID.")

if __name__ == "__main__":
    main()
