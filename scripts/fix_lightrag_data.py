import json
import os

def fix_and_clear_lightrag_data():
    """
    Fixes the file_path issue in kv_store_doc_status.json and clears other
    related JSON files to reset the LightRAG server's state.
    """
    data_dir = "/Users/Shared/personal_agent_data/agno/Eric/memory_rag_storage"
    doc_status_file = os.path.join(data_dir, "kv_store_doc_status.json")

    # Fix kv_store_doc_status.json
    if os.path.exists(doc_status_file):
        with open(doc_status_file, 'r+') as f:
            data = json.load(f)
            for doc_id, doc_info in data.items():
                if doc_info.get("file_path") is None:
                    doc_info["file_path"] = "unknown_source"
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
        print(f"Fixed {doc_status_file}")
    else:
        print(f"File not found: {doc_status_file}")

    # Clear other files
    files_to_clear = [
        "kv_store_full_docs.json",
        "kv_store_llm_response_cache.json",
        "kv_store_text_chunks.json"
    ]

    for file_name in files_to_clear:
        file_path = os.path.join(data_dir, file_name)
        if os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f)
            print(f"Cleared {file_path}")
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    fix_and_clear_lightrag_data()