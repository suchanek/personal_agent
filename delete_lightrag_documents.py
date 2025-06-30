#!/usr/bin/env python3
"""
LightRAG Document Deletion Script

This script connects to a LightRAG server and deletes failed documents
that are causing parsing issues.
"""

import requests
import json
import sys
from typing import List, Dict, Any

class LightRAGDocumentManager:
    def __init__(self, base_url: str = "http://localhost:9621"):
        self.base_url = base_url.rstrip('/')
        
    def get_documents(self) -> Dict[str, Any]:
        """Fetch all documents from the LightRAG server"""
        try:
            response = requests.get(f"{self.base_url}/documents")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching documents: {e}")
            return {}
    
    def get_failed_documents(self) -> List[Dict[str, Any]]:
        """Get only the documents with 'Failed' status"""
        data = self.get_documents()
        if isinstance(data, dict) and 'statuses' in data:
            return data['statuses'].get('failed', [])
        return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a specific document by ID"""
        try:
            # Use the correct endpoint for individual document deletion
            response = requests.post(f"{self.base_url}/documents/delete_document", 
                                   json={"doc_id": doc_id})
            
            if response.status_code in [200, 204]:
                print(f"✅ Successfully deleted document: {doc_id}")
                return True
            elif response.status_code == 404:
                print(f"❌ Document {doc_id} not found")
                return False
            elif response.status_code == 405:
                print(f"❌ Method not allowed - check if the endpoint supports POST")
                return False
            else:
                print(f"❌ Error deleting document {doc_id}: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error deleting document {doc_id}: {e}")
            return False
    
    def delete_failed_documents(self, confirm: bool = True) -> int:
        """Delete all failed documents"""
        failed_docs = self.get_failed_documents()
        
        if not failed_docs:
            print("No failed documents found.")
            return 0
        
        print(f"Found {len(failed_docs)} failed documents:")
        for doc in failed_docs:
            doc_id = doc.get('id', 'Unknown ID')
            summary = doc.get('summary', 'No summary')[:100] + "..." if len(doc.get('summary', '')) > 100 else doc.get('summary', 'No summary')
            length = doc.get('length', 'Unknown')
            print(f"  - ID: {doc_id}")
            print(f"    Summary: {summary}")
            print(f"    Length: {length}")
            print()
        
        if confirm:
            response = input(f"Do you want to delete these {len(failed_docs)} failed documents? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("Deletion cancelled.")
                return 0
        
        deleted_count = 0
        for doc in failed_docs:
            doc_id = doc.get('id')
            if doc_id and self.delete_document(doc_id):
                deleted_count += 1
        
        print(f"\n🎉 Successfully deleted {deleted_count} out of {len(failed_docs)} failed documents.")
        return deleted_count
    
    def delete_specific_documents(self, doc_ids: List[str], confirm: bool = True) -> int:
        """Delete specific documents by their IDs"""
        if not doc_ids:
            print("No document IDs provided.")
            return 0
        
        print(f"Preparing to delete {len(doc_ids)} specific documents:")
        for doc_id in doc_ids:
            print(f"  - {doc_id}")
        
        if confirm:
            response = input(f"Do you want to delete these {len(doc_ids)} documents? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("Deletion cancelled.")
                return 0
        
        deleted_count = 0
        for doc_id in doc_ids:
            if self.delete_document(doc_id):
                deleted_count += 1
        
        print(f"\n🎉 Successfully deleted {deleted_count} out of {len(doc_ids)} documents.")
        return deleted_count
    
    def list_all_documents(self):
        """List all documents with their status"""
        data = self.get_documents()
        if not isinstance(data, dict) or 'statuses' not in data:
            print("No documents found or invalid response format.")
            return
        
        statuses = data['statuses']
        all_docs = []
        status_counts = {}
        
        # Collect all documents from different status categories
        for status_name, docs_list in statuses.items():
            if isinstance(docs_list, list):
                for doc in docs_list:
                    doc['status'] = status_name  # Ensure status is set
                    all_docs.append(doc)
                status_counts[status_name] = len(docs_list)
        
        if not all_docs:
            print("No documents found.")
            return
        
        print(f"Found {len(all_docs)} documents:")
        print("-" * 80)
        
        for doc in all_docs:
            doc_id = doc.get('id', 'Unknown ID')
            status = doc.get('status', 'Unknown')
            summary = doc.get('content_summary', 'No summary')[:50] + "..." if len(doc.get('content_summary', '')) > 50 else doc.get('content_summary', 'No summary')
            length = doc.get('content_length', 'Unknown')
            chunks = doc.get('chunks_count', 'Unknown')
            file_path = doc.get('file_path', 'Unknown')
            
            status_emoji = "✅" if status.lower() == "processed" else "❌" if status.lower() == "failed" else "⏳"
            
            print(f"{status_emoji} {doc_id}")
            print(f"   Status: {status} | Length: {length} | Chunks: {chunks}")
            print(f"   File: {file_path}")
            print(f"   Summary: {summary}")
            print()
        
        print("-" * 80)
        print("Status Summary:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")


def main():
    """Main function to handle command line arguments and execute operations"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage LightRAG documents")
    parser.add_argument("--url", default="http://localhost:9621", 
                       help="LightRAG server URL (default: http://localhost:9621)")
    parser.add_argument("--list", action="store_true", 
                       help="List all documents")
    parser.add_argument("--delete-failed", action="store_true", 
                       help="Delete all failed documents")
    parser.add_argument("--delete-ids", nargs="+", 
                       help="Delete specific documents by ID")
    parser.add_argument("--no-confirm", action="store_true", 
                       help="Skip confirmation prompts")
    
    args = parser.parse_args()
    
    manager = LightRAGDocumentManager(args.url)
    
    if args.list:
        manager.list_all_documents()
    elif args.delete_failed:
        manager.delete_failed_documents(confirm=not args.no_confirm)
    elif args.delete_ids:
        manager.delete_specific_documents(args.delete_ids, confirm=not args.no_confirm)
    else:
        print("No action specified. Use --help for available options.")
        print("\nQuick examples:")
        print("  python delete_lightrag_documents.py --list")
        print("  python delete_lightrag_documents.py --delete-failed")
        print("  python delete_lightrag_documents.py --delete-ids doc-726db79638518e14b6a257 doc-e46e8b403a2224cb473dd9")


if __name__ == "__main__":
    main()
