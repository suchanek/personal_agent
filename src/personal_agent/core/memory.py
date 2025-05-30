"""Memory and vector store operations."""

import logging
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

logger = logging.getLogger(__name__)

# Global variables for vector store and client
vector_store: Optional[WeaviateVectorStore] = None
weaviate_client: Optional[WeaviateClient] = None


def setup_weaviate() -> bool:
    """Setup Weaviate client and vector store. Returns True if successful."""
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

    # Initialize Weaviate client
    try:
        weaviate_client = WeaviateClient(connection_params, skip_init_checks=True)
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
                vectorizer_config=wvc.Configure.Vectorizer.none(),
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
