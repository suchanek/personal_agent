#!/usr/bin/env python3
"""Utility script for storing facts in the knowledge base.

This script provides a simple command-line interface for storing facts
in the Weaviate vector database knowledge base.

Usage:
    python -m personal_agent.utils.store_fact "Your fact here"
    python -m personal_agent.utils.store_fact "Your fact here" --topic "science"

Examples:
    python -m personal_agent.utils.store_fact "Python was created by Guido van Rossum"
    python -m personal_agent.utils.store_fact "The speed of light is 299,792,458 m/s" --topic "physics"
"""

import argparse
import os
import sys
from datetime import datetime
from typing import Optional

import requests
import weaviate.classes.config as wvc
from langchain_ollama import OllamaEmbeddings
from langchain_weaviate import WeaviateVectorStore
from urllib3.util import parse_url
from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams
from weaviate.util import generate_uuid5

from ..config import OLLAMA_URL, USE_WEAVIATE, WEAVIATE_URL
from ..utils.logging import setup_logging

# Setup logging
logger = setup_logging(name=__name__)


def connect_to_weaviate() -> (
    tuple[Optional[WeaviateClient], Optional[WeaviateVectorStore]]
):
    """
    Connect to Weaviate and return client and vector store.

    :return: Tuple of (weaviate_client, vector_store) or (None, None) if failed
    """
    if not USE_WEAVIATE:
        logger.info("Weaviate disabled by configuration")
        return None, None

    try:
        # Verify Weaviate is running with retries
        for attempt in range(3):
            logger.info(
                "Attempting to connect to Weaviate at %s (attempt %d/3)",
                WEAVIATE_URL,
                attempt + 1,
            )
            response = requests.get(f"{WEAVIATE_URL}/v1/.well-known/ready", timeout=10)
            if response.status_code == 200:
                logger.info("Weaviate is ready")
                break
            else:
                raise RuntimeError(f"Weaviate returned status {response.status_code}")
        else:
            logger.error(
                "Cannot connect to Weaviate at %s after 3 attempts", WEAVIATE_URL
            )
            return None, None

    except requests.exceptions.RequestException as e:
        logger.error("Error connecting to Weaviate: %s", e)
        return None, None

    # Parse WEAVIATE_URL to create ConnectionParams
    parsed_url = parse_url(WEAVIATE_URL)
    connection_params = ConnectionParams.from_params(
        http_host=parsed_url.host or "localhost",
        http_port=parsed_url.port or 8080,
        http_secure=parsed_url.scheme == "https",
        grpc_host=parsed_url.host or "localhost",
        grpc_port=50051,  # Weaviate's default gRPC port
        grpc_secure=parsed_url.scheme == "https",
    )

    try:
        # Initialize Weaviate client
        weaviate_client = WeaviateClient(
            connection_params,
            skip_init_checks=True,
            additional_headers={
                "X-OpenAI-Api-Key": os.environ.get("OPENAI_API_KEY", "dummy")
            },
        )
        weaviate_client.connect()
        collection_name = "UserKnowledgeBase"

        # Create Weaviate collection if it doesn't exist
        if not weaviate_client.collections.exists(collection_name):
            logger.info("Creating Weaviate collection: %s", collection_name)
            weaviate_client.collections.create(
                name=collection_name,
                properties=[
                    wvc.Property(name="text", data_type=wvc.DataType.TEXT),
                    wvc.Property(name="timestamp", data_type=wvc.DataType.DATE),
                    wvc.Property(name="topic", data_type=wvc.DataType.TEXT),
                ],
                vectorizer_config=wvc.Configure.Vectorizer.text2vec_ollama(
                    api_endpoint="http://host.docker.internal:11434",
                    model="nomic-embed-text",
                ),
            )

        # Initialize Weaviate vector store
        vector_store = WeaviateVectorStore(
            client=weaviate_client,
            index_name=collection_name,
            text_key="text",
            embedding=OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_URL),
            attributes=["timestamp", "topic"],
        )

        logger.info("Successfully initialized Weaviate vector store")
        return weaviate_client, vector_store

    except (ImportError, AttributeError) as e:
        logger.error("Error with Weaviate dependencies: %s", e)
        return None, None
    except (ConnectionError, RuntimeError) as e:
        logger.error("Error connecting to Weaviate: %s", e)
        return None, None


def store_fact_in_knowledge_base(fact: str, topic: str = "fact") -> bool:
    """
    Store a fact in the Weaviate knowledge base.

    :param fact: The fact to store as a string
    :param topic: The topic category for the fact
    :return: True if successful, False otherwise
    """
    if not USE_WEAVIATE:
        logger.error("Weaviate is disabled in configuration")
        print("❌ Error: Weaviate is disabled in configuration")
        return False

    # Connect to Weaviate
    weaviate_client, vector_store = connect_to_weaviate()

    if vector_store is None:
        logger.error("Failed to connect to Weaviate")
        print("❌ Error: Failed to connect to Weaviate. Is it running?")
        print("   Try: docker-compose up -d")
        return False

    try:
        # Format timestamp as RFC3339 (with 'Z' for UTC)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Store the fact in the knowledge base
        vector_store.add_texts(
            texts=[fact],
            metadatas=[{"timestamp": timestamp, "topic": topic}],
            ids=[generate_uuid5(fact)],
        )

        logger.info("Successfully stored fact: %s...", fact[:50])
        print("✅ Fact stored successfully!")
        print(f"   Topic: {topic}")
        print(f"   Timestamp: {timestamp}")
        print(f"   Preview: {fact[:100]}{'...' if len(fact) > 100 else ''}")
        return True

    except (ConnectionError, RuntimeError, ValueError) as e:
        logger.error("Error storing fact: %s", str(e))
        print(f"❌ Error storing fact: {str(e)}")
        return False
    finally:
        # Clean up connection
        try:
            if weaviate_client:
                weaviate_client.close()
        except (ConnectionError, RuntimeError):
            pass


def verify_fact_storage(fact: str, limit: int = 3) -> bool:
    """
    Verify that a fact was stored by searching for it.

    :param fact: The fact to search for
    :param limit: Maximum number of results to return
    :return: True if fact was found, False otherwise
    """
    # Connect to Weaviate
    weaviate_client, vector_store = connect_to_weaviate()

    if vector_store is None:
        return False

    try:
        # Search for the fact using the first few words
        search_query = " ".join(fact.split()[:5])  # Use first 5 words
        results = vector_store.similarity_search(search_query, k=limit)

        if results:
            print(f"\n🔍 Verification search found {len(results)} related items:")
            for i, doc in enumerate(results, 1):
                metadata = doc.metadata if hasattr(doc, "metadata") else {}
                topic = metadata.get("topic", "general")
                content_preview = doc.page_content[:100]
                print(
                    f"   {i}. [{topic}] {content_preview}{'...' if len(doc.page_content) > 100 else ''}"
                )
            return True
        else:
            print("\n⚠️  Verification search found no related items")
            return False

    except (ConnectionError, RuntimeError, ValueError) as e:
        logger.error("Error verifying fact storage: %s", str(e))
        print(f"❌ Error verifying fact storage: {str(e)}")
        return False
    finally:
        # Clean up connection
        try:
            if weaviate_client:
                weaviate_client.close()
        except (ConnectionError, RuntimeError):
            pass


def main():
    """Main entry point for the store_fact utility."""
    parser = argparse.ArgumentParser(
        description="Store facts in the Personal AI Agent knowledge base",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Python was created by Guido van Rossum"
  %(prog)s "The speed of light is 299,792,458 m/s" --topic "physics"
  %(prog)s "My favorite coffee shop is on Main Street" --topic "personal"
        """,
    )

    parser.add_argument("fact", help="The fact to store in the knowledge base")

    parser.add_argument(
        "--topic",
        "-t",
        default="fact",
        help="Topic category for the fact (default: 'fact')",
    )

    parser.add_argument(
        "--verify",
        "-v",
        action="store_true",
        help="Verify that the fact was stored by searching for it",
    )

    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress verbose output"
    )

    args = parser.parse_args()

    if not args.quiet:
        print("📚 Personal AI Agent - Fact Storage Utility")
        print("=" * 50)
        print(f"Storing fact: {args.fact}")
        print(f"Topic: {args.topic}")
        print()

    # Store the fact
    success = store_fact_in_knowledge_base(args.fact, args.topic)

    if not success:
        sys.exit(1)

    # Verify storage if requested
    if args.verify and not args.quiet:
        verify_fact_storage(args.fact)

    if not args.quiet:
        print("\n💡 Tip: You can now query this fact using the AI agent!")


if __name__ == "__main__":
    main()
