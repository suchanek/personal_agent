# -*- coding: utf-8 -*-
# pylint: disable=W0718,W0603

"""Memory and vector store operations."""

import logging
import os
import time
from typing import Optional

import requests
import weaviate.classes.config as wvc
from langchain_ollama import OllamaEmbeddings
from langchain_weaviate import WeaviateVectorStore
from urllib3.util import parse_url
from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams

from ..config import OLLAMA_URL, USE_WEAVIATE, WEAVIATE_URL
from ..utils import setup_logging

# Setup logging
logger = setup_logging(name=__name__, level=logging.INFO)

# Global variables for vector store and client
vector_store: Optional[WeaviateVectorStore] = None
weaviate_client: Optional[WeaviateClient] = None


def setup_weaviate() -> bool:
    """
    Setup Weaviate client and vector store. Returns True if successful.

    :return: True if Weaviate setup succeeded, False otherwise
    """
    global vector_store, weaviate_client

    if not USE_WEAVIATE:
        logger.info("Weaviate disabled by configuration")
        return False

    try:
        # Verify Weaviate is running with retries
        for attempt in range(5):
            logger.info(
                "Attempting to connect to Weaviate at %s (attempt %d/5)",
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
            # If we've exhausted all attempts
            logger.error(
                "Cannot connect to Weaviate at %s after 5 attempts",
                WEAVIATE_URL,
            )
            return False

    except requests.exceptions.RequestException as e:
        logger.error("Attempt %d/5: Error connecting to Weaviate: %s", attempt + 1, e)
        if attempt == 4:
            logger.error(
                "Cannot connect to Weaviate at %s, proceeding without Weaviate",
                WEAVIATE_URL,
            )
            return False
        time.sleep(10)

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

    # Initialize Weaviate client !!!
    try:
        weaviate_client = WeaviateClient(
            connection_params,
            skip_init_checks=True,
            additional_headers={
                "X-OpenAI-Api-Key": os.environ[
                    "OPENAI_API_KEY"
                ]  # Add inference API keys as needed
            },
        )
        weaviate_client.connect()  # Explicitly connect
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
    except ImportError as e:
        logger.error("Import error initializing Weaviate client or collection: %s", e)
        return False
    except AttributeError as e:
        logger.error(
            "Attribute error initializing Weaviate client or collection: %s", e
        )
        return False
    except Exception as e:
        logger.error(
            "Unexpected error initializing Weaviate client or collection: %s", e
        )
        return False

    # Initialize Weaviate vector store
    try:
        vector_store = WeaviateVectorStore(
            client=weaviate_client,
            index_name=collection_name,
            text_key="text",
            embedding=OllamaEmbeddings(model="nomic-embed-text", base_url=OLLAMA_URL),
            attributes=["timestamp", "topic"],
        )
        logger.info("Successfully initialized Weaviate vector store")
        return True
    except Exception as e:
        logger.error("Error initializing vector store: %s", e)
        return False


def is_weaviate_connected() -> bool:
    """
    Check if Weaviate is available and connected.

    :return: True if Weaviate is connected and ready, False otherwise
    """
    if not USE_WEAVIATE:
        return False

    if weaviate_client is None:
        return False

    try:
        # Check if Weaviate is ready via HTTP endpoint
        response = requests.get(f"{WEAVIATE_URL}/v1/.well-known/ready", timeout=5)
        if response.status_code != 200:
            return False

        # Additionally check database health and attempt recovery if needed
        return reset_weaviate_if_corrupted()

    except (requests.exceptions.RequestException, Exception) as e:
        logger.debug("Weaviate connection check failed: %s", e)
        return False


def reset_weaviate_if_corrupted() -> bool:
    """
    Check for Weaviate database corruption and attempt recovery.

    :return: True if reset was successful or not needed, False if reset failed
    """
    global vector_store, weaviate_client

    if not USE_WEAVIATE or weaviate_client is None:
        return False

    try:
        # Try a simple operation to test database health
        collection = weaviate_client.collections.get("UserKnowledgeBase")
        # Attempt to get collection info
        collection.config.get()
        return True  # Database is healthy

    except Exception as e:
        error_msg = str(e).lower()

        # Check for common corruption indicators
        corruption_indicators = [
            "no such file or directory",
            "wal",
            "segment-",
            "commit log",
            "failed to send all objects",
            "weaviateinsertmanyallfailederror",
        ]

        if any(indicator in error_msg for indicator in corruption_indicators):
            logger.warning("Database corruption detected: %s", e)
            logger.info("Attempting to reconnect to Weaviate...")

            # Close existing connection
            try:
                if weaviate_client:
                    weaviate_client.close()
            except Exception:
                pass

            # Reset global variables
            weaviate_client = None
            vector_store = None

            # Wait a moment for cleanup
            time.sleep(2)

            # Attempt to reconnect
            return setup_weaviate()

        # Not a corruption error, re-raise
        logger.error("Non-corruption Weaviate error: %s", e)
        return False


def is_agno_storage_connected() -> bool:
    """
    Check if Agno storage is available and connected.

    :return: True if Agno storage directories exist and are accessible, False otherwise
    """
    from ..config import STORAGE_BACKEND, AGNO_STORAGE_DIR, AGNO_KNOWLEDGE_DIR
    
    if STORAGE_BACKEND != "agno":
        return False
    
    try:
        import os
        from pathlib import Path
        
        # Check if storage directories exist and are accessible
        storage_path = Path(AGNO_STORAGE_DIR)
        knowledge_path = Path(AGNO_KNOWLEDGE_DIR)
        
        # Create directories if they don't exist (this is normal for Agno)
        storage_path.mkdir(parents=True, exist_ok=True)
        knowledge_path.mkdir(parents=True, exist_ok=True)
        
        # Test write access to storage directory
        test_file = storage_path / ".connection_test"
        try:
            test_file.write_text("test")
            test_file.unlink()  # Remove test file
        except (OSError, PermissionError):
            logger.debug("Cannot write to Agno storage directory: %s", storage_path)
            return False
        
        # Check if we can import required Agno modules
        try:
            from agno.storage.sqlite import SqliteStorage
            from agno.memory.v2.db.sqlite import SqliteMemoryDb
            return True
        except ImportError as e:
            logger.debug("Agno modules not available: %s", e)
            return False
            
    except Exception as e:
        logger.debug("Agno storage connection check failed: %s", e)
        return False


def is_memory_connected() -> bool:
    """
    Check if the configured memory backend is connected.
    
    :return: True if the configured memory backend is connected, False otherwise
    """
    from ..config import STORAGE_BACKEND
    
    if STORAGE_BACKEND == "weaviate":
        return is_weaviate_connected()
    elif STORAGE_BACKEND == "agno":
        return is_agno_storage_connected()
    else:
        logger.warning("Unknown storage backend: %s", STORAGE_BACKEND)
        return False
