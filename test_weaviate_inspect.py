#!/usr/bin/env python3
"""
Test script to inspect Weaviate database directly.

This script examines all collections in the Weaviate database,
shows their schemas, and displays sample data to help understand
what data is stored where.
"""

import os
import sys
from typing import Any, Dict, List

import requests
import weaviate
from urllib3.util import parse_url
from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams

# Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")


def connect_to_weaviate() -> WeaviateClient:
    """Connect to Weaviate database."""
    print(f"Connecting to Weaviate at {WEAVIATE_URL}...")

    # Check if Weaviate is running
    try:
        response = requests.get(f"{WEAVIATE_URL}/v1/.well-known/ready", timeout=5)
        if response.status_code != 200:
            print(f"❌ Weaviate is not ready: status {response.status_code}")
            sys.exit(1)
        print("✅ Weaviate is ready")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to Weaviate: {e}")
        sys.exit(1)

    # Parse URL and create connection
    parsed_url = parse_url(WEAVIATE_URL)
    connection_params = ConnectionParams.from_params(
        http_host=parsed_url.host or "localhost",
        http_port=parsed_url.port or 8080,
        http_secure=parsed_url.scheme == "https",
        grpc_host=parsed_url.host or "localhost",
        grpc_port=50051,
        grpc_secure=parsed_url.scheme == "https",
    )

    # Create client
    client = WeaviateClient(connection_params, skip_init_checks=True)
    client.connect()

    if not client.is_ready():
        print("❌ Weaviate client is not ready")
        sys.exit(1)

    print("✅ Connected to Weaviate successfully")
    return client


def list_all_collections(client: WeaviateClient) -> List[str]:
    """List all collections in Weaviate."""
    print("\n" + "=" * 50)
    print("COLLECTIONS IN WEAVIATE")
    print("=" * 50)

    try:
        collections = client.collections.list_all()
        collection_names = [col.name for col in collections.values()]

        if not collection_names:
            print("No collections found in Weaviate")
            return []

        print(f"Found {len(collection_names)} collections:")
        for i, name in enumerate(collection_names, 1):
            print(f"  {i}. {name}")

        return collection_names
    except Exception as e:
        print(f"❌ Error listing collections: {e}")
        return []


def inspect_collection_schema(
    client: WeaviateClient, collection_name: str
) -> Dict[str, Any]:
    """Inspect the schema of a specific collection."""
    print(f"\n" + "-" * 50)
    print(f"SCHEMA FOR COLLECTION: {collection_name}")
    print("-" * 50)

    try:
        collection = client.collections.get(collection_name)
        config = collection.config.get()

        print(f"Collection: {config.name}")
        print(f"Description: {config.description or 'No description'}")

        if config.properties:
            print("\nProperties:")
            for prop in config.properties:
                print(f"  - {prop.name}: {prop.data_type}")
                if prop.description:
                    print(f"    Description: {prop.description}")
        else:
            print("No properties defined")

        # Get vectorizer config
        if hasattr(config, "vectorizer_config") and config.vectorizer_config:
            print(f"\nVectorizer: {config.vectorizer_config}")
        else:
            print("\nVectorizer: None configured")

        return {
            "name": config.name,
            "properties": (
                [{"name": p.name, "type": p.data_type} for p in config.properties]
                if config.properties
                else []
            ),
            "vectorizer": (
                str(config.vectorizer_config)
                if hasattr(config, "vectorizer_config")
                else None
            ),
        }
    except Exception as e:
        print(f"❌ Error inspecting schema for {collection_name}: {e}")
        return {}


def sample_collection_data(
    client: WeaviateClient, collection_name: str, limit: int = 5
) -> List[Dict]:
    """Sample data from a collection."""
    print(f"\n" + "-" * 30)
    print(f"SAMPLE DATA FROM: {collection_name}")
    print("-" * 30)

    try:
        collection = client.collections.get(collection_name)
        objects = collection.query.fetch_objects(limit=limit)

        if not objects.objects:
            print("No data found in collection")
            return []

        print(f"Found {len(objects.objects)} objects (showing up to {limit}):")

        sample_data = []
        for i, obj in enumerate(objects.objects, 1):
            print(f"\nObject {i}:")
            print(f"  UUID: {obj.uuid}")

            if obj.properties:
                print("  Properties:")
                for key, value in obj.properties.items():
                    # Truncate long text values
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"    {key}: {value}")

                sample_data.append(
                    {"uuid": str(obj.uuid), "properties": obj.properties}
                )
            else:
                print("  No properties")

        return sample_data
    except Exception as e:
        print(f"❌ Error sampling data from {collection_name}: {e}")
        return []


def count_collection_objects(client: WeaviateClient, collection_name: str) -> int:
    """Count total objects in a collection."""
    try:
        collection = client.collections.get(collection_name)
        # Use aggregate to get count
        result = collection.aggregate.over_all(total_count=True)
        count = result.total_count if result.total_count is not None else 0
        print(f"  Total objects: {count}")
        return count
    except Exception as e:
        print(f"  ❌ Error counting objects: {e}")
        return 0


def search_for_specific_content(
    client: WeaviateClient, collection_name: str, search_term: str = "Personal AI"
):
    """Search for specific content in a collection."""
    print(f"\n" + "-" * 30)
    print(f"SEARCHING FOR '{search_term}' IN: {collection_name}")
    print("-" * 30)

    try:
        collection = client.collections.get(collection_name)

        # Try different search methods
        try:
            # Try semantic search first
            results = collection.query.near_text(query=search_term, limit=3)

            if results.objects:
                print(f"Found {len(results.objects)} semantic search results:")
                for i, obj in enumerate(results.objects, 1):
                    print(f"\nResult {i}:")
                    if obj.properties:
                        for key, value in obj.properties.items():
                            if isinstance(value, str) and len(value) > 200:
                                value = value[:200] + "..."
                            print(f"  {key}: {value}")
            else:
                print("No semantic search results found")

        except Exception as search_error:
            print(f"Semantic search failed: {search_error}")

            # Fallback to fetch and filter
            try:
                all_objects = collection.query.fetch_objects(limit=100)
                matching = []

                for obj in all_objects.objects:
                    if obj.properties:
                        for value in obj.properties.values():
                            if (
                                isinstance(value, str)
                                and search_term.lower() in value.lower()
                            ):
                                matching.append(obj)
                                break

                if matching:
                    print(f"Found {len(matching)} objects containing '{search_term}':")
                    for i, obj in enumerate(matching[:3], 1):
                        print(f"\nMatch {i}:")
                        if obj.properties:
                            for key, value in obj.properties.items():
                                if isinstance(value, str) and len(value) > 200:
                                    value = value[:200] + "..."
                                print(f"  {key}: {value}")
                else:
                    print(f"No objects found containing '{search_term}'")

            except Exception as fallback_error:
                print(f"Fallback search also failed: {fallback_error}")

    except Exception as e:
        print(f"❌ Error searching in {collection_name}: {e}")


def main():
    """Main inspection function."""
    print("🔍 WEAVIATE DATABASE INSPECTOR")
    print("=" * 50)

    # Connect to Weaviate
    client = connect_to_weaviate()

    try:
        # List all collections
        collections = list_all_collections(client)

        if not collections:
            print("\n❌ No collections found. Database appears to be empty.")
            return

        # Inspect each collection
        all_data = {}
        for collection_name in collections:
            # Get schema
            schema = inspect_collection_schema(client, collection_name)

            # Count objects
            count = count_collection_objects(client, collection_name)

            # Sample data
            sample_data = sample_collection_data(client, collection_name)

            # Search for specific content
            search_for_specific_content(client, collection_name, "Personal AI")
            search_for_specific_content(client, collection_name, "assistant")

            all_data[collection_name] = {
                "schema": schema,
                "count": count,
                "sample_data": sample_data,
            }

        # Summary
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)

        total_objects = sum(data["count"] for data in all_data.values())
        print(f"Total collections: {len(collections)}")
        print(f"Total objects across all collections: {total_objects}")

        for collection_name, data in all_data.items():
            print(f"\n{collection_name}:")
            print(f"  - Objects: {data['count']}")
            print(f"  - Properties: {len(data['schema'].get('properties', []))}")
            if data["schema"].get("properties"):
                prop_names = [p["name"] for p in data["schema"]["properties"]]
                print(f"  - Property names: {', '.join(prop_names)}")

        # Check for potential conflicts
        print("\n" + "=" * 50)
        print("POTENTIAL ISSUES")
        print("=" * 50)

        if len(collections) > 1:
            print("⚠️  Multiple collections detected:")
            for collection in collections:
                print(f"   - {collection}")
            print("\nThis might indicate duplicate or conflicting data storage.")
            print("Consider consolidating to a single collection if appropriate.")

        # Check for empty collections
        empty_collections = [
            name for name, data in all_data.items() if data["count"] == 0
        ]
        if empty_collections:
            print(f"\n📭 Empty collections found: {', '.join(empty_collections)}")

        print("\n✅ Inspection complete!")

    finally:
        client.close()


if __name__ == "__main__":
    main()
