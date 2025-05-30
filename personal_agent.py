# pylint: disable=C0301,C0116
# pylint: disable=C0301,C0116,C0115,W0613,E0611,C0413,E0401,W0601,W0621,C0302,E1101,C0103,W0718

"""
Personal Agent - An AI-powered assistant with multi-modal capabilities.

This module implements a personal AI agent that combines multiple technologies to provide
comprehensive assistance with file operations, knowledge management, web search, and
GitHub integration. The agent uses Model Context Protocol (MCP) servers for external
tool access and maintains a persistent knowledge base using Weaviate vector database.

Key Features:
    - File System Operations: Read, write, and list files through MCP filesystem servers
    - Knowledge Base: Store and query interactions using Weaviate vector database
    - GitHub Integration: Search repositories and perform GitHub operations
    - Web Search: Access web content through Brave Search and Puppeteer
    - LLM Integration: Uses Ollama for local language model inference
    - Environment Configuration: Configurable through environment variables

Architecture:
    - MCP Client: Manages connections to multiple MCP servers for tool access
    - Vector Store: Weaviate-based persistent memory for context and learning
    - LLM Backend: Ollama integration for language model capabilities
    - Tool Framework: LangChain-based tool system for structured operations
    - Web Interface: Flask-based web interface for user interactions

Environment Variables:
    - ROOT_DIR: Root directory for MCP filesystem operations (default: /Users/egs)
    - DATA_DIR: Data directory for vector database (default: /Users/egs/data)
    - GITHUB_PERSONAL_ACCESS_TOKEN: GitHub API access token
    - BRAVE_API_KEY: Brave Search API key
    - WEAVIATE_URL: Weaviate database URL (default: http://localhost:8080)
    - OLLAMA_URL: Ollama service URL (default: http://localhost:11434)

MCP Servers:
    - filesystem-home: Access to user's home directory
    - filesystem-data: Access to data directory for vector operations
    - filesystem-root: System-wide file access (use with caution)
    - github: GitHub repository operations and code search
    - brave-search: Web search capabilities
    - puppeteer: Browser automation and web content extraction

Usage:
    The agent can be run as a standalone script or imported as a module.
    Configuration is handled through environment variables loaded from .env file.

    Example:
        $ poetry run personal-agent

Dependencies:
    - python-dotenv: Environment variable management
    - langchain: LLM framework and tool orchestration
    - weaviate-client: Vector database operations
    - ollama: Local LLM inference
    - flask: Web interface
    - rich: Enhanced logging and console output

Author: Eric G. Suchanek, PhD
Version: 0.1.0
License: See LICENSE file
Last Revision: 2025-05-29 23:54:58
"""

import atexit
import gc
import json
import logging
import os
import signal
import subprocess
import sys
import time
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import weaviate.classes.config as wvc
from dotenv import load_dotenv
from flask import Flask, render_template_string, request
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_ollama import ChatOllama, OllamaEmbeddings
from rich.logging import RichHandler
from urllib3.util import parse_url
from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams
from weaviate.util import generate_uuid5

# Load environment variables from .env file
dotenv_loaded = load_dotenv()

# Store loaded environment variables if dotenv succeeded
_env_vars = {}
if dotenv_loaded:
    # Load all variables from .env file into a cache
    import dotenv

    _env_vars = dotenv.dotenv_values()


# Helper function to get environment variables with fallback
def get_env_var(key: str, fallback: str = "") -> str:
    """Get environment variable from dotenv cache first, then os.environ as fallback."""
    if dotenv_loaded and key in _env_vars:
        return _env_vars[key] or fallback
    else:
        # If dotenv failed or key not in .env, try os.getenv as fallback
        return os.getenv(key, fallback)


# Suppress Pydantic deprecation warnings from Ollama
warnings.filterwarnings("ignore", category=DeprecationWarning, module="ollama")
warnings.filterwarnings(
    "ignore", message=".*model_fields.*", category=DeprecationWarning
)
# Suppress resource warnings for unclosed sockets (common with MCP servers)
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*")
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*subprocess.*")

# Setup logging
logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])
logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Reduce httpx logging verbosity to WARNING to reduce noise
logging.getLogger("httpx").setLevel(logging.WARNING)


# Configuration
WEAVIATE_URL = "http://localhost:8080"
OLLAMA_URL = "http://localhost:11434"
USE_WEAVIATE = True  # Set to False to bypass Weaviate for testing
USE_MCP = True  # Set to False to bypass MCP for testing

ROOT_DIR = get_env_var("ROOT_DIR", ".")  # Root directory for MCP filesystem server
DATA_DIR = get_env_var("DATA_DIR", "./data")  # Data directory for vector database

LLM_MODEL = "qwen2.5:7b-instruct"  # Ollama model to use for LLM

# MCP Server configurations
MCP_SERVERS = {
    "filesystem-home": {
        "command": "npx",
        "args": ["--yes", "@modelcontextprotocol/server-filesystem", ROOT_DIR],
        "description": "Access home directory filesystem operations",
    },
    "filesystem-data": {
        "command": "npx",
        "args": ["--yes", "@modelcontextprotocol/server-filesystem", DATA_DIR],
        "description": "Access data directory for vector database",
    },
    "filesystem-root": {
        "command": "npx",
        "args": ["--yes", "@modelcontextprotocol/server-filesystem", "/"],
        "description": "Access root directory filesystem operations",
    },
    "github": {
        "command": "npx",
        "args": ["--yes", "@modelcontextprotocol/server-github"],
        "description": "GitHub repository operations and code search",
        "env": {
            "GITHUB_PERSONAL_ACCESS_TOKEN": get_env_var(
                "GITHUB_PERSONAL_ACCESS_TOKEN", ""
            )
        },
    },
    "brave-search": {
        "command": "npx",
        "args": ["--yes", "@modelcontextprotocol/server-brave-search"],
        "description": "Web search for research and technical information",
        "env": {
            "BRAVE_API_KEY": get_env_var("BRAVE_API_KEY", "")
        },  # Set your API key here
    },
    "puppeteer": {
        "command": "npx",
        "args": ["--yes", "@modelcontextprotocol/server-puppeteer"],
        "description": "Browser automation and web content fetching",
    },
}


class SimpleMCPClient:
    """Simple MCP client based on the working test_mcp.py implementation."""

    def __init__(self, server_configs: Dict[str, Dict[str, Any]]):
        self.server_configs = server_configs
        self.active_servers = {}

    def start_server_sync(self, server_name: str) -> bool:
        """Start an MCP server process synchronously."""
        if server_name not in self.server_configs:
            logger.error("Unknown MCP server: %s", server_name)
            return False

        if server_name in self.active_servers:
            logger.info("MCP server %s already running", server_name)
            return True

        config = self.server_configs[server_name]
        try:
            # Start the MCP server process
            # Set working directory based on the server root path
            cwd = None
            if server_name == "filesystem-home":
                cwd = ROOT_DIR
            elif server_name == "filesystem-data":
                cwd = DATA_DIR

            # Prepare environment variables
            env = os.environ.copy()  # Start with current environment
            if "env" in config:
                env.update(config["env"])  # Add server-specific env vars

            process = subprocess.Popen(
                [config["command"]] + config["args"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                cwd=cwd,
                env=env,  # Pass environment variables
            )

            self.active_servers[server_name] = {"process": process, "config": config}

            # Wait a moment for server to start
            time.sleep(1)

            # Initialize the server
            if self._initialize_server_sync(server_name):
                logger.info("Started MCP server: %s", server_name)
                return True
            else:
                logger.error("Failed to initialize MCP server: %s", server_name)
                return False

        except Exception as e:
            logger.error("Failed to start MCP server %s: %s", server_name, e)
            return False

    def _initialize_server_sync(self, server_name: str) -> bool:
        """Initialize server synchronously."""
        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "personal-agent", "version": "0.1.0"},
                },
            }

            response = self._send_request_sync(server_name, init_request)
            if response and response.get("result"):
                logger.info("Initialized MCP server: %s", server_name)
                return True

        except Exception as e:
            logger.error("Failed to initialize MCP server %s: %s", server_name, e)

        return False

    def _send_request_sync(
        self, server_name: str, request: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Send a JSON-RPC request to an MCP server synchronously."""
        if server_name not in self.active_servers:
            return None

        try:
            process = self.active_servers[server_name]["process"]
            request_json = json.dumps(request) + "\n"

            # Send request
            process.stdin.write(request_json)
            process.stdin.flush()

            # Read response
            response_line = process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())

        except Exception as e:
            logger.error("Error sending request to MCP server %s: %s", server_name, e)

        return None

    def call_tool_sync(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> str:
        """Call a tool on an MCP server synchronously."""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }

            response = self._send_request_sync(server_name, request)
            if response and response.get("result"):
                content = response["result"].get("content", [])
                if content and len(content) > 0:
                    return content[0].get("text", "No response")

        except Exception as e:
            logger.error(
                "Error calling tool %s on server %s: %s", tool_name, server_name, e
            )

        return f"Error calling tool {tool_name}"

    def list_tools_sync(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools on an MCP server synchronously."""
        try:
            request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

            response = self._send_request_sync(server_name, request)
            if response and response.get("result"):
                tools = response["result"].get("tools", [])
                logger.debug(
                    "Available tools on %s: %s",
                    server_name,
                    [tool.get("name") for tool in tools],
                )
                return tools

        except Exception as e:
            logger.error("Error listing tools on server %s: %s", server_name, e)

        return []

    def stop_server_sync(self, server_name: str) -> bool:
        """Stop a specific MCP server."""
        if server_name not in self.active_servers:
            logger.debug("MCP server %s not running", server_name)
            return True

        try:
            server_info = self.active_servers[server_name]
            process = server_info["process"]

            # Terminate the process
            process.terminate()

            # Wait for it to exit gracefully
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't exit gracefully
                process.kill()
                process.wait()

            # Remove from active servers
            del self.active_servers[server_name]
            logger.info("Stopped MCP server: %s", server_name)
            return True

        except Exception as e:
            logger.error("Error stopping MCP server %s: %s", server_name, e)
            return False

    def stop_all_servers(self):
        """Stop all active MCP servers."""
        for server_name, server_info in self.active_servers.items():
            try:
                process = server_info["process"]
                process.terminate()
                process.wait(timeout=5)  # Wait up to 5 seconds
                logger.info("Stopped MCP server: %s", server_name)
            except Exception as e:
                logger.error("Error stopping MCP server %s: %s", server_name, e)

        self.active_servers.clear()


# Initialize MCP client
mcp_client = None
if USE_MCP:
    mcp_client = SimpleMCPClient(MCP_SERVERS)

# Initialize Flask app
app = Flask(__name__)

# Initialize Weaviate client and vector store
vector_store = None
weaviate_client = None
if USE_WEAVIATE:
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
    except requests.exceptions.RequestException as e:
        logger.error("Attempt %d/5: Error connecting to Weaviate: %s", attempt + 1, e)
        if attempt == 4:
            logger.error(
                "Cannot connect to Weaviate at %s, proceeding without Weaviate",
                WEAVIATE_URL,
            )
            USE_WEAVIATE = False
        time.sleep(10)

    if USE_WEAVIATE:
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
            logger.error(
                "Import error initializing Weaviate client or collection: %s", e
            )
            USE_WEAVIATE = False
        except AttributeError as e:
            logger.error(
                "Attribute error initializing Weaviate client or collection: %s", e
            )
            USE_WEAVIATE = False
        except Exception as e:
            logger.error(
                "Unexpected error initializing Weaviate client or collection: %s", e
            )
            USE_WEAVIATE = False

        if USE_WEAVIATE:
            # Initialize Weaviate vector store
            from langchain_weaviate import WeaviateVectorStore

            vector_store = WeaviateVectorStore(
                client=weaviate_client,
                index_name=collection_name,
                text_key="text",
                embedding=OllamaEmbeddings(
                    model="nomic-embed-text", base_url=OLLAMA_URL
                ),
                attributes=["timestamp", "topic"],
            )

# Initialize Ollama LLM
llm = ChatOllama(model=LLM_MODEL, temperature=0.7, base_url=OLLAMA_URL)


# Define tools
@tool
def store_interaction(text: str, topic: str = "general") -> str:
    """Store user interaction in Weaviate."""
    if not USE_WEAVIATE or vector_store is None:
        logger.warning("Weaviate is disabled, interaction not stored.")
        return "Weaviate is disabled, interaction not stored."
    try:
        # Format timestamp as RFC3339 (with 'Z' for UTC)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        vector_store.add_texts(
            texts=[text],
            metadatas=[{"timestamp": timestamp, "topic": topic}],
            ids=[generate_uuid5(text)],
        )
        logger.info("Stored interaction: %s...", text[:50])
        return "Interaction stored successfully."
    except Exception as e:
        logger.error("Error storing interaction: %s", str(e))
        return f"Error storing interaction: {str(e)}"


@tool
def query_knowledge_base(query: str, limit: int = 5) -> List[str]:
    """Query Weaviate for relevant context."""
    if not USE_WEAVIATE or vector_store is None:
        logger.warning("Weaviate is disabled, no context available.")
        return ["Weaviate is disabled, no context available."]
    try:
        results = vector_store.similarity_search(query, k=limit)
        logger.info("Queried knowledge base with: %s...", query[:50])
        return (
            [doc.page_content for doc in results]
            if results
            else ["No relevant context found."]
        )
    except Exception as e:
        logger.error("Error querying knowledge base: %s", str(e))
        return [f"Error querying knowledge base: {str(e)}"]


@tool
def clear_knowledge_base() -> str:
    """Clear all data from the knowledge base."""
    if not USE_WEAVIATE or weaviate_client is None:
        logger.warning("Weaviate is disabled, cannot clear knowledge base.")
        return "Weaviate is disabled, cannot clear knowledge base."
    try:
        collection_name = "UserKnowledgeBase"
        collection = weaviate_client.collections.get(collection_name)

        # Delete all objects in the collection using a different approach
        try:
            # First, try to delete with an empty where clause
            result = collection.data.delete_many(where={})
            deleted_count = result.successful if hasattr(result, "successful") else 0
        except Exception as delete_error:
            logger.warning(
                "delete_many failed, trying alternative approach: %s", delete_error
            )
            # Alternative: Get all objects and delete them individually
            try:
                # Get all object UUIDs
                objects = collection.query.fetch_objects(limit=10000)
                deleted_count = 0
                for obj in objects.objects:
                    try:
                        collection.data.delete_by_id(obj.uuid)
                        deleted_count += 1
                    except Exception as individual_delete_error:
                        logger.warning(
                            "Failed to delete object %s: %s",
                            obj.uuid,
                            individual_delete_error,
                        )
            except Exception as fetch_error:
                logger.error("Failed to fetch objects for deletion: %s", fetch_error)
                # Last resort: recreate the collection
                try:
                    weaviate_client.collections.delete(collection_name)
                    # Recreate the collection
                    weaviate_client.collections.create(
                        name=collection_name,
                        properties=[
                            wvc.Property(name="text", data_type=wvc.DataType.TEXT),
                            wvc.Property(name="timestamp", data_type=wvc.DataType.DATE),
                            wvc.Property(name="topic", data_type=wvc.DataType.TEXT),
                        ],
                        vectorizer_config=wvc.Configure.Vectorizer.none(),
                    )
                    deleted_count = "all (collection recreated)"
                    logger.info("Recreated collection %s", collection_name)
                except Exception as recreate_error:
                    logger.error("Failed to recreate collection: %s", recreate_error)
                    return f"Error clearing knowledge base: {recreate_error}"

        logger.info("Cleared knowledge base. Deleted objects: %s", deleted_count)
        return f"Knowledge base cleared successfully. Deleted {deleted_count} objects."
    except Exception as e:
        logger.error("Error clearing knowledge base: %s", str(e))
        return f"Error clearing knowledge base: {str(e)}"


# MCP-based tools
@tool
def mcp_read_file(file_path: str) -> str:
    """Read file content using MCP filesystem server."""
    # Handle case where file_path might be a JSON string from LangChain
    if isinstance(file_path, str) and file_path.startswith("{"):
        try:
            params = json.loads(file_path)
            file_path = params.get("file_path", file_path)
        except (json.JSONDecodeError, TypeError):
            pass  # Use original value if parsing fails

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot read file."

    try:
        # Determine which server to use based on path
        server_name = "filesystem-home"

        # Start filesystem server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP filesystem server."

        # Convert absolute paths to relative paths for the restricted root
        # The server root is ROOT_DIR, so we need to make paths relative to that
        if file_path == ROOT_DIR:
            file_path = "."  # Root directory (though reading a directory as file will likely fail)
        elif file_path.startswith(ROOT_DIR + "/"):
            file_path = file_path[len(ROOT_DIR) + 1 :]  # Remove ROOT_DIR prefix
        elif file_path.startswith("~/"):
            file_path = file_path[2:]  # Remove "~/" prefix
        elif file_path.startswith("/"):
            # If it's an absolute path outside home, we can't access it
            return f"Error: Path {file_path} is outside the accessible directory ({ROOT_DIR})"

        # Ensure path doesn't start with / for relative paths
        if file_path.startswith("/"):
            file_path = file_path[1:]

        logger.debug(
            "Calling read_file with path: %s on server: %s", file_path, server_name
        )

        # Call read_file tool with correct parameter name
        result = mcp_client.call_tool_sync(
            server_name, "read_file", {"path": file_path}
        )

        # Store the file read operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = (
                f"Read file: {file_path}\nContent preview: {result[:200]}..."
            )
            store_interaction.invoke(
                {"text": interaction_text, "topic": "file_operations"}
            )

        logger.info("Read file via MCP: %s", file_path)
        return result

    except Exception as e:
        logger.error("Error reading file via MCP: %s", str(e))
        return f"Error reading file: {str(e)}"


@tool
def mcp_write_file(file_path: str, content: str = None) -> str:
    """Write content to file using MCP filesystem server."""
    # Log the raw inputs for debugging
    logger.debug(
        "mcp_write_file called with file_path: %r, content: %r", file_path, content
    )
    logger.debug("file_path type: %s, content type: %s", type(file_path), type(content))

    # Handle case where LangChain incorrectly passes the entire JSON as file_path
    if (
        isinstance(file_path, str)
        and file_path.startswith("{")
        and file_path.endswith("}")
    ):
        try:
            # This is the case where LangChain passes the entire JSON string as file_path
            logger.debug("Detected JSON string in file_path, attempting to parse...")
            params = json.loads(file_path)
            logger.debug("Successfully parsed JSON: %s", params)

            # Extract the actual parameters
            if "file_path" in params and "content" in params:
                file_path = params["file_path"]
                content = params["content"]
                logger.debug(
                    "Extracted parameters: file_path=%r, content=%r", file_path, content
                )
            else:
                logger.warning(
                    "JSON missing required keys. Available keys: %s",
                    list(params.keys()),
                )
                return "Error: JSON parameters missing required 'file_path' or 'content' keys"

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from file_path parameter: %s", e)
            return f"Error: Invalid JSON in parameters: {e}"
        except Exception as e:
            logger.error("Unexpected error parsing parameters: %s", e)
            return f"Error parsing parameters: {e}"

    # Validate that we have both required parameters
    if not file_path:
        logger.error("file_path is empty or None")
        return "Error: file_path parameter is required"
    if content is None or content == "":
        logger.error("content is None or empty")
        return "Error: content parameter is required"

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot write file."

    try:
        # Store original path for logging
        original_path = file_path

        # Expand ~ to actual path first
        if file_path.startswith("~/"):
            file_path = os.path.expanduser(file_path)

        # Determine which server to use based on path
        server_name = "filesystem-home"
        if file_path.startswith(DATA_DIR + "/") or file_path.startswith("data/"):
            server_name = "filesystem-data"

        # Start filesystem server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP filesystem server."

        # Convert absolute paths to relative paths for the restricted root
        if server_name == "filesystem-home":
            # The server root is ROOT_DIR
            if file_path == ROOT_DIR:
                return "Error: Cannot write to root directory as a file"
            elif file_path.startswith(ROOT_DIR + "/"):
                file_path = file_path[
                    len(ROOT_DIR + "/") :
                ]  # Remove ROOT_DIR prefix properly
            elif file_path.startswith("/"):
                return f"Error: Path {file_path} is outside the accessible directory ({ROOT_DIR})"
        else:  # filesystem-data
            # The server root is DATA_DIR
            if file_path.startswith(DATA_DIR + "/"):
                file_path = file_path[len(DATA_DIR + "/") :]  # Remove data dir prefix
            elif file_path.startswith("data/"):
                file_path = file_path[5:]  # Remove "data/" prefix

        # Ensure path doesn't start with / for relative paths
        if file_path.startswith("/"):
            file_path = file_path[1:]

        # Create directory structure if it doesn't exist
        dir_path = os.path.dirname(file_path)
        if dir_path:
            full_dir_path = os.path.join(
                ROOT_DIR if server_name == "filesystem-home" else DATA_DIR, dir_path
            )
            if not os.path.exists(full_dir_path):
                try:
                    os.makedirs(full_dir_path, exist_ok=True)
                    logger.info("Created directory structure: %s", full_dir_path)
                except Exception as e:
                    logger.warning(
                        "Could not create directory %s: %s", full_dir_path, e
                    )

        logger.debug(
            "Calling write_file with original path: %s, converted path: %s on server: %s",
            original_path,
            file_path,
            server_name,
        )

        # Call write_file tool with correct parameter name
        result = mcp_client.call_tool_sync(
            server_name, "write_file", {"path": file_path, "content": content}
        )

        # Store the file write operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = f"Wrote file: {original_path}\nContent length: {len(content)} characters"
            store_interaction.invoke(
                {"text": interaction_text, "topic": "file_operations"}
            )

        logger.info("Wrote file via MCP: %s -> %s", original_path, file_path)
        return result

    except Exception as e:
        logger.error("Error writing file via MCP: %s", str(e))
        return f"Error writing file: {str(e)}"


@tool
def mcp_list_directory(directory_path: str) -> str:
    """List directory contents using MCP filesystem server."""
    # Handle case where directory_path might be a JSON string from LangChain
    if isinstance(directory_path, str) and directory_path.startswith("{"):
        try:
            params = json.loads(directory_path)
            directory_path = params.get("directory_path", directory_path)
        except (json.JSONDecodeError, TypeError):
            pass  # Use original value if parsing fails

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot list directory."

    try:
        # Determine which server to use based on path
        server_name = "filesystem-home"
        if directory_path.startswith(DATA_DIR + "/") or directory_path.startswith(
            "data/"
        ):
            server_name = "filesystem-data"

        # Start filesystem server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP filesystem server."

        # Convert absolute paths to relative paths for the restricted root
        original_path = directory_path  # Keep for logging

        if server_name == "filesystem-home":
            # The server root is ROOT_DIR
            if directory_path in [ROOT_DIR, ROOT_DIR, "~", "$HOME"]:
                directory_path = "."  # Root directory
            elif directory_path.startswith(ROOT_DIR + "/"):
                directory_path = directory_path[
                    len(ROOT_DIR + "/") :
                ]  # Remove ROOT_DIR prefix
                if not directory_path:  # If empty after removing prefix
                    directory_path = "."
            elif directory_path.startswith("~/"):
                directory_path = directory_path[2:]  # Remove "~/" prefix
            elif directory_path.startswith("/"):
                return f"Error: Path {directory_path} is outside the accessible directory ({ROOT_DIR})"
        else:  # filesystem-data
            # The server root is DATA_DIR
            if directory_path.startswith(DATA_DIR + "/"):
                directory_path = directory_path[
                    len(DATA_DIR + "/") :
                ]  # Remove data dir prefix
                if not directory_path:  # If empty after removing prefix
                    directory_path = "."
            elif directory_path.startswith("data/"):
                directory_path = directory_path[5:]  # Remove "data/" prefix

        # Ensure path doesn't start with / for relative paths, but handle root directory
        if directory_path.startswith("/"):
            directory_path = directory_path[1:]

        # If path is empty after processing, it means we want the root directory
        if not directory_path:
            directory_path = "."

        logger.debug(
            "Original path: %s, Converted path: %s, Server: %s",
            original_path,
            directory_path,
            server_name,
        )

        # Call list_directory tool with the correct path
        result = mcp_client.call_tool_sync(
            server_name, "list_directory", {"path": directory_path}
        )

        # Store the directory listing operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = (
                f"Listed directory: {original_path}\nResult: {result[:300]}..."
            )
            store_interaction.invoke(
                {"text": interaction_text, "topic": "file_operations"}
            )

        logger.info("Listed directory via MCP: %s -> %s", original_path, directory_path)
        return result

    except Exception as e:
        logger.error("Error listing directory via MCP: %s", str(e))
        return f"Error listing directory: {str(e)}"


@tool
def intelligent_file_search(search_query: str, directory: str = "/") -> str:
    """Search for files and enhance results with memory context."""
    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot search files."

    try:
        # First, search memory for relevant context
        memory_context = []
        if USE_WEAVIATE and vector_store is not None:
            memory_results = query_knowledge_base.invoke(
                {"query": search_query, "limit": 3}
            )
            memory_context = (
                memory_results
                if memory_results != ["No relevant context found."]
                else []
            )

        # Use MCP to list directory contents and search for relevant files
        directory_listing = mcp_list_directory.invoke({"directory_path": directory})

        # Use LLM to analyze which files might be relevant based on the search query
        analysis_prompt = f"""
        Based on the search query: "{search_query}"
        
        Directory listing: {directory_listing}
        
        Memory context: {memory_context}
        
        Which files in this directory are most relevant to the search query? 
        Provide a focused analysis and suggest the top 2-3 most relevant files to examine.
        """

        # Store this search operation in memory
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = f"File search: {search_query} in {directory}\nFound: {directory_listing[:200]}..."
            store_interaction.invoke({"text": interaction_text, "topic": "file_search"})

        logger.info("Performed intelligent file search: %s", search_query)
        return f"Directory contents: {directory_listing}\n\nMemory context: {memory_context}\n\nAnalysis needed: {analysis_prompt}"

    except Exception as e:
        logger.error("Error in intelligent file search: %s", str(e))
        return f"Error searching files: {str(e)}"


def _sanitize_github_output(result: str) -> str:
    """Sanitize GitHub search output to prevent LangChain parsing issues."""
    if not result:
        return result

    try:
        # If it's valid JSON, parse and summarize to prevent large output issues
        if result.strip().startswith("{") and result.strip().endswith("}"):
            import json

            parsed = json.loads(result)

            # Create a more concise summary for LangChain
            if isinstance(parsed, dict) and "items" in parsed:
                total_count = parsed.get("total_count", 0)
                items = parsed.get("items", [])

                summary = {"total_count": total_count, "found_repositories": []}

                # Limit to first 5 results to prevent output size issues
                for item in items[:5]:
                    repo_info = {
                        "name": item.get("full_name", item.get("name", "Unknown")),
                        "description": (
                            item.get("description", "")[:200]
                            if item.get("description")
                            else ""
                        ),
                        "url": item.get("html_url", item.get("url", "")),
                        "stars": item.get("stargazers_count", 0),
                        "language": item.get("language", ""),
                        "updated": item.get("updated_at", ""),
                    }
                    summary["found_repositories"].append(repo_info)

                # Return formatted summary instead of raw JSON
                result_text = f"Found {total_count} repositories:\n\n"
                for repo in summary["found_repositories"]:
                    result_text += f"• {repo['name']}\n"
                    if repo["description"]:
                        result_text += f"  Description: {repo['description']}\n"
                    if repo["stars"]:
                        result_text += f"  Stars: {repo['stars']}\n"
                    if repo["language"]:
                        result_text += f"  Language: {repo['language']}\n"
                    result_text += f"  URL: {repo['url']}\n\n"

                return result_text.strip()

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.debug(f"Could not parse GitHub result as JSON: {e}")

    # Fallback: truncate if too long and remove problematic characters
    if len(result) > 10000:
        result = result[:10000] + "... (truncated)"

    # Remove or escape problematic characters that might confuse LangChain
    result = result.replace("\r\n", "\n").replace("\r", "\n")

    return result


@tool
def mcp_github_search(query: str, repo: str = "") -> str:
    """Search GitHub repositories or specific repo for code, issues, or documentation."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(query, str) and query.startswith("{"):
        try:
            params = json.loads(query)
            query = params.get("query", query)
            repo = params.get("repo", repo)
        except (json.JSONDecodeError, TypeError):
            pass

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot search GitHub."

    try:
        server_name = "github"

        # Start GitHub server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP GitHub server. Make sure GITHUB_PERSONAL_ACCESS_TOKEN is set."

        # Determine which search tool to use based on query characteristics
        tool_name = "search_repositories"  # Default
        params = {}

        # If searching within a specific repo, use search_code for code-specific queries
        if repo and any(
            keyword in query.lower()
            for keyword in [
                "language:",
                "def ",
                "class ",
                "function",
                "import ",
                "const ",
                "var ",
            ]
        ):
            tool_name = "search_code"
            # For search_code, we need to format the query differently
            if repo:
                params = {"q": f"repo:{repo} {query}"}
            else:
                params = {"q": query}
        elif any(
            keyword in query.lower()
            for keyword in ["issue", "bug", "feature", "pull request", "pr"]
        ):
            tool_name = "search_issues"
            if repo:
                params = {"q": f"repo:{repo} {query}"}
            else:
                params = {"q": query}
        else:
            # Default repository search
            if repo:
                params = {"query": f"repo:{repo} {query}"}
            else:
                params = {"query": query}

        logger.debug("Using GitHub tool: %s with params: %s", tool_name, params)

        # Call the appropriate GitHub search tool
        result = mcp_client.call_tool_sync(server_name, tool_name, params)

        # Sanitize result to prevent LangChain parsing issues
        sanitized_result = _sanitize_github_output(result)

        # Store the GitHub search operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = (
                f"GitHub search: {query}"
                + (f" in {repo}" if repo else "")
                + f"\nResults: {sanitized_result[:300]}..."
            )
            store_interaction.invoke(
                {"text": interaction_text, "topic": "github_search"}
            )

        logger.info("GitHub search completed: %s", query)
        return sanitized_result

    except Exception as e:
        logger.error("Error searching GitHub via MCP: %s", str(e))
        return f"Error searching GitHub: {str(e)}"


@tool
def mcp_brave_search(query: str, count: int = 5) -> str:
    """Search the web using Brave Search for research and technical information."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(query, str) and query.startswith("{"):
        try:
            params = json.loads(query)
            query = params.get("query", query)
            count = params.get("count", count)
        except (json.JSONDecodeError, TypeError):
            pass

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot search web."

    try:
        server_name = "brave-search"

        # Start Brave Search server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP Brave Search server. Make sure BRAVE_API_KEY is set."

        # Call Brave search tool
        result = mcp_client.call_tool_sync(
            server_name, "brave_web_search", {"query": query, "count": count}
        )

        # Store the web search operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = (
                f"Web search: {query}\nResults preview: {result[:300]}..."
            )
            store_interaction.invoke({"text": interaction_text, "topic": "web_search"})

        logger.info("Web search completed: %s", query)
        return result

    except Exception as e:
        logger.error("Error searching web via MCP: %s", str(e))
        return f"Error searching web: {str(e)}"


@tool
def mcp_shell_command(command: str, timeout: int = 30) -> str:
    """Execute shell commands safely using subprocess (MCP shell server unavailable)."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(command, str) and command.startswith("{"):
        try:
            params = json.loads(command)
            command = params.get("command", command)
            timeout = params.get("timeout", timeout)
        except (json.JSONDecodeError, TypeError):
            pass

    try:
        # Use subprocess for safe shell command execution
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        output = f"Command: {command}\nReturn code: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"

        # Store the shell command operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = f"Shell command: {command}\nOutput: {output[:300]}..."
            store_interaction.invoke(
                {"text": interaction_text, "topic": "shell_commands"}
            )

        logger.info("Shell command executed: %s", command)
        return output

    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds"
        logger.error("Shell command timeout: %s", command)
        return error_msg
    except Exception as e:
        logger.error("Error executing shell command: %s", str(e))
        return f"Error executing shell command: {str(e)}"


@tool
def mcp_fetch_url(url: str, method: str = "GET") -> str:
    """Fetch content from web URLs using MCP puppeteer server for browser automation."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(url, str) and url.startswith("{"):
        try:
            params = json.loads(url)
            url = params.get("url", url)
            method = params.get("method", method)
        except (json.JSONDecodeError, TypeError):
            pass

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot fetch URLs."

    try:
        server_name = "puppeteer"

        # Start puppeteer server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP puppeteer server."

        # Call puppeteer goto tool to fetch page content
        result = mcp_client.call_tool_sync(server_name, "puppeteer_goto", {"url": url})

        # Store the fetch operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = f"Fetched URL: {url}\nContent preview: {result[:300]}..."
            store_interaction.invoke({"text": interaction_text, "topic": "web_fetch"})

        logger.info("Fetched URL: %s", url)
        return result

    except Exception as e:
        logger.error("Error fetching URL via MCP puppeteer: %s", str(e))
        return f"Error fetching URL: {str(e)}"


@tool
def comprehensive_research(topic: str, max_results: int = 10) -> str:
    """Perform comprehensive research combining memory, web search, GitHub, and file operations."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(topic, str) and topic.startswith("{"):
        try:
            params = json.loads(topic)
            topic = params.get("topic", topic)
            max_results = params.get("max_results", max_results)
        except (json.JSONDecodeError, TypeError):
            pass

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot perform comprehensive research."

    try:
        research_results = []

        # 1. Search memory for existing knowledge
        if USE_WEAVIATE and vector_store is not None:
            memory_results = query_knowledge_base.invoke({"query": topic, "limit": 5})
            if memory_results and memory_results != ["No relevant context found."]:
                research_results.append("=== MEMORY CONTEXT ===")
                research_results.extend(memory_results)

        # 2. Web search for current information
        try:
            web_results = mcp_brave_search.invoke(
                {"query": topic, "count": min(5, max_results)}
            )
            research_results.append("=== WEB SEARCH RESULTS ===")
            research_results.append(web_results)
        except Exception as e:
            research_results.append(f"Web search failed: {str(e)}")

        # 3. GitHub search for code and technical documentation
        try:
            github_results = mcp_github_search.invoke({"query": topic})
            research_results.append("=== GITHUB SEARCH RESULTS ===")
            research_results.append(github_results)
        except Exception as e:
            research_results.append(f"GitHub search failed: {str(e)}")

        # 4. Search local files for relevant information
        try:
            file_search_results = intelligent_file_search.invoke(
                {"search_query": topic, "directory": "."}
            )
            research_results.append("=== LOCAL FILE SEARCH ===")
            research_results.append(file_search_results)
        except Exception as e:
            research_results.append(f"File search failed: {str(e)}")

        # Combine all results
        comprehensive_result = "\n\n".join(research_results)

        # Store the comprehensive research in memory
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = f"Comprehensive research on: {topic}\nSummary: Combined memory, web, GitHub, and file search results"
            store_interaction.invoke({"text": interaction_text, "topic": "research"})

            # Also store the research results for future reference
            store_interaction.invoke(
                {
                    "text": comprehensive_result[:2000],
                    "topic": f"research_{topic.replace(' ', '_')}",
                }
            )

        logger.info("Comprehensive research completed for: %s", topic)
        return comprehensive_result

    except Exception as e:
        logger.error("Error in comprehensive research: %s", str(e))
        return f"Error performing comprehensive research: {str(e)}"


@tool
def create_and_save_file(file_path: str, content: str, create_dirs: bool = True) -> str:
    """Create directories if needed and save file content. This is the preferred tool for creating new files."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(file_path, str) and file_path.startswith("{"):
        try:
            params = json.loads(file_path)
            file_path = params.get("file_path", file_path)
            content = params.get("content", content)
            create_dirs = params.get("create_dirs", create_dirs)
        except (json.JSONDecodeError, TypeError):
            pass

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot create file."

    try:
        # Store original path for logging
        original_path = file_path

        # Expand ~ to actual home directory
        if file_path.startswith("~/"):
            file_path = os.path.expanduser(file_path)

        # Get directory path
        dir_path = os.path.dirname(file_path)

        # Create directories if they don't exist and create_dirs is True
        if create_dirs and dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info("Created directory: %s", dir_path)
            except Exception as e:
                return f"Error creating directory {dir_path}: {str(e)}"

        # Now use the existing mcp_write_file tool
        result = mcp_write_file.invoke({"file_path": original_path, "content": content})

        # Store the file creation operation in memory
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = f"Created file: {original_path}\nContent length: {len(content)} characters\nDirectory created: {create_dirs}"
            store_interaction.invoke(
                {"text": interaction_text, "topic": "file_creation"}
            )

        logger.info("Created and saved file: %s", original_path)
        return f"Successfully created file: {original_path}\n{result}"

    except Exception as e:
        logger.error("Error creating and saving file: %s", str(e))
        return f"Error creating file: {str(e)}"


# Define system prompt for the agent
system_prompt = PromptTemplate(
    template="""You are a helpful personal assistant named "Personal Agent" that learns about the user and provides context-aware responses.

You have access to these tools:
{tools}

Tool names: {tool_names}

IMPORTANT INSTRUCTIONS:
1. ALWAYS respond to the user's current question/request first
2. Use the context from knowledge base to enhance your response when relevant
3. Store important interactions for future reference
4. Be conversational and helpful
5. Use MCP filesystem tools to read, write, and analyze files when requested
6. Combine file operations with memory storage for enhanced context
7. When the user asks to reset knowledge, clear the knowledge base and inform them
8. When the user asks to remember something, store it in the knowledge base
9. When the user asks to clear the context, clear the current context but not the knowledge base
10. Never clear the knowledge base unless explicitly requested by the user
11. For comprehensive research requests, use the 'comprehensive_research' tool which combines multiple sources
12. Always format your final response properly and use 'Final Answer:' to conclude


CAPABILITIES:
- Memory: Store and query interactions using Weaviate vector database
- File Operations: Read, write, list files using MCP filesystem server
- Intelligent Search: Combine file system exploration with memory context
- Learning: Automatically store important file operations for future reference

Current context from knowledge base: {context}

User's current input: {input}

To use a tool, follow this exact format:
Thought: I need to [reason for using tool]
Action: [exact tool name from: {tool_names}]
Action Input: {{"param": "value"}}
Observation: [tool result will appear here]

When you have enough information, provide your final answer:
Thought: I can now answer the user's question
Final Answer: [your complete response to the user's current input]

CRITICAL: Once you write "Final Answer:", you MUST stop immediately. Do NOT add any more thoughts, actions, or text after the Final Answer.

Remember: Answer the user's CURRENT question first, then optionally use context to enhance your response.

{agent_scratchpad}""",
    input_variables=["input", "context", "tool_names", "tools", "agent_scratchpad"],
)

# Initialize ReAct agent
tools = [
    store_interaction,
    query_knowledge_base,
    clear_knowledge_base,
    mcp_read_file,
    mcp_write_file,
    mcp_list_directory,
    intelligent_file_search,
    mcp_github_search,
    mcp_brave_search,
    mcp_shell_command,
    mcp_fetch_url,
    comprehensive_research,
    create_and_save_file,
]
agent = create_react_agent(llm=llm, tools=tools, prompt=system_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=10,  # Increased from 3 to 10 for complex research tasks
)


# Flask routes
@app.route("/", methods=["GET", "POST"])
def index():
    response = None
    context = None
    agent_thoughts = []
    if request.method == "POST":
        user_input = request.form.get("query", "")
        topic = request.form.get("topic", "general")
        if user_input:
            # Add initial thinking state
            agent_thoughts = [
                "🤔 Thinking about your request...",
                "🔍 Searching memory for context...",
            ]

            # Query knowledge base for context
            try:
                # Call the function directly with proper parameters
                context = query_knowledge_base.invoke(
                    {"query": user_input, "limit": 3}
                )  # Reduced from 5 to 3
                context_str = (
                    "\n".join(context) if context else "No relevant context found."
                )

                # Update thoughts after context search
                if (
                    context
                    and context != ["No relevant context found."]
                    and context != ["Weaviate is disabled, no context available."]
                ):
                    agent_thoughts.append("✅ Found relevant context in memory")
                else:
                    agent_thoughts.append("📝 No previous context found")

                agent_thoughts.append("🧠 Starting reasoning process...")

                # Generate response and capture verbose output to extract thoughts
                import io
                from contextlib import redirect_stderr, redirect_stdout

                # Capture verbose output
                stdout_capture = io.StringIO()
                stderr_capture = io.StringIO()

                try:
                    with redirect_stdout(stdout_capture), redirect_stderr(
                        stderr_capture
                    ):
                        result = agent_executor.invoke(
                            {"input": user_input, "context": context_str}
                        )

                    # Parse verbose output for thoughts with better parsing
                    verbose_output = stdout_capture.getvalue()

                    # Extract thoughts from verbose output with enhanced logic
                    lines = verbose_output.split("\n")
                    thought_count = 0
                    action_count = 0
                    last_action = None

                    for line in lines:
                        line = line.strip()
                        if line.startswith("Thought:"):
                            thought = line[8:].strip()  # Remove "Thought:" prefix
                            if thought:
                                thought_count += 1
                                # Filter out common generic thoughts but keep meaningful ones
                                skip_phrases = [
                                    "i can now",
                                    "i need to",
                                    "let me",
                                    "i'll",
                                    "i should",
                                    "i will",
                                ]
                                if not any(
                                    skip in thought.lower() for skip in skip_phrases
                                ):
                                    if thought_count <= 4:  # Limit to prevent spam
                                        agent_thoughts.append(f"💭 {thought}")

                        elif "Action:" in line and not line.startswith("Action Input:"):
                            action = line.split("Action:")[-1].strip()
                            if action and action != last_action:  # Avoid duplicates
                                action_count += 1
                                last_action = action
                                # Make tool names more user-friendly
                                tool_names = {
                                    "query_knowledge_base": "Searching memory database",
                                    "mcp_brave_search": "Searching the web",
                                    "mcp_github_search": "Searching GitHub repositories",
                                    "mcp_read_file": "Reading file content",
                                    "mcp_write_file": "Writing to file",
                                    "mcp_list_directory": "Exploring directory",
                                    "comprehensive_research": "Conducting comprehensive research",
                                    "intelligent_file_search": "Smart file analysis",
                                    "store_interaction": "Saving to memory",
                                    "mcp_shell_command": "Executing system command",
                                    "mcp_fetch_url": "Fetching web content",
                                }
                                friendly_name = tool_names.get(action, action)
                                agent_thoughts.append(f"🔧 {friendly_name}")

                        elif "Observation:" in line and action_count > 0:
                            # Only add completion for actual tool executions
                            if last_action and not any(
                                "completed" in thought
                                for thought in agent_thoughts[-2:]
                            ):
                                agent_thoughts.append("✅ Tool execution completed")

                    # Add processing thoughts if we didn't capture much from verbose output
                    if (
                        len(
                            [
                                t
                                for t in agent_thoughts
                                if not t.startswith(("🤔", "🔍", "✅", "📝"))
                            ]
                        )
                        < 3
                    ):
                        additional_thoughts = [
                            "⚡ Processing with AI reasoning",
                            "🧩 Analyzing problem components",
                            "📊 Synthesizing information",
                        ]
                        for thought in additional_thoughts:
                            if thought not in agent_thoughts:
                                agent_thoughts.append(thought)

                    # Add final processing thought
                    if not any(
                        "final" in thought.lower() for thought in agent_thoughts
                    ):
                        agent_thoughts.append("🎯 Finalizing response")

                except Exception as e:
                    # Fallback if capture fails
                    result = agent_executor.invoke(
                        {"input": user_input, "context": context_str}
                    )
                    agent_thoughts.extend(
                        [
                            "🔄 Processing your request",
                            "🛠️ Using available tools",
                            "⚡ Generating response",
                        ]
                    )

                if isinstance(result, dict):
                    response = result.get("output", "No response generated.")
                else:
                    response = str(result)

                # Remove duplicate final thoughts and add completion
                agent_thoughts = list(
                    dict.fromkeys(agent_thoughts)
                )  # Remove duplicates while preserving order
                if not any(
                    "complete" in thought.lower() or "final" in thought.lower()
                    for thought in agent_thoughts
                ):
                    agent_thoughts.append("✨ Response generated successfully")

                # Store interaction AFTER getting response
                interaction_text = f"User: {user_input}\nAssistant: {response}"
                store_interaction.invoke({"text": interaction_text, "topic": topic})
            except Exception as e:
                logger.error("Error processing query: %s", str(e))
                response = f"Error processing query: {str(e)}"
                agent_thoughts = [f"❌ Error occurred: {str(e)}"]
            logger.info(
                "Received query: %s..., Response: %s...",
                user_input[:50],
                response[:50],
            )
    return render_template_string(
        """
        <!DOCTYPE html>
        <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>🤖 Personal AI Agent</title>
                <style>
                    * { box-sizing: border-box; }
                    body { 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                        margin: 0; 
                        padding: 20px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        color: #333;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 15px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        overflow: hidden;
                    }
                    .header {
                        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                        color: white;
                        padding: 20px;
                        text-align: center;
                    }
                    .header h1 {
                        margin: 0;
                        font-size: 2rem;
                        font-weight: 300;
                    }
                    .content {
                        display: grid;
                        grid-template-columns: 1fr 400px;
                        gap: 0;
                        min-height: 600px;
                    }
                    .main-panel {
                        padding: 30px;
                    }
                    .thoughts-panel {
                        background: #f8f9fa;
                        border-left: 3px solid #4facfe;
                        padding: 20px;
                        overflow-y: auto;
                        max-height: 600px;
                    }
                    .form-group {
                        margin-bottom: 20px;
                    }
                    label {
                        display: block;
                        font-weight: 600;
                        margin-bottom: 5px;
                        color: #555;
                    }
                    textarea, input[type="text"] {
                        width: 100%;
                        padding: 12px;
                        border: 2px solid #e1e8ed;
                        border-radius: 8px;
                        font-size: 14px;
                        font-family: inherit;
                        transition: border-color 0.3s ease;
                    }
                    textarea:focus, input[type="text"]:focus {
                        outline: none;
                        border-color: #4facfe;
                        box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
                    }
                    .button-group {
                        display: flex;
                        gap: 10px;
                        margin-top: 20px;
                    }
                    .btn {
                        padding: 12px 24px;
                        border: none;
                        border-radius: 8px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        font-size: 14px;
                        text-decoration: none;
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                    }
                    .btn-primary {
                        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                        color: white;
                    }
                    .btn-primary:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
                    }
                    .btn-danger {
                        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                        color: white;
                    }
                    .btn-danger:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 5px 15px rgba(238, 90, 82, 0.4);
                    }
                    .response-section {
                        margin-top: 30px;
                        padding: 20px;
                        background: #f8f9fa;
                        border-radius: 10px;
                        border-left: 4px solid #28a745;
                    }
                    .response-section h2 {
                        margin: 0 0 15px 0;
                        color: #28a745;
                        font-size: 1.2rem;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }
                    .response-content {
                        white-space: pre-wrap;
                        line-height: 1.6;
                        background: white;
                        padding: 15px;
                        border-radius: 8px;
                        border: 1px solid #e1e8ed;
                    }
                    .context-section {
                        margin-top: 20px;
                        padding: 15px;
                        background: #e3f2fd;
                        border-radius: 10px;
                        border-left: 4px solid #2196f3;
                    }
                    .context-section h3 {
                        margin: 0 0 10px 0;
                        color: #1976d2;
                        font-size: 1rem;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }
                    .context-item {
                        background: white;
                        padding: 10px;
                        margin: 5px 0;
                        border-radius: 6px;
                        border-left: 3px solid #2196f3;
                        font-size: 0.9rem;
                        line-height: 1.4;
                    }
                    .thoughts-header {
                        font-weight: 600;
                        color: #666;
                        margin-bottom: 15px;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        font-size: 1.1rem;
                    }
                    .thought-item {
                        background: white;
                        padding: 10px 15px;
                        margin: 8px 0;
                        border-radius: 8px;
                        border-left: 3px solid #4facfe;
                        font-size: 0.9rem;
                        line-height: 1.4;
                        animation: slideIn 0.3s ease-out;
                    }
                    @keyframes slideIn {
                        from { opacity: 0; transform: translateX(-10px); }
                        to { opacity: 1; transform: translateX(0); }
                    }
                    .empty-thoughts {
                        text-align: center;
                        color: #999;
                        font-style: italic;
                        padding: 40px 20px;
                    }
                    @media (max-width: 768px) {
                        .content {
                            grid-template-columns: 1fr;
                        }
                        .thoughts-panel {
                            border-left: none;
                            border-top: 3px solid #4facfe;
                            max-height: 300px;
                        }
                        body { padding: 10px; }
                    }
                    .context-preview {
                        max-height: 150px;
                        overflow-y: auto;
                    }
                    .context-item-short {
                        display: -webkit-box;
                        -webkit-line-clamp: 2;
                        -webkit-box-orient: vertical;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }
                    .loading-spinner {
                        display: none;
                        border: 3px solid #f3f3f3;
                        border-top: 3px solid #4facfe;
                        border-radius: 50%;
                        width: 20px;
                        height: 20px;
                        animation: spin 1s linear infinite;
                        margin-right: 8px;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    .processing-thoughts {
                        display: none;
                    }
                    .btn:disabled {
                        opacity: 0.6;
                        cursor: not-allowed;
                        transform: none !important;
                    }
                </style>
                <script>
                    function showProgress() {
                        // Show loading spinner on button
                        const submitBtn = document.querySelector('.btn-primary');
                        const spinner = document.querySelector('.loading-spinner');
                        
                        if (submitBtn && spinner) {
                            submitBtn.disabled = true;
                            spinner.style.display = 'inline-block';
                            submitBtn.innerHTML = '<div class="loading-spinner" style="display: inline-block;"></div>Processing...';
                        }
                        
                        // Show processing thoughts immediately
                        const thoughtsPanel = document.querySelector('.thoughts-panel');
                        if (thoughtsPanel) {
                            const processingThoughts = [
                                '🚀 Starting to process your request...',
                                '🔄 Initializing AI reasoning...',
                                '📊 Preparing tools and memory access...'
                            ];
                            
                            // Clear existing thoughts
                            const thoughtsContainer = thoughtsPanel.querySelector('.thoughts-header').parentNode;
                            const existingThoughts = thoughtsContainer.querySelectorAll('.thought-item, .empty-thoughts');
                            existingThoughts.forEach(item => item.remove());
                            
                            // Add processing thoughts
                            processingThoughts.forEach((thought, index) => {
                                setTimeout(() => {
                                    const thoughtItem = document.createElement('div');
                                    thoughtItem.className = 'thought-item';
                                    thoughtItem.textContent = thought;
                                    thoughtsContainer.appendChild(thoughtItem);
                                }, index * 500); // Stagger the thoughts
                            });
                        }
                        
                        return true; // Allow form to submit
                    }
                </script>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🤖 Personal AI Agent</h1>
                        <p style="margin: 5px 0 0 0; opacity: 0.9;">Your intelligent assistant with memory, research, and reasoning capabilities</p>
                    </div>
                    
                    <div class="content">
                        <div class="main-panel">
                            <form method="post" onsubmit="return showProgress()">
                                <div class="form-group">
                                    <label for="query">💬 Ask me anything:</label>
                                    <textarea name="query" id="query" rows="4" placeholder="e.g., Research Python 3.12 features, help me write a script, remember my preferences..."></textarea>
                                </div>
                                
                                <div class="form-group">
                                    <label for="topic">🏷️ Topic Category:</label>
                                    <input type="text" name="topic" id="topic" value="general" placeholder="e.g., programming, personal, research, etc.">
                                </div>
                                
                                <div class="button-group">
                                    <button type="submit" class="btn btn-primary">
                                        <div class="loading-spinner"></div>
                                        🚀 Ask Agent
                                    </button>
                                    <button type="button" class="btn btn-danger" onclick="if(confirm('⚠️ Are you sure you want to clear all stored knowledge? This action cannot be undone.')) { window.location.href='/clear'; }">
                                        🗑️ Reset Knowledge
                                    </button>
                                </div>
                            </form>
                            
                            {% if response %}
                                <div class="response-section">
                                    <h2>🎯 Agent Response</h2>
                                    <div class="response-content">{{ response }}</div>
                                </div>
                            {% endif %}
                            
                            {% if context and context != ['No relevant context found.'] and context != ['Weaviate is disabled, no context available.'] %}
                                <div class="context-section">
                                    <h3>🧠 Memory Context Used</h3>
                                    <div class="context-preview">
                                        {% for item in context %}
                                            <div class="context-item context-item-short">{{ item }}</div>
                                        {% endfor %}
                                    </div>
                                </div>
                            {% endif %}
                        </div>
                        
                        <div class="thoughts-panel">
                            <div class="thoughts-header">
                                🧠 Agent Thoughts
                            </div>
                            
                            {% if agent_thoughts %}
                                {% for thought in agent_thoughts %}
                                    <div class="thought-item">{{ thought }}</div>
                                {% endfor %}
                            {% else %}
                                <div class="empty-thoughts">
                                    💭 Agent thoughts will appear here during processing...
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """,
        response=response,
        context=context,
        agent_thoughts=agent_thoughts,
    )


@app.route("/clear")
def clear_kb():
    """Route to clear the knowledge base."""
    try:
        result = clear_knowledge_base.invoke({})
        logger.info("Knowledge base cleared via web interface: %s", result)
        return render_template_string(
            """
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>🤖 Personal AI Agent - Knowledge Cleared</title>
                    <style>
                        * { box-sizing: border-box; }
                        body { 
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                            margin: 0; 
                            padding: 20px; 
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            min-height: 100vh;
                            color: #333;
                        }
                        .container {
                            max-width: 600px;
                            margin: 50px auto;
                            background: white;
                            border-radius: 15px;
                            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                            overflow: hidden;
                            text-align: center;
                        }
                        .header {
                            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                            color: white;
                            padding: 30px;
                        }
                        .header h1 {
                            margin: 0;
                            font-size: 1.8rem;
                            font-weight: 300;
                        }
                        .content {
                            padding: 40px 30px;
                        }
                        .success-icon {
                            font-size: 4rem;
                            margin-bottom: 20px;
                        }
                        .success-message {
                            background: #d4edda;
                            border: 2px solid #c3e6cb;
                            border-radius: 10px;
                            padding: 20px;
                            margin: 20px 0;
                            color: #155724;
                            font-weight: 500;
                        }
                        .btn {
                            display: inline-block;
                            padding: 12px 24px;
                            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                            color: white;
                            text-decoration: none;
                            border-radius: 8px;
                            font-weight: 600;
                            transition: all 0.3s ease;
                            margin-top: 20px;
                        }
                        .btn:hover {
                            transform: translateY(-2px);
                            box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>🗑️ Knowledge Base Cleared</h1>
                        </div>
                        <div class="content">
                            <div class="success-icon">✅</div>
                            <div class="success-message">
                                <strong>Success!</strong> {{ result }}
                            </div>
                            <a href="/" class="btn">🏠 Back to Agent</a>
                        </div>
                    </div>
                </body>
            </html>
            """,
            result=result,
        )
    except Exception as e:
        logger.error("Error clearing knowledge base via web interface: %s", str(e))
        return render_template_string(
            """
            <!DOCTYPE html>
            <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>🤖 Personal AI Agent - Error</title>
                    <style>
                        * { box-sizing: border-box; }
                        body { 
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                            margin: 0; 
                            padding: 20px; 
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            min-height: 100vh;
                            color: #333;
                        }
                        .container {
                            max-width: 600px;
                            margin: 50px auto;
                            background: white;
                            border-radius: 15px;
                            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                            overflow: hidden;
                            text-align: center;
                        }
                        .header {
                            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                            color: white;
                            padding: 30px;
                        }
                        .header h1 {
                            margin: 0;
                            font-size: 1.8rem;
                            font-weight: 300;
                        }
                        .content {
                            padding: 40px 30px;
                        }
                        .error-icon {
                            font-size: 4rem;
                            margin-bottom: 20px;
                        }
                        .error-message {
                            background: #f8d7da;
                            border: 2px solid #f5c6cb;
                            border-radius: 10px;
                            padding: 20px;
                            margin: 20px 0;
                            color: #721c24;
                            font-weight: 500;
                        }
                        .btn {
                            display: inline-block;
                            padding: 12px 24px;
                            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                            color: white;
                            text-decoration: none;
                            border-radius: 8px;
                            font-weight: 600;
                            transition: all 0.3s ease;
                            margin-top: 20px;
                        }
                        .btn:hover {
                            transform: translateY(-2px);
                            box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>❌ Error Occurred</h1>
                        </div>
                        <div class="content">
                            <div class="error-icon">⚠️</div>
                            <div class="error-message">
                                <strong>Error!</strong> Failed to clear knowledge base: {{ error }}
                            </div>
                            <a href="/" class="btn">🏠 Back to Agent</a>
                        </div>
                    </div>
                </body>
            </html>
            """,
            error=str(e),
        )


def cleanup():
    """Clean up resources on shutdown."""
    global weaviate_client, vector_store

    # Prevent multiple cleanup calls
    if hasattr(cleanup, "called") and cleanup.called:
        logger.debug("Cleanup already called, skipping...")
        return
    cleanup.called = True

    logger.info("Starting cleanup process...")

    # Clean up MCP servers
    if mcp_client:
        try:
            # Use stop_all_servers method (no need for individual stops)
            mcp_client.stop_all_servers()
            logger.info("MCP servers stopped successfully")

            # Give servers time to shutdown properly
            time.sleep(1)

        except Exception as e:
            logger.error("Error stopping MCP servers: %s", e)

    # Clean up Weaviate vector store and client
    if vector_store:
        try:
            # Clean up the vector store first
            if hasattr(vector_store, "client") and vector_store.client:
                vector_store.client.close()
                logger.debug("Vector store client closed")
            vector_store = None
        except Exception as e:
            logger.error("Error closing vector store: %s", e)

    if weaviate_client:
        try:
            # Ensure the client is properly disconnected
            if (
                hasattr(weaviate_client, "is_connected")
                and weaviate_client.is_connected()
            ):
                weaviate_client.close()
                logger.info("Weaviate client closed successfully")
            elif hasattr(weaviate_client, "close"):
                weaviate_client.close()
                logger.info("Weaviate client closed successfully")
            weaviate_client = None
        except Exception as e:
            logger.error("Error closing Weaviate client: %s", e)

    # Force garbage collection to help with cleanup

    gc.collect()

    logger.info("Cleanup process completed")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received signal %d, shutting down gracefully...", signum)
    cleanup()
    sys.exit(0)


def main():
    """Main entry point for the Personal AI Agent."""
    # Register cleanup function for normal exit
    atexit.register(cleanup)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting Personal AI Agent...")
    logger.info("Web interface will be available at: http://127.0.0.1:5001")

    try:
        # Disable Flask's reloader in production to avoid resource leaks
        app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        # cleanup() will be called by atexit, no need to call here
    except Exception as e:
        logger.error("Error running Flask app: %s", e)
        cleanup()
        raise


if __name__ == "__main__":
    main()

# end of personal_agent.py
