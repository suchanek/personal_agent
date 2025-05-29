# pylint: disable=C0301,C0116
# pylint: disable=C0301,C0116,C0115,W0613,E0611,C0413,E0401,W0601,W0621,C0302,E1101,C0103,W0718

import atexit
import json
import logging
import subprocess
import time
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
import weaviate.classes.config as wvc
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

# Suppress Pydantic deprecation warnings from Ollama
warnings.filterwarnings("ignore", category=DeprecationWarning, module="ollama")
warnings.filterwarnings(
    "ignore", message=".*model_fields.*", category=DeprecationWarning
)

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

ROOT_DIR = "/Users/egs"  # Root directory for MCP filesystem server
DATA_DIR = "/Users/egs/data"  # Data directory for vector database
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
        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": ""},  # Set your token here
    },
    "brave-search": {
        "command": "npx",
        "args": ["--yes", "@modelcontextprotocol/server-brave-search"],
        "description": "Web search for research and technical information",
        "env": {"BRAVE_API_KEY": ""},  # Set your API key here
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

            process = subprocess.Popen(
                [config["command"]] + config["args"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                cwd=cwd,
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
                    import weaviate.classes.config as wvc

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
        # The server root is /Users/egs, so we need to make paths relative to that
        if file_path == ROOT_DIR:
            file_path = "."  # Root directory (though reading a directory as file will likely fail)
        elif file_path.startswith("/Users/egs/"):
            file_path = file_path[10:]  # Remove ROOT_DIR prefix
        elif file_path.startswith("~/"):
            file_path = file_path[2:]  # Remove "~/" prefix
        elif file_path.startswith("/"):
            # If it's an absolute path outside home, we can't access it
            return f"Error: Path {file_path} is outside the accessible directory (/Users/egs)"

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
def mcp_write_file(file_path: str, content: str) -> str:
    """Write content to file using MCP filesystem server."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(file_path, str) and file_path.startswith("{"):
        try:
            params = json.loads(file_path)
            file_path = params.get("file_path", file_path)
            content = params.get("content", content)
        except (json.JSONDecodeError, TypeError):
            pass  # Use original values if parsing fails

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot write file."

    try:
        # Determine which server to use based on path
        server_name = "filesystem-home"
        if file_path.startswith("/Users/egs/data/") or file_path.startswith("data/"):
            server_name = "filesystem-data"

        # Start filesystem server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP filesystem server."

        # Convert absolute paths to relative paths for the restricted root
        if server_name == "filesystem-home":
            # The server root is /Users/egs
            if file_path == ROOT_DIR:
                return "Error: Cannot write to root directory as a file"
            elif file_path.startswith("/Users/egs/"):
                file_path = file_path[10:]  # Remove ROOT_DIR prefix
            elif file_path.startswith("~/"):
                file_path = file_path[2:]  # Remove "~/" prefix
            elif file_path.startswith("/"):
                return f"Error: Path {file_path} is outside the accessible directory (/Users/egs)"
        else:  # filesystem-data
            # The server root is /Users/egs/data
            if file_path.startswith("/Users/egs/data/"):
                file_path = file_path[16:]  # Remove "/Users/egs/data/" prefix
            elif file_path.startswith("data/"):
                file_path = file_path[5:]  # Remove "data/" prefix

        # Ensure path doesn't start with / for relative paths
        if file_path.startswith("/"):
            file_path = file_path[1:]

        logger.debug(
            "Calling write_file with path: %s on server: %s", file_path, server_name
        )

        # Call write_file tool with correct parameter name
        result = mcp_client.call_tool_sync(
            server_name, "write_file", {"path": file_path, "contents": content}
        )

        # Store the file write operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = (
                f"Wrote file: {file_path}\nContent length: {len(content)} characters"
            )
            store_interaction.invoke(
                {"text": interaction_text, "topic": "file_operations"}
            )

        logger.info("Wrote file via MCP: %s", file_path)
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
        if directory_path.startswith("/Users/egs/data/") or directory_path.startswith(
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
            # The server root is /Users/egs
            if directory_path == ROOT_DIR:
                directory_path = "."  # Root directory
            elif directory_path.startswith("/Users/egs/"):
                directory_path = directory_path[10:]  # Remove ROOT_DIR prefix
            elif directory_path.startswith("~/"):
                directory_path = directory_path[2:]  # Remove "~/" prefix
            elif directory_path.startswith("/"):
                return f"Error: Path {directory_path} is outside the accessible directory (/Users/egs)"
        else:  # filesystem-data
            # The server root is /Users/egs/data
            if directory_path.startswith("/Users/egs/data/"):
                directory_path = directory_path[16:]  # Remove "/Users/egs/data/" prefix
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
        directory_listing = mcp_list_directory(directory)

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

        # Prepare parameters for GitHub search
        params = {"query": query}
        if repo:
            params["repo"] = repo

        # Call GitHub search tool
        result = mcp_client.call_tool_sync(server_name, "search_repositories", params)

        # Store the GitHub search operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = (
                f"GitHub search: {query}"
                + (f" in {repo}" if repo else "")
                + f"\nResults: {result[:300]}..."
            )
            store_interaction.invoke(
                {"text": interaction_text, "topic": "github_search"}
            )

        logger.info("GitHub search completed: %s", query)
        return result

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
        import subprocess

        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
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
]
agent = create_react_agent(llm=llm, tools=tools, prompt=system_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=3,
)


# Flask routes
@app.route("/", methods=["GET", "POST"])
def index():
    response = None
    context = None
    if request.method == "POST":
        user_input = request.form.get("query", "")
        topic = request.form.get("topic", "general")
        if user_input:
            # Query knowledge base for context
            try:
                # Call the function directly with proper parameters
                context = query_knowledge_base.invoke({"query": user_input, "limit": 5})
                context_str = (
                    "\n".join(context) if context else "No relevant context found."
                )
                # Generate response
                result = agent_executor.invoke(
                    {"input": user_input, "context": context_str}
                )
                if isinstance(result, dict):
                    response = result.get("output", "No response generated.")
                else:
                    response = str(result)
                # Store interaction AFTER getting response
                interaction_text = f"User: {user_input}\nAssistant: {response}"
                store_interaction.invoke({"text": interaction_text, "topic": topic})
            except Exception as e:
                logger.error("Error processing query: %s", str(e))
                response = f"Error processing query: {str(e)}"
            logger.info(
                "Received query: %s..., Response: %s...",
                user_input[:50],
                response[:50],
            )
    return render_template_string(
        """
        <html>
            <head>
                <title>Personal AI Agent</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #333; }
                    textarea, input[type="text"] { width: 100%; max-width: 600px; }
                    input[type="submit"] { margin-top: 10px; padding: 10px 20px; }
                    .reset-btn { margin-left: 10px; padding: 10px 20px; background-color: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; }
                    .reset-btn:hover { background-color: #c82333; }
                    .response, .context { margin-top: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
                    .context { background-color: #f9f9f9; }
                    .context ul { list-style-type: none; padding: 0; }
                    .success-message { margin-top: 20px; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; color: #155724; }
                </style>
            </head>
            <body>
                <h1>Personal AI Agent</h1>
                <form method="post">
                    <label for="query">Query:</label><br>
                    <textarea name="query" rows="5" cols="50" placeholder="Ask me anything..."></textarea><br>
                    <label for="topic">Topic:</label><br>
                    <input type="text" name="topic" value="general" placeholder="e.g., programming, personal, etc."><br>
                    <input type="submit" value="Submit">
                    <button type="button" class="reset-btn" onclick="if(confirm('Are you sure you want to clear all stored knowledge? This action cannot be undone.')) { window.location.href='/clear'; }">Reset Knowledge Base</button>
                </form>
                {% if response %}
                    <div class="response">
                        <h2>Response:</h2>
                        <p style="white-space: pre-wrap;">{{ response }}</p>
                    </div>
                {% endif %}
                {% if context and context != ['No relevant context found.'] %}
                    <div class="context">
                        <h2>Context Used:</h2>
                        <ul>
                        {% for item in context %}
                            <li style="margin: 5px 0; padding: 5px; background: #f0f0f0; border-radius: 3px;">{{ item }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                {% endif %}
            </body>
        </html>
        """,
        response=response,
        context=context,
    )


@app.route("/clear")
def clear_kb():
    """Route to clear the knowledge base."""
    try:
        result = clear_knowledge_base.invoke({})
        logger.info("Knowledge base cleared via web interface: %s", result)
        return render_template_string(
            """
            <html>
                <head>
                    <title>Personal AI Agent - Knowledge Base Cleared</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h1 { color: #333; }
                        .success-message { margin-top: 20px; padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; color: #155724; }
                        .back-btn { margin-top: 20px; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; display: inline-block; }
                        .back-btn:hover { background-color: #0056b3; }
                    </style>
                </head>
                <body>
                    <h1>Personal AI Agent</h1>
                    <div class="success-message">
                        <strong>Success!</strong> {{ result }}
                    </div>
                    <a href="/" class="back-btn">Back to Agent</a>
                </body>
            </html>
            """,
            result=result,
        )
    except Exception as e:
        logger.error("Error clearing knowledge base via web interface: %s", str(e))
        return render_template_string(
            """
            <html>
                <head>
                    <title>Personal AI Agent - Error</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h1 { color: #333; }
                        .error-message { margin-top: 20px; padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; color: #721c24; }
                        .back-btn { margin-top: 20px; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 4px; display: inline-block; }
                        .back-btn:hover { background-color: #0056b3; }
                    </style>
                </head>
                <body>
                    <h1>Personal AI Agent</h1>
                    <div class="error-message">
                        <strong>Error!</strong> Failed to clear knowledge base: {{ error }}
                    </div>
                    <a href="/" class="back-btn">Back to Agent</a>
                </body>
            </html>
            """,
            error=str(e),
        )


def cleanup():
    """Clean up resources on shutdown."""
    global weaviate_client, mcp_client

    # Clean up MCP servers
    if mcp_client:
        try:
            mcp_client.stop_all_servers()
            logger.info("MCP servers stopped successfully")
        except Exception as e:
            logger.error("Error stopping MCP servers: %s", e)

    # Clean up Weaviate client
    if weaviate_client:
        try:
            weaviate_client.close()
            logger.info("Weaviate client closed successfully")
        except Exception as e:
            logger.error("Error closing Weaviate client: %s", e)


def main():
    """Main entry point for the Personal AI Agent."""
    atexit.register(cleanup)
    try:
        app.run(host="127.0.0.1", port=5001, debug=True)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
