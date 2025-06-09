#!/usr/bin/env python3
"""Debug script to examine Weaviate database contents."""

import json
import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import weaviate

from personal_agent.config import WEAVIATE_URL


def examine_weaviate():
    """Examine what's stored in Weaviate database."""
    try:
        # Connect to Weaviate (v4 syntax)
        client = weaviate.connect_to_local(host="localhost", port=8080)

        print("=== Weaviate Database Examination ===")
        print(f"Connected to: localhost:8080")

        # Check if Weaviate is ready
        if not client.is_ready():
            print("❌ Weaviate is not ready!")
            client.close()
            return

        print("✅ Weaviate is ready")

        # Get schema
        schema = client.collections.list_all()
        print(f"\n=== Collections ===")
        if schema:
            for collection_name in schema:
                print(f"Collection: {collection_name}")
                try:
                    collection = client.collections.get(collection_name)
                    # Get a few objects from this collection
                    response = collection.query.fetch_objects(limit=5)
                    print(f"  Objects count: {len(response.objects)}")

                    for i, obj in enumerate(response.objects):
                        print(f"  Object {i+1}:")
                        print(f"    UUID: {obj.uuid}")
                        for prop_name, prop_value in obj.properties.items():
                            # Truncate long values
                            if isinstance(prop_value, str) and len(prop_value) > 100:
                                prop_value = prop_value[:100] + "..."
                            print(f"    {prop_name}: {prop_value}")
                        print()
                except Exception as e:
                    print(f"  Error accessing collection {collection_name}: {e}")
                print()
        else:
            print("No collections found")

        # Try to search for user facts
        print(f"\n=== Searching for User Facts ===")
        for collection_name in schema:
            try:
                collection = client.collections.get(collection_name)
                # Search for facts about the user
                response = collection.query.near_text(
                    query="user facts personal information about user", limit=10
                )

                if response.objects:
                    print(f"\n--- Found in {collection_name} ---")
                    for obj in response.objects:
                        print(f"UUID: {obj.uuid}")
                        for prop_name, prop_value in obj.properties.items():
                            print(f"  {prop_name}: {prop_value}")
                        if hasattr(obj, "metadata") and obj.metadata.distance:
                            print(f"  Distance: {obj.metadata.distance}")
                        print()

            except Exception as e:
                print(f"Error searching in {collection_name}: {e}")

        client.close()

    except Exception as e:
        print(f"❌ Error connecting to Weaviate: {e}")
        print(f"Make sure Weaviate is running on localhost:8080")


if __name__ == "__main__":
    examine_weaviate()
