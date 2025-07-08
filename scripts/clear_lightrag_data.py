import json
import os

def clear_json_file(file_path):
    """Clears the content of a JSON file, making it an empty dictionary."""
    if os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump({}, f)
        print(f"Cleared {file_path}")
    else:
        print(f"File not found: {file_path}")

if __name__ == "__main__":
    data_dir = "/Users/Shared/personal_agent_data/agno/Eric/memory_rag_storage"
    files_to_clear = [
        "kv_store_doc_status.json",
        "kv_store_full_docs.json",
        "kv_store_llm_response_cache.json",
        "kv_store_text_chunks.json"
    ]

    for file_name in files_to_clear:
        clear_json_file(os.path.join(data_dir, file_name))