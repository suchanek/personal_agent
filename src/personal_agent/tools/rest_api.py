"""
REST API Module for Personal Agent Streamlit Application

This module provides REST API endpoints that run alongside the Streamlit web interface,
allowing external systems to interact with memory and knowledge storage capabilities
via standard HTTP requests.

The API runs on a separate port (default 8002) while sharing the same agent instances
and session state with the Streamlit UI for consistency.

Endpoints:
    Memory:
    - POST /api/v1/memory/store - Store text content as memory
    - POST /api/v1/memory/store-url - Extract and store URL content as memory
    - GET /api/v1/memory/search - Search existing memories
    - GET /api/v1/memory/list - List all memories
    - DELETE /api/v1/memory/{memory_id} - Delete specific memory
    - GET /api/v1/memory/stats - Get memory statistics

    Knowledge:
    - POST /api/v1/knowledge/store-text - Store text in knowledge base
    - POST /api/v1/knowledge/store-url - Extract and store URL content in knowledge base
    - GET /api/v1/knowledge/search - Search knowledge base
    - GET /api/v1/knowledge/status - Get knowledge base status

    Users:
    - GET /api/v1/users - List all users
    - POST /api/v1/users/switch - Switch to a different user (includes system restart)
        Parameters:
        - user_id (required): User ID to switch to
        - restart_containers (optional, default: true): Restart Docker containers
        - restart_system (optional, default: true): Restart agent/team system

    System:
    - GET /api/v1/health - Health check
    - GET /api/v1/status - System status

Usage:
    # Store memory
    curl -X POST http://localhost:8001/api/v1/memory/store \
      -H "Content-Type: application/json" \
      -d '{"content": "I work at Google", "topics": ["work"]}'

    # Store knowledge from URL
    curl -X POST http://localhost:8001/api/v1/knowledge/store-url \
      -H "Content-Type: application/json" \
      -d '{"url": "https://example.com", "title": "Example"}'

Author: Personal Agent Development Team
Version: v1.0.0
Last Revision: 2025-01-24
"""

import asyncio
import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request

# Try to import CORS, but make it optional
try:
    from flask_cors import CORS

    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False

# Handle imports for both module import and direct execution
try:
    from ..utils import setup_logging
    from .global_state import get_global_state

    logger = setup_logging(__name__)
except ImportError:
    # Fallback for when running directly before main block
    import logging

    logger = logging.getLogger(__name__)
    get_global_state = None


class PersonalAgentRestAPI:
    """REST API server for Personal Agent memory and knowledge operations."""

    def __init__(self, port: int = 8002, host: str = "0.0.0.0"):
        self.port = port
        self.host = host
        self.app = Flask(__name__)

        # Enable CORS if available
        if CORS_AVAILABLE:
            CORS(self.app)
        else:
            # Add basic CORS headers manually
            @self.app.after_request
            def after_request(response):
                response.headers.add("Access-Control-Allow-Origin", "*")
                response.headers.add(
                    "Access-Control-Allow-Headers", "Content-Type,Authorization"
                )
                response.headers.add(
                    "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS"
                )
                return response

        # Reference to Streamlit session state (will be set externally)
        self.streamlit_session = None

        # Setup routes
        self._setup_routes()

        # Server thread
        self._server_thread = None
        self._running = False

    def set_streamlit_session(self, session_state):
        """Set reference to Streamlit session state for shared agent access."""
        self.streamlit_session = session_state

    def _setup_routes(self):
        """Setup all API routes."""

        # Health and status endpoints
        @self.app.route("/api/v1/health", methods=["GET"])
        def health_check():
            try:
                # Use global state to check system health
                global_state = get_global_state()
                if global_state is None:
                    logger.error("global_state is None")
                    raise Exception("Global state not available")
                    
                global_status = global_state.get_status()
                if global_status is None:
                    logger.error("global_status is None")
                    raise Exception("Global status not available")

                # Check all required conditions
                streamlit_connected = self.streamlit_session is not None
                agent_available = global_status.get("agent_available", False)
                team_available = global_status.get("team_available", False)
                memory_available = global_status.get("memory_helper_available", False)
                knowledge_available = global_status.get("knowledge_helper_available", False)

                # Get user and model directly from global state (using correct keys)
                user = global_status.get("user", "unknown")  # get_status returns "user" key
                model = global_status.get("llm_model", "unknown")  # get_status returns "llm_model" key

                # System is healthy if all conditions are met, with exception that either team or agent must be available
                is_healthy = (
                    streamlit_connected
                    and memory_available
                    and knowledge_available
                    and (agent_available or team_available)
                )

                status = "healthy" if is_healthy else "unhealthy"

                return jsonify(
                    {
                        "status": status,
                        "timestamp": datetime.now().isoformat(),
                        "service": "personal-agent-api",
                        "version": "1.0.0",
                        "model": model,
                        "user": user,
                        "checks": {
                            "streamlit_connected": streamlit_connected,
                            "agent_available": agent_available,
                            "team_available": team_available,
                            "memory_available": memory_available,
                            "knowledge_available": knowledge_available,
                        },
                    }
                )

            except Exception as e:
                logger.error(f"Error in health check: {e}")
                return (
                    jsonify(
                        {
                            "status": "Unhealthy",
                            "timestamp": datetime.now().isoformat(),
                            "service": "personal-agent-api",
                            "version": "1.0.0",
                            "error": str(e),
                        }
                    ),
                    503,
                )

        @self.app.route("/api/v1/status", methods=["GET"])
        def system_status():
            try:
                # Use global state instead of Streamlit session state
                global_state = get_global_state()
                global_status = global_state.get_status()

                # Get user and model directly from global state
                user = global_status.get("user", "unknown")
                model = global_status.get("llm_model", "unknown")

                status = {
                    "status": "Running",
                    "timestamp": datetime.now().isoformat(),
                    "streamlit_connected": self.streamlit_session is not None,
                    "agent_available": (
                        "Yes" if global_status["agent_available"] else "No"
                    ),
                    "team_available": (
                        "Yes" if global_status["team_available"] else "No"
                    ),
                    "memory_available": (
                        "Yes" if global_status["memory_helper_available"] else "No"
                    ),
                    "knowledge_available": (
                        "Yes" if global_status["knowledge_helper_available"] else "No"
                    ),
                    "user": user,
                    "model": model,
                }

                return jsonify(status)
            except Exception as e:
                print(
                    f"Error getting system status: {e}"
                )  # Use print since logger may not be available
                return jsonify({"error": str(e)}), 500

        # Memory endpoints
        @self.app.route("/api/v1/memory/store", methods=["POST"])
        def store_memory():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400

                content = data.get("content", "").strip()
                if not content:
                    return jsonify({"error": "Content is required"}), 400

                topics = data.get("topics", [])
                if isinstance(topics, str):
                    topics = [t.strip() for t in topics.split(",") if t.strip()]

                # Get memory helper from Streamlit session
                memory_helper = self._get_memory_helper()
                if not memory_helper:
                    return jsonify({"error": "Memory system not available"}), 503

                # Store memory
                result = memory_helper.add_memory(
                    memory_text=content,
                    topics=topics if topics else None,
                    input_text="REST API",
                )

                # Parse result
                if hasattr(result, "is_success"):
                    success = result.is_success
                    message = result.message
                    memory_id = getattr(result, "memory_id", None)
                    generated_topics = getattr(result, "topics", topics)
                elif isinstance(result, tuple) and len(result) >= 2:
                    success, message = result[0], result[1]
                    memory_id = result[2] if len(result) > 2 else None
                    generated_topics = result[3] if len(result) > 3 else topics
                else:
                    success = False
                    message = f"Unexpected result format: {result}"
                    memory_id = None
                    generated_topics = topics

                if success:
                    logger.info(
                        f"Successfully stored memory via API: {content[:50]}..."
                    )
                    return jsonify(
                        {
                            "success": "True",
                            "message": message,
                            "memory_id": memory_id,
                            "topics": generated_topics,
                            "content_length": len(content),
                        }
                    )
                else:
                    logger.warning(f"Failed to store memory via API: {message}")
                    return jsonify({"error": message}), 400

            except Exception as e:
                logger.error(f"Error storing memory via API: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/v1/memory/store-url", methods=["POST"])
        def store_memory_from_url():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400

                url = data.get("url", "").strip()
                if not url:
                    return jsonify({"error": "URL is required"}), 400

                # Validate URL
                parsed_url = urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    return jsonify({"error": "Invalid URL format"}), 400

                title = data.get("title", "").strip()
                topics = data.get("topics", [])
                if isinstance(topics, str):
                    topics = [t.strip() for t in topics.split(",") if t.strip()]

                extract_method = data.get("extract_method", "full_text")

                # Extract content from URL
                try:
                    content, extracted_title = self._extract_url_content(
                        url, extract_method
                    )
                    if not content:
                        return (
                            jsonify(
                                {"error": "No content could be extracted from URL"}
                            ),
                            400,
                        )

                    # Use provided title or extracted title
                    final_title = title or extracted_title or parsed_url.netloc

                    # Add source URL to content
                    content_with_source = (
                        f"Source: {url}\nTitle: {final_title}\n\n{content}"
                    )

                except Exception as e:
                    logger.error(f"Error extracting content from URL {url}: {e}")
                    return (
                        jsonify(
                            {"error": f"Failed to extract content from URL: {str(e)}"}
                        ),
                        400,
                    )

                # Get memory helper
                memory_helper = self._get_memory_helper()
                if not memory_helper:
                    return jsonify({"error": "Memory system not available"}), 503

                # Store memory
                result = memory_helper.add_memory(
                    memory_text=content_with_source,
                    topics=topics if topics else None,
                    input_text=f"REST API - URL: {url}",
                )

                # Parse result
                if hasattr(result, "is_success"):
                    success = result.is_success
                    message = result.message
                    memory_id = getattr(result, "memory_id", None)
                    generated_topics = getattr(result, "topics", topics)
                elif isinstance(result, tuple) and len(result) >= 2:
                    success, message = result[0], result[1]
                    memory_id = result[2] if len(result) > 2 else None
                    generated_topics = result[3] if len(result) > 3 else topics
                else:
                    success = False
                    message = f"Unexpected result format: {result}"
                    memory_id = None
                    generated_topics = topics

                if success:
                    logger.info(f"Successfully stored memory from URL via API: {url}")
                    return jsonify(
                        {
                            "success": "True",
                            "message": message,
                            "memory_id": memory_id,
                            "topics": generated_topics,
                            "url": url,
                            "extracted_title": final_title,
                            "content_length": len(content_with_source),
                        }
                    )
                else:
                    logger.warning(
                        f"Failed to store memory from URL via API: {message}"
                    )
                    return jsonify({"error": message}), 400

            except Exception as e:
                logger.error(f"Error storing memory from URL via API: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/v1/memory/search", methods=["GET"])
        def search_memories():
            try:
                query = request.args.get("q", "").strip()
                if not query:
                    return jsonify({"error": "Query parameter 'q' is required"}), 400

                limit = request.args.get("limit", 10, type=int)
                similarity_threshold = request.args.get(
                    "similarity_threshold", 0.3, type=float
                )

                # Get memory helper
                memory_helper = self._get_memory_helper()
                if not memory_helper:
                    return jsonify({"error": "Memory system not available"}), 503

                # Search memories
                search_results = memory_helper.search_memories(
                    query=query, limit=limit, similarity_threshold=similarity_threshold
                )

                # Format results
                results = []
                for memory, score in search_results:
                    results.append(
                        {
                            "memory_id": getattr(memory, "memory_id", None),
                            "content": memory.memory,
                            "similarity_score": round(score, 3),
                            "topics": getattr(memory, "topics", []),
                            "last_updated": getattr(memory, "last_updated", None),
                            "input": getattr(memory, "input", None),
                        }
                    )

                logger.info(f"Memory search via API: {query} - {len(results)} results")
                return jsonify(
                    {
                        "success": "True",
                        "query": query,
                        "results": results,
                        "total_results": len(results),
                        "limit": limit,
                        "similarity_threshold": similarity_threshold,
                    }
                )

            except Exception as e:
                logger.error(f"Error searching memories via API: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/v1/memory/list", methods=["GET"])
        def list_memories():
            try:
                limit = request.args.get("limit", None, type=int)

                # Get memory helper
                memory_helper = self._get_memory_helper()
                if not memory_helper:
                    return jsonify({"error": "Memory system not available"}), 503

                # Get all memories
                memories = memory_helper.get_all_memories()

                # Apply limit if specified
                if limit and len(memories) > limit:
                    memories = memories[:limit]

                # Format results
                results = []
                for memory in memories:
                    results.append(
                        {
                            "memory_id": getattr(memory, "memory_id", None),
                            "content": memory.memory,
                            "topics": getattr(memory, "topics", []),
                            "last_updated": getattr(memory, "last_updated", None),
                            "input": getattr(memory, "input", None),
                        }
                    )

                logger.info(f"Memory list via API: {len(results)} memories")
                return jsonify(
                    {
                        "success": "True",
                        "memories": results,
                        "total_count": len(results),
                        "limit": limit,
                    }
                )

            except Exception as e:
                logger.error(f"Error listing memories via API: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/v1/memory/stats", methods=["GET"])
        def memory_stats():
            try:
                # Get memory helper
                memory_helper = self._get_memory_helper()
                if not memory_helper:
                    return jsonify({"error": "Memory system not available"}), 503

                # Get memory statistics
                stats = memory_helper.get_memory_stats()

                if "error" in stats:
                    return jsonify({"error": stats["error"]}), 500

                logger.info("Memory stats retrieved via API")
                return jsonify({"success": "True", "stats": stats})

            except Exception as e:
                logger.error(f"Error getting memory stats via API: {e}")
                return jsonify({"error": str(e)}), 500

        # Knowledge endpoints
        @self.app.route("/api/v1/knowledge/store-text", methods=["POST"])
        def store_knowledge_text():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400

                content = data.get("content", "").strip()
                if not content:
                    return jsonify({"error": "Content is required"}), 400

                title = data.get("title", "").strip()
                if not title:
                    return jsonify({"error": "Title is required"}), 400

                file_type = data.get("file_type", "txt")

                # Get knowledge helper
                knowledge_helper = self._get_knowledge_helper()
                if not knowledge_helper:
                    return jsonify({"error": "Knowledge system not available"}), 503

                # Get the agent to access knowledge tools
                agent = self._get_agent()
                if not agent:
                    return jsonify({"error": "Agent not available"}), 503

                # Find knowledge tools
                knowledge_tools = self._get_knowledge_tools(agent)
                if not knowledge_tools:
                    return jsonify({"error": "Knowledge tools not available"}), 503

                # Store knowledge using unified method
                result = knowledge_tools.ingest_knowledge_text(
                    content, title, file_type
                )

                if "✅" in result:
                    logger.info(f"Successfully stored knowledge text via API: {title}")
                    return jsonify(
                        {
                            "success": "True",
                            "message": result,
                            "title": title,
                            "content_length": len(content),
                            "file_type": file_type,
                        }
                    )
                else:
                    logger.warning(f"Failed to store knowledge text via API: {result}")
                    return jsonify({"success": "False", "error": result}), 400

            except Exception as e:
                logger.error(f"Error storing knowledge text via API: {e}")
                return jsonify({"success": "False", "error": str(e)}), 500

        @self.app.route("/api/v1/knowledge/store-url", methods=["POST"])
        def store_knowledge_from_url():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400

                url = data.get("url", "").strip()
                if not url:
                    return jsonify({"error": "URL is required"}), 400

                # Validate URL
                parsed_url = urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    return jsonify({"error": "Invalid URL format"}), 400

                title = data.get("title", "").strip()

                # Get agent
                agent = self._get_agent()
                if not agent:
                    return jsonify({"error": "Agent not available"}), 503

                # Find knowledge tools
                knowledge_tools = self._get_knowledge_tools(agent)
                if not knowledge_tools:
                    return jsonify({"error": "Knowledge tools not available"}), 503

                # Store knowledge from URL using unified method
                result = knowledge_tools.ingest_knowledge_from_url(url, title)

                if "✅" in result:
                    logger.info(
                        f"Successfully stored knowledge from URL via API: {url}"
                    )
                    return jsonify(
                        {
                            "success": "True",
                            "message": result,
                            "url": url,
                            "title": title or parsed_url.netloc,
                        }
                    )
                else:
                    logger.warning(
                        f"Failed to store knowledge from URL via API: {result}"
                    )
                    return jsonify({"success": "False", "error": result}), 400

            except Exception as e:
                logger.error(f"Error storing knowledge from URL via API: {e}")
                return jsonify({"success": "False", "error": str(e)}), 500

        @self.app.route("/api/v1/knowledge/search", methods=["GET"])
        def search_knowledge():
            try:
                query = request.args.get("q", "").strip()
                if not query:
                    return jsonify({"error": "Query parameter 'q' is required"}), 400

                mode = request.args.get("mode", "auto")
                limit = request.args.get("limit", 5, type=int)

                # Get agent
                agent = self._get_agent()
                if not agent:
                    return jsonify({"error": "Agent not available"}), 503

                # Find knowledge tools
                knowledge_tools = self._get_knowledge_tools(agent)
                if not knowledge_tools:
                    return jsonify({"error": "Knowledge tools not available"}), 503

                # Search knowledge base
                result = asyncio.run(
                    knowledge_tools.query_knowledge_base(query, mode, limit)
                )

                logger.info(f"Knowledge search via API: {query}")
                return jsonify(
                    {
                        "success": "True",
                        "query": query,
                        "mode": mode,
                        "limit": limit,
                        "result": result,
                    }
                )

            except Exception as e:
                logger.error(f"Error searching knowledge via API: {e}")
                return jsonify({"success": "False", "error": str(e)}), 500

        @self.app.route("/api/v1/knowledge/status", methods=["GET"])
        def knowledge_status():
            try:
                # Get knowledge helper
                knowledge_helper = self._get_knowledge_helper()
                if not knowledge_helper:
                    return jsonify({"error": "Knowledge system not available"}), 503

                # Check knowledge manager status
                km = knowledge_helper.knowledge_manager
                status = {
                    "knowledge_manager_available": km is not None,
                    "semantic_kb_available": knowledge_helper.agno_knowledge
                    is not None,
                    "lightrag_available": False,
                }

                # Test LightRAG connection
                try:
                    from ..config import settings

                    response = requests.get(
                        f"{settings.LIGHTRAG_URL}/health", timeout=5
                    )
                    status["lightrag_available"] = response.status_code == 200
                    status["lightrag_url"] = settings.LIGHTRAG_URL
                except:
                    status["lightrag_available"] = False

                logger.info("Knowledge status retrieved via API")
                return jsonify({"success": "True", "status": status})

            except Exception as e:
                logger.error(f"Error getting knowledge status via API: {e}")
                return jsonify({"success": "False", "error": str(e)}), 500

        # User endpoints
        @self.app.route("/api/v1/users", methods=["GET"])
        def list_users():
            try:
                # Import user utilities
                from ..streamlit.utils.user_utils import get_all_users

                # Get all users
                users = get_all_users()

                logger.info(f"Users list retrieved via API: {len(users)} users")
                return jsonify({
                    "success": "True",
                    "users": users,
                    "total_count": len(users)
                })

            except Exception as e:
                logger.error(f"Error listing users via API: {e}")
                return jsonify({"success": "False", "error": str(e)}), 500

        @self.app.route("/api/v1/users/switch", methods=["POST"])
        def switch_user():
            try:
                data = request.get_json()
                if not data:
                    return jsonify({"error": "No JSON data provided"}), 400

                user_id = data.get("user_id", "").strip()
                if not user_id:
                    return jsonify({"error": "user_id is required"}), 400

                restart_containers = data.get("restart_containers", True)
                restart_system = data.get("restart_system", True)  # New parameter to control system restart

                # Import user utilities
                from ..streamlit.utils.user_utils import switch_user

                # Switch to the specified user
                result = switch_user(user_id, restart_containers=restart_containers)

                if result.get("success", False):
                    logger.info(f"Successfully switched to user via API: {user_id}")

                    # After successful user switch, perform system restart if requested
                    system_restart_result = None
                    if restart_system:
                        logger.info(f"Performing system restart after user switch to {user_id}")
                        try:
                            # Create restart marker file to trigger page refresh in Streamlit apps
                            import tempfile
                            marker_file = os.path.join(tempfile.gettempdir(), "personal_agent_restart_marker")
                            with open(marker_file, "w") as f:
                                f.write(str(time.time()))

                            # Call the system restart logic directly
                            global_state = get_global_state()
                            current_agent_mode = global_state.get("agent_mode", "single")
                            current_model = global_state.get("llm_model", os.getenv("LLM_MODEL", "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:q8_0"))
                            current_ollama_url = global_state.get("ollama_url", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))

                            # Clear global state
                            global_state.clear()

                            # Reinitialize based on agent mode
                            restart_success = False
                            restart_message = ""

                            if current_agent_mode == "team":
                                try:
                                    from .streamlit_agent_manager import initialize_team
                                    team = initialize_team(current_model, current_ollama_url, recreate=True)
                                    if team:
                                        global_state.set("agent_mode", "team")
                                        global_state.set("team", team)
                                        global_state.set("llm_model", current_model)
                                        global_state.set("ollama_url", current_ollama_url)

                                        from .streamlit_helpers import StreamlitMemoryHelper, StreamlitKnowledgeHelper
                                        if hasattr(team, "members") and team.members:
                                            knowledge_agent = team.members[0]
                                            memory_helper = StreamlitMemoryHelper(knowledge_agent)
                                            knowledge_helper_obj = StreamlitKnowledgeHelper(knowledge_agent)
                                            global_state.set("memory_helper", memory_helper)
                                            global_state.set("knowledge_helper", knowledge_helper_obj)

                                        restart_success = True
                                        restart_message = "System restarted successfully in team mode"
                                        logger.info(restart_message)
                                    else:
                                        restart_message = "Failed to initialize team during restart"
                                        logger.error(restart_message)
                                except Exception as e:
                                    restart_message = f"Error restarting team: {str(e)}"
                                    logger.error(restart_message)
                            else:
                                try:
                                    from .streamlit_agent_manager import initialize_agent
                                    agent = initialize_agent(current_model, current_ollama_url, recreate=True)
                                    if agent:
                                        global_state.set("agent_mode", "single")
                                        global_state.set("agent", agent)
                                        global_state.set("llm_model", current_model)
                                        global_state.set("ollama_url", current_ollama_url)

                                        from .streamlit_helpers import StreamlitMemoryHelper, StreamlitKnowledgeHelper
                                        memory_helper = StreamlitMemoryHelper(agent)
                                        knowledge_helper_obj = StreamlitKnowledgeHelper(agent)
                                        global_state.set("memory_helper", memory_helper)
                                        global_state.set("knowledge_helper", knowledge_helper_obj)

                                        restart_success = True
                                        restart_message = "System restarted successfully in single agent mode"
                                        logger.info(restart_message)
                                    else:
                                        restart_message = "Failed to initialize agent during restart"
                                        logger.error(restart_message)
                                except Exception as e:
                                    restart_message = f"Error restarting agent: {str(e)}"
                                    logger.error(restart_message)

                            system_restart_result = {
                                "restart_performed": True,
                                "restart_success": restart_success,
                                "restart_message": restart_message,
                                "agent_mode": current_agent_mode,
                                "model": current_model
                            }

                        except Exception as restart_error:
                            logger.error(f"Error during system restart after user switch: {restart_error}")
                            system_restart_result = {
                                "restart_performed": True,
                                "restart_success": False,
                                "restart_message": str(restart_error)
                            }

                    response_data = {
                        "success": "True",
                        "message": result.get("message", "User switched successfully"),
                        "user_id": user_id,
                        "restart_containers": restart_containers,
                        "restart_system": restart_system
                    }

                    if system_restart_result:
                        response_data["system_restart"] = system_restart_result

                    return jsonify(response_data)
                else:
                    logger.warning(f"Failed to switch user via API: {result.get('error', 'Unknown error')}")
                    return jsonify({"success": "False", "error": result.get("error", "Failed to switch user")}), 400

            except Exception as e:
                logger.error(f"Error switching user via API: {e}")
                return jsonify({"success": "False", "error": str(e)}), 500

        # Discovery endpoint for finding the actual API port
        @self.app.route("/api/v1/discovery", methods=["GET"])
        def discovery():
            """Discovery endpoint to find API server information."""
            try:
                return jsonify({
                    "service": "personal-agent-api",
                    "version": "1.0.0",
                    "port": self.port,
                    "host": self.host,
                    "base_url": f"http://{self.host}:{self.port}",
                    "endpoints": {
                        "health": "/api/v1/health",
                        "status": "/api/v1/status",
                        "discovery": "/api/v1/discovery",
                        "memory": {
                            "store": "/api/v1/memory/store",
                            "store_url": "/api/v1/memory/store-url",
                            "search": "/api/v1/memory/search",
                            "list": "/api/v1/memory/list",
                            "stats": "/api/v1/memory/stats"
                        },
                        "knowledge": {
                            "store_text": "/api/v1/knowledge/store-text",
                            "store_url": "/api/v1/knowledge/store-url",
                            "search": "/api/v1/knowledge/search",
                            "status": "/api/v1/knowledge/status"
                        },
                        "users": {
                            "list": "/api/v1/users",
                            "switch": "/api/v1/users/switch"
                        },
                        "system": {
                            "restart": "/api/v1/system/restart"
                        }
                    }
                })
            except Exception as e:
                logger.error(f"Error in discovery endpoint: {e}")
                return jsonify({"error": str(e)}), 500

        # System endpoints
        @self.app.route("/api/v1/system/restart", methods=["POST"])
        def restart_system():
            try:
                logger.info("System restart requested via REST API")

                # Parse request data for optional parameters
                data = request.get_json() if request.is_json else {}
                restart_lightrag = data.get("restart_lightrag", True)  # Default to True

                # Create restart marker file to trigger page refresh in Streamlit apps
                import tempfile
                marker_file = os.path.join(tempfile.gettempdir(), "personal_agent_restart_marker")
                with open(marker_file, "w") as f:
                    f.write(str(time.time()))

                # Get current configuration from global state or environment
                global_state = get_global_state()
                current_agent_mode = global_state.get("agent_mode", "single")

                # Get model and URL from global state or environment
                current_model = global_state.get("llm_model", os.getenv("LLM_MODEL", "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:q8_0"))
                current_ollama_url = global_state.get("ollama_url", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))

                # Restart LightRAG services if requested
                lightrag_result = None
                if restart_lightrag:
                    try:
                        logger.info("Restarting LightRAG services...")
                        from ..core.lightrag_manager import LightRAGManager
                        from ..config.user_id_mgr import get_userid
                        
                        lightrag_manager = LightRAGManager()
                        current_user = get_userid()
                        lightrag_result = lightrag_manager.restart_lightrag_services(current_user)
                        
                        if lightrag_result.get("success"):
                            logger.info(f"LightRAG services restarted successfully: {lightrag_result.get('services_restarted', [])}")
                        else:
                            logger.warning(f"LightRAG restart had issues: {lightrag_result.get('errors', [])}")
                    except Exception as e:
                        logger.error(f"Error restarting LightRAG services: {e}")
                        lightrag_result = {
                            "success": False,
                            "errors": [str(e)]
                        }

                # Clear global state
                logger.info("Clearing global state for restart")
                global_state.clear()

                # Reinitialize based on agent mode
                success = False
                message = ""

                if current_agent_mode == "team":
                    # Team mode restart
                    logger.info("Restarting in team mode")
                    try:
                        # Import team initialization function
                        from .streamlit_agent_manager import initialize_team

                        # Initialize team
                        team = initialize_team(current_model, current_ollama_url, recreate=True)

                        if team:
                            # Update global state with team
                            global_state.set("agent_mode", "team")
                            global_state.set("team", team)
                            global_state.set("llm_model", current_model)
                            global_state.set("ollama_url", current_ollama_url)

                            # Create memory and knowledge helpers
                            from .streamlit_helpers import StreamlitMemoryHelper, StreamlitKnowledgeHelper

                            if hasattr(team, "members") and team.members:
                                knowledge_agent = team.members[0]  # First member is knowledge agent
                                memory_helper = StreamlitMemoryHelper(knowledge_agent)
                                knowledge_helper = StreamlitKnowledgeHelper(knowledge_agent)

                                global_state.set("memory_helper", memory_helper)
                                global_state.set("knowledge_helper", knowledge_helper)

                            success = True
                            message = "System restarted successfully in team mode"
                            logger.info(message)
                        else:
                            message = "Failed to initialize team during restart"
                            logger.error(message)

                    except Exception as e:
                        message = f"Error restarting team: {str(e)}"
                        logger.error(message)

                else:
                    # Single agent mode restart (default)
                    logger.info("Restarting in single agent mode")
                    try:
                        # Import agent initialization function
                        from .streamlit_agent_manager import initialize_agent

                        # Initialize agent
                        agent = initialize_agent(current_model, current_ollama_url, recreate=True)

                        if agent:
                            # Update global state with agent
                            global_state.set("agent_mode", "single")
                            global_state.set("agent", agent)
                            global_state.set("llm_model", current_model)
                            global_state.set("ollama_url", current_ollama_url)

                            # Create memory and knowledge helpers
                            from .streamlit_helpers import StreamlitMemoryHelper, StreamlitKnowledgeHelper

                            memory_helper = StreamlitMemoryHelper(agent)
                            knowledge_helper = StreamlitKnowledgeHelper(agent)

                            global_state.set("memory_helper", memory_helper)
                            global_state.set("knowledge_helper", knowledge_helper)

                            success = True
                            message = "System restarted successfully in single agent mode"
                            logger.info(message)
                        else:
                            message = "Failed to initialize agent during restart"
                            logger.error(message)

                    except Exception as e:
                        message = f"Error restarting agent: {str(e)}"
                        logger.error(message)

                if success:
                    response_data = {
                        "success": "True",
                        "message": message,
                        "agent_mode": current_agent_mode,
                        "model": current_model,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Include LightRAG restart results if performed
                    if lightrag_result:
                        response_data["lightrag_restart"] = {
                            "performed": True,
                            "success": lightrag_result.get("success", False),
                            "services_restarted": lightrag_result.get("services_restarted", []),
                            "errors": lightrag_result.get("errors", [])
                        }
                    
                    return jsonify(response_data)
                else:
                    response_data = {
                        "success": "False",
                        "error": message,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Include LightRAG restart results even on failure
                    if lightrag_result:
                        response_data["lightrag_restart"] = {
                            "performed": True,
                            "success": lightrag_result.get("success", False),
                            "services_restarted": lightrag_result.get("services_restarted", []),
                            "errors": lightrag_result.get("errors", [])
                        }
                    
                    return jsonify(response_data), 500

            except Exception as e:
                logger.error(f"Error during system restart via API: {e}")
                return jsonify({
                    "success": "False",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500

    def _get_memory_helper(self):
        """Get memory helper from global state."""
        global_state = get_global_state()
        return global_state.get("memory_helper")

    def _get_knowledge_helper(self):
        """Get knowledge helper from global state."""
        global_state = get_global_state()
        return global_state.get("knowledge_helper")

    def _get_agent(self):
        """Get agent from global state (single or team mode)."""
        global_state = get_global_state()
        agent_mode = global_state.get("agent_mode", "single")

        if agent_mode == "team":
            # Team mode - get the knowledge agent (first team member)
            team = global_state.get("team")
            if team and hasattr(team, "members") and team.members:
                return team.members[0]
        else:
            # Single agent mode
            return global_state.get("agent")

        return None

    def _get_knowledge_tools(self, agent):
        """Get knowledge tools from agent."""
        if (
            not agent
            or not hasattr(agent, "agent")
            or not hasattr(agent.agent, "tools")
        ):
            return None

        # Find knowledge tools
        for tool in agent.agent.tools:
            if hasattr(tool, "__class__") and "KnowledgeTools" in str(tool.__class__):
                return tool

        return None

    def _extract_url_content(self, url: str, method: str = "full_text") -> tuple:
        """Extract content from URL."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()

        if "text/html" in content_type:
            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get title
            title_tag = soup.find("title")
            title = title_tag.get_text().strip() if title_tag else ""

            # Get text content
            content = soup.get_text()

            # Clean up content
            content = "\n".join(
                line.strip() for line in content.splitlines() if line.strip()
            )

            return content, title

        elif "text/" in content_type or "application/json" in content_type:
            return response.text, ""
        else:
            raise ValueError(f"Unsupported content type: {content_type}")

    def start(self):
        """Start the REST API server in a background thread."""
        if self._running:
            logger.warning("REST API server is already running")
            return

        def run_server():
            try:
                logger.info(f"Starting REST API server on {self.host}:{self.port}")
                self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
            except Exception as e:
                logger.error(f"Error starting REST API server: {e}")

        self._server_thread = threading.Thread(target=run_server, daemon=True)
        self._server_thread.start()
        self._running = True

        # Give server time to start
        time.sleep(1)
        logger.info(f"REST API server started at http://{self.host}:{self.port}")

    def stop(self):
        """Stop the REST API server."""
        if not self._running:
            return

        self._running = False
        logger.info("REST API server stopped")


def start_rest_api(streamlit_session, port: int = 8002, host: str = "0.0.0.0"):
    """Start the REST API server with Streamlit session reference."""
    import socket

    def is_port_available(port, host="0.0.0.0"):
        """Check if a port is available on the given host."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result != 0  # 0 means connection successful (port in use)
        except Exception:
            return False

    def find_available_port(start_port, host="0.0.0.0", max_attempts=10):
        """Find an available port starting from start_port."""
        for port in range(start_port, start_port + max_attempts):
            if is_port_available(port, host):
                return port
        return None

    # Try the requested port first
    if is_port_available(port, host):
        actual_port = port
        logger.info(f"Starting REST API server on {host}:{actual_port}")
    else:
        logger.warning(f"Port {port} is already in use on {host}, searching for available port...")
        available_port = find_available_port(port + 1, host)
        if available_port:
            actual_port = available_port
            logger.info(f"Found available port {actual_port}, starting REST API server on {host}:{actual_port}")
        else:
            logger.error(f"Could not find an available port starting from {port}")
            raise RuntimeError(f"No available ports found starting from {port}")

    # Start the API server
    api = PersonalAgentRestAPI(port=actual_port, host=host)
    api.set_streamlit_session(streamlit_session)
    api.start()

    # Store the actual port in global state for discovery
    try:
        from .global_state import get_global_state
        global_state = get_global_state()
        global_state.set("rest_api_port", actual_port)
        global_state.set("rest_api_host", host)
    except Exception as e:
        logger.warning(f"Could not store API port in global state: {e}")

    return api


if __name__ == "__main__":
    """Run the REST API server directly."""
    import argparse
    import sys
    from pathlib import Path

    # Add src to path for imports when running directly
    project_root = Path(__file__).parent.parent.parent
    src_path = project_root / "src"
    if src_path not in sys.path:
        sys.path.insert(0, str(src_path))

    # Re-import with proper path setup
    try:
        from personal_agent.tools.global_state import get_global_state
        from personal_agent.utils import setup_logging

        logger = setup_logging(__name__)
    except ImportError:
        # Fallback if absolute imports also fail
        import logging

        logger = logging.getLogger(__name__)
        print("Warning: Using fallback logging - some features may not work")

    parser = argparse.ArgumentParser(description="Personal Agent REST API Server")
    parser.add_argument(
        "--port", type=int, default=8002, help="Port to run the server on"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Starting REST API server on {args.host}:{args.port}")

    # Create and start the API server
    api = PersonalAgentRestAPI(port=args.port, host=args.host)
    api.start()

    # Keep the server running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down REST API server...")
        api.stop()
