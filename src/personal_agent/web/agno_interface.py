# -*- coding: utf-8 -*-
# pylint: disable=C0302, W0603, C0103, C0301
"""
Web interface module for the Personal AI Agent using agno framework.

This module provides a Flask-based web interface that works with agno agents,
maintaining the same UI and functionality as the original interface.py.
"""

import asyncio
import json
import logging
import queue
import threading
import time
from datetime import datetime
from io import StringIO
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from flask import Flask, Response, render_template_string, request

if TYPE_CHECKING:
    from logging import Logger

    from ..core.agno_agent import AgnoPersonalAgent

# These will be injected by the main module
app: Flask = None
agno_agent: "AgnoPersonalAgent" = None
logger: "Logger" = None

# Memory function references (async functions from agno)
query_knowledge_base_func: Optional[Callable[[str], str]] = None
store_interaction_func: Optional[Callable[[str, str], bool]] = None
clear_knowledge_base_func: Optional[Callable[[], bool]] = None

# Streaming thoughts management
thoughts_queue = queue.Queue()
active_sessions = set()
current_thoughts = {}  # Store only the latest thought per session


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    :return: Configured Flask application
    """
    flask_app = Flask(__name__)
    return flask_app


def add_thought(thought: str, session_id: str = "default"):
    """Add a thought to the streaming queue - only keeps the latest thought per session."""
    thought_data = {
        "session_id": session_id,
        "thought": thought,
        "timestamp": datetime.now().isoformat() + "Z",
    }

    # Store only the latest thought for this session
    current_thoughts[session_id] = thought_data

    # Always add to queue for all active sessions to see
    if active_sessions:
        thoughts_queue.put(thought_data)
        if logger:
            logger.info(f"Added latest thought for session {session_id}: {thought}")
    else:
        if logger:
            logger.info(
                f"Stored latest thought for inactive session {session_id}: {thought}"
            )

    # Always add to queue for all active sessions to see
    if active_sessions:
        thoughts_queue.put(thought_data)
        if logger:
            logger.info(f"Added latest thought for session {session_id}: {thought}")
    else:
        if logger:
            logger.info(
                f"Stored latest thought for inactive session {session_id}: {thought}"
            )


def stream_thoughts(session_id: str = "default"):
    """Generator for streaming thoughts - sends only the latest thought per session."""
    active_sessions.add(session_id)
    if logger:
        logger.debug(f"Started streaming for session: {session_id}")

    try:
        # Send initial connection confirmation
        yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"

        # Send the current latest thought if one exists for this session
        if session_id in current_thoughts:
            thought_data = current_thoughts[session_id]
            if logger:
                logger.debug(
                    f"Sending current thought for {session_id}: {thought_data['thought']}"
                )
            yield f"data: {json.dumps(thought_data)}\n\n"

        while session_id in active_sessions:
            try:
                # Check for new thoughts - broadcast all thoughts to all active connections
                thought_data = thoughts_queue.get(timeout=1.0)
                if logger:
                    logger.debug(
                        f"Broadcasting thought from {thought_data['session_id']} to session {session_id}: {thought_data['thought']}"
                    )
                yield f"data: {json.dumps(thought_data)}\n\n"
            except queue.Empty:
                # Send keep-alive
                yield f"data: {json.dumps({'type': 'keep-alive'})}\n\n"
    finally:
        active_sessions.discard(session_id)
        if logger:
            logger.debug(f"Stopped streaming for session: {session_id}")


def register_routes(
    flask_app: Flask,
    agent: "AgnoPersonalAgent",
    log: "Logger",
    query_kb_func: Callable[[str], str],
    store_int_func: Callable[[str, str], bool],
    clear_kb_func: Callable[[], bool],
):
    """
    Register Flask routes with the agno agent.

    :param flask_app: Flask application instance
    :param agent: Agno agent instance
    :param log: Logger instance
    :param query_kb_func: Function to query knowledge base (async)
    :param store_int_func: Function to store interactions (async)
    :param clear_kb_func: Function to clear knowledge base (async)
    """
    global app, agno_agent, logger, query_knowledge_base_func, store_interaction_func, clear_knowledge_base_func

    app = flask_app
    agno_agent = agent
    logger = log
    query_knowledge_base_func = query_kb_func
    store_interaction_func = store_int_func
    clear_knowledge_base_func = clear_kb_func

    logger.info("Starting route registration for agno interface")

    # Add initial system ready thought
    add_thought("🟢 Agno System Ready", "default")
    logger.info("Added initial system ready thought")

    app.add_url_rule("/", "index", index, methods=["GET", "POST"])
    app.add_url_rule("/clear", "clear_kb", clear_kb_route)
    app.add_url_rule("/agent_info", "agent_info", agent_info_route)
    app.add_url_rule("/stream_thoughts", "stream_thoughts", stream_thoughts_route)

    logger.info("All agno interface routes registered successfully")


def run_async_in_thread(coroutine):
    """Helper function to run async functions in a thread with a new event loop."""

    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coroutine)
        finally:
            loop.close()

    result_container = {"result": None, "error": None, "done": False}

    def worker():
        try:
            result_container["result"] = thread_target()
        except Exception as e:
            result_container["error"] = e
        finally:
            result_container["done"] = True

    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    thread.join(timeout=60)  # 60 second timeout

    if result_container["error"]:
        raise result_container["error"]

    if not result_container["done"]:
        raise TimeoutError("Async operation timed out")

    return result_container["result"]


def parse_agent_response(response_text):
    """
    Parse agent response to separate thinking process from actual response.

    :param response_text: Raw agent response that may contain thinking tags
    :return: dict with 'thinking' and 'response' content
    """
    if not response_text or not isinstance(response_text, str):
        return {"thinking": "", "response": response_text or ""}

    thinking_content = ""
    actual_response = response_text

    # Look for various thinking patterns and extract them
    import re

    # Pattern 1: <thinking>...</thinking> tags
    thinking_pattern = r"<thinking>(.*?)</thinking>"
    thinking_matches = re.findall(
        thinking_pattern, response_text, re.DOTALL | re.IGNORECASE
    )
    if thinking_matches:
        thinking_content = "\n".join(thinking_matches).strip()
        # Remove thinking blocks from the actual response
        actual_response = re.sub(
            thinking_pattern, "", response_text, flags=re.DOTALL | re.IGNORECASE
        )

    # Pattern 2: Look for content after </thinking> tags
    if "</thinking>" in response_text.lower():
        parts = response_text.split("</thinking>")
        if len(parts) > 1:
            # Everything after the last </thinking> tag is the response
            actual_response = parts[-1].strip()
            # Everything before and including thinking tags is thinking content
            thinking_part = "</thinking>".join(parts[:-1])
            if thinking_part:
                # Extract just the thinking content without tags
                thinking_matches = re.findall(
                    r"<thinking>(.*?)(?=</thinking>|$)",
                    thinking_part,
                    re.DOTALL | re.IGNORECASE,
                )
                if thinking_matches:
                    thinking_content = "\n".join(thinking_matches).strip()

    # Pattern 3: Look for <response>...</response> tags for the actual response
    response_pattern = r"<response>(.*?)</response>"
    response_matches = re.findall(
        response_pattern, actual_response, re.DOTALL | re.IGNORECASE
    )
    if response_matches:
        actual_response = "\n".join(response_matches).strip()

    # Clean up the actual response
    actual_response = actual_response.strip()

    # Remove any remaining XML-like tags
    actual_response = re.sub(
        r"</?(?:thinking|response)>", "", actual_response, flags=re.IGNORECASE
    )
    actual_response = actual_response.strip()

    # If we couldn't extract any clear response content, use the original
    if not actual_response:
        actual_response = response_text
        thinking_content = ""

    return {"thinking": thinking_content, "response": actual_response}


def index():
    """
    Main route for the agent interface using agno framework.

    :return: Rendered HTML template
    """
    if logger:
        logger.info(f"Index route accessed - method: {request.method}")

    response = None
    context = None
    agent_thoughts = []
    tool_calls = []

    # Get agent information for display
    agent_info = agno_agent.get_agent_info() if agno_agent else {}

    # Get status of associated agents/services
    agents = [
        {
            "name": "Personal AI Agent",
            "status": "Active" if agent_info.get("initialized", False) else "Inactive",
            "type": "Primary",
            "icon": "robot",
        },
        {
            "name": "Knowledge Base",
            "status": (
                "Connected"
                if agent_info.get("knowledge_enabled", False)
                else "Disconnected"
            ),
            "type": "Service",
            "icon": "database",
        },
        {
            "name": "MCP Tools",
            "status": "Active" if agent_info.get("mcp_enabled", False) else "Inactive",
            "count": agent_info.get("mcp_servers", 0),
            "type": "Service",
            "icon": "plug",
        },
        {
            "name": f"{agent_info.get('model_provider', 'LLM').title()} Model",
            "status": "Connected",
            "type": "Model",
            "model": agent_info.get("model_name", "Unknown"),
            "icon": "brain",
        },
    ]

    if request.method == "POST":
        user_input = request.form.get("query", "")
        topic = request.form.get("topic", "general")
        session_id = request.form.get("session_id", "default")

        if logger:
            logger.info(
                f"POST request received - user_input: '{user_input[:100]}{'...' if len(user_input) > 100 else ''}', session_id: {session_id}"
            )

        if user_input:
            # Clear any existing thoughts for this session from the queue
            temp_queue = queue.Queue()
            while not thoughts_queue.empty():
                try:
                    item = thoughts_queue.get_nowait()
                    if item["session_id"] != session_id:
                        temp_queue.put(item)
                except queue.Empty:
                    break

            # Put back non-matching items
            while not temp_queue.empty():
                try:
                    thoughts_queue.put(temp_queue.get_nowait())
                except queue.Empty:
                    break

            # Start streaming thoughts
            add_thought("🤔 Thinking about your request...", session_id)
            add_thought("🧠 Agno agent processing with automatic memory", session_id)

            try:
                # Agno handles memory automatically - no manual context retrieval needed
                context = None  # Let Agno handle memory internally

                if logger:
                    logger.info(
                        "Starting agno agent processing with CLI-style direct query"
                    )

                # Add processing thoughts
                add_thought("🧠 Analyzing request with agno reasoning", session_id)
                add_thought("🔧 Preparing MCP tools and capabilities", session_id)
                add_thought("⚡ Processing with agno framework", session_id)

                # Execute agno agent in a separate thread for real-time thoughts
                try:
                    if logger:
                        logger.info("Starting agno agent execution in separate thread")

                    # Add more detailed processing thoughts
                    add_thought("🔍 Examining available MCP tools", session_id)
                    add_thought("📊 Processing with async capabilities", session_id)
                    add_thought("💡 Formulating response strategy", session_id)
                    add_thought("🎯 Executing with agno agent", session_id)

                    # Container for the response and any error from the thread
                    result_container = {"response": None, "error": None, "done": False}

                    def agent_worker():
                        """Worker function to run agno agent in separate thread."""
                        try:
                            if logger:
                                logger.info("Agent worker thread started")

                            # Add periodic thoughts during processing
                            add_thought("🤖 Agno agent is processing...", session_id)
                            time.sleep(0.5)  # Small delay to show the thought

                            add_thought("🔧 Analyzing with MCP tools", session_id)
                            time.sleep(0.5)

                            # Initialize tool calls and agent thoughts if they're empty
                            nonlocal tool_calls, agent_thoughts
                            if not tool_calls:
                                tool_calls = []
                            if not agent_thoughts:
                                agent_thoughts = []

                            # Add initial thinking entry
                            agent_thoughts.append("🧠 Starting agent reasoning process")

                            # Since Agno handles memory internally, we don't need to pass context
                            # Skip creating a context string and let the agent use its own knowledge base
                            if logger:
                                logger.info(
                                    "Using direct query approach like CLI mode - Agno will use its knowledge base automatically"
                                )

                            # Using the same simple approach as CLI mode - directly pass the user's query
                            query = user_input

                            # Use agno agent with async execution and thought callback
                            if logger:
                                logger.info(
                                    "Creating new event loop for agno agent execution"
                                )

                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                # Create thought callback for this session and tool capture
                                def thought_callback(thought: str):
                                    # Declare all nonlocal variables at the top
                                    nonlocal tool_calls, agent_thoughts

                                    # Enhanced tool call detection patterns
                                    tool_indicators = [
                                        "search_knowledge",
                                        "github",
                                        "brave_search",
                                        "filesystem",
                                        "duckduckgo",
                                        "puppeteer",
                                        "mcp_",
                                        "tool:",
                                        "Tool:",
                                        "using tool",
                                        "calling",
                                        "invoke",
                                        "execute",
                                    ]

                                    # Check for various tool call patterns
                                    is_tool_call = False
                                    tool_name = ""
                                    params_text = ""

                                    # Pattern 1: function_name(param=value, param2=value2)
                                    if (
                                        "(" in thought
                                        and "=" in thought
                                        and ")" in thought
                                    ):
                                        for indicator in tool_indicators:
                                            if indicator in thought.lower():
                                                tool_name = thought.split("(")[
                                                    0
                                                ].strip()
                                                params_text = thought.split("(")[
                                                    1
                                                ].split(")")[0]
                                                is_tool_call = True
                                                break

                                    # Pattern 2: "Using tool: tool_name" or "Calling tool_name"
                                    elif any(
                                        phrase in thought.lower()
                                        for phrase in [
                                            "using tool",
                                            "calling",
                                            "invoke",
                                            "execute",
                                        ]
                                    ):
                                        # Extract tool name after the action word
                                        for phrase in [
                                            "using tool:",
                                            "calling",
                                            "invoke",
                                            "execute",
                                        ]:
                                            if phrase in thought.lower():
                                                tool_name = (
                                                    thought.lower()
                                                    .split(phrase)[-1]
                                                    .strip()
                                                )
                                                is_tool_call = True
                                                break

                                    # Pattern 3: Look for MCP server names or specific tool names
                                    elif any(
                                        indicator in thought.lower()
                                        for indicator in tool_indicators
                                    ):
                                        tool_name = thought.strip()
                                        is_tool_call = True

                                    if is_tool_call and tool_name:
                                        tool_calls.append(
                                            {
                                                "name": tool_name,
                                                "parameters": params_text,
                                                "timestamp": datetime.now().isoformat(),
                                            }
                                        )

                                        # Also add to agent thoughts for visibility
                                        agent_thoughts.append(
                                            f"🔧 Using tool: {tool_name}"
                                        )

                                        if logger:
                                            logger.info(
                                                f"Detected tool call: {tool_name}({params_text})"
                                            )

                                    # Handle <think> blocks for thinking display
                                    if "<think>" in thought and "</think>" in thought:
                                        # Extract thinking content
                                        thinking_text = (
                                            thought.split("<think>")[1]
                                            .split("</think>")[0]
                                            .strip()
                                        )
                                        if thinking_text:
                                            agent_thoughts.append(f"🤔 {thinking_text}")

                                        if logger:
                                            logger.info(
                                                f"Detected thinking: {thinking_text}"
                                            )

                                    # General reasoning detection (only if not already captured as tool or thinking)
                                    elif not is_tool_call and any(
                                        x in thought.lower()
                                        for x in [
                                            "reasoning",
                                            "thinking",
                                            "considering",
                                            "analyzing",
                                            "planning",
                                            "strategy",
                                        ]
                                    ):
                                        agent_thoughts.append(f"� {thought}")

                                        if logger:
                                            logger.info(
                                                f"Detected reasoning: {thought}"
                                            )

                                    # Always add the thought to the stream
                                    add_thought(thought, session_id)

                                if logger:
                                    logger.info(
                                        "Starting agno agent run with direct query (CLI-style)"
                                    )

                                agent_response = loop.run_until_complete(
                                    agno_agent.run(
                                        query,
                                        add_thought_callback=thought_callback,
                                    )
                                )
                                result_container["response"] = agent_response

                                if logger:
                                    logger.info(
                                        f"Agno agent completed successfully - response length: {len(str(agent_response))}"
                                    )

                                add_thought(
                                    "✨ Response generated successfully", session_id
                                )
                            finally:
                                loop.close()
                                if logger:
                                    logger.info(
                                        "Event loop closed after agno agent execution"
                                    )

                        except Exception as e:
                            result_container["error"] = e
                            if logger:
                                logger.error(
                                    f"Error during agno agent processing: {str(e)}"
                                )
                            add_thought(
                                f"❌ Error during processing: {str(e)}", session_id
                            )
                        finally:
                            result_container["done"] = True
                            # Add final completion thought
                            add_thought("✅ Processing complete", session_id)

                    # Start the agent in a separate thread
                    agent_thread = threading.Thread(target=agent_worker)
                    agent_thread.daemon = True
                    agent_thread.start()

                    # Add progressive thoughts while waiting
                    thought_counter = 0
                    progress_thoughts = [
                        "🧠 Deep thinking with agno...",
                        "🔍 Exploring MCP capabilities...",
                        "📝 Gathering relevant information...",
                        "⚙️ Processing with async reasoning...",
                        "🎯 Refining the approach...",
                        "💭 Almost there...",
                    ]

                    # Wait for the agent to complete, adding thoughts periodically
                    if logger:
                        logger.info(
                            "Waiting for agent thread to complete with periodic progress thoughts"
                        )

                    while not result_container["done"]:
                        time.sleep(2.0)  # Wait 2 seconds between thoughts
                        if not result_container["done"] and thought_counter < len(
                            progress_thoughts
                        ):
                            add_thought(progress_thoughts[thought_counter], session_id)
                            thought_counter += 1

                    # Wait for thread to complete and get the result
                    if logger:
                        logger.info(
                            "Agent thread marked as done, waiting for join with 60s timeout"
                        )

                    agent_thread.join(timeout=60)  # Max 60 seconds wait

                    error = result_container.get("error")
                    if error is not None:
                        if logger:
                            logger.error(f"Agent thread returned error: {error}")
                        if isinstance(error, Exception):
                            raise error
                        else:
                            raise RuntimeError(f"Agno agent execution failed: {error}")

                    response = result_container.get("response")
                    if response is None:
                        if logger:
                            logger.error(
                                "Agent thread completed but returned no response"
                            )
                        raise RuntimeError(
                            "Agno agent execution timed out or returned no response"
                        )

                    if logger:
                        logger.info(
                            f"Successfully received response from agent thread - length: {len(str(response))}"
                        )

                    # Store interaction AFTER getting response
                    if store_interaction_func:
                        try:
                            if logger:
                                logger.info(
                                    "Storing interaction in memory using async function"
                                )

                            # Use async function via thread
                            run_async_in_thread(
                                store_interaction_func(user_input, response)
                            )
                            add_thought("💾 Interaction stored in memory", session_id)

                            if logger:
                                logger.info("Interaction successfully stored in memory")

                        except Exception as e:
                            logger.warning("Could not store interaction: %s", e)
                    else:
                        if logger:
                            logger.warning(
                                "No store_interaction_func available - skipping memory storage"
                            )

                except Exception as e:
                    logger.error("Error with agno execution: %s", str(e))
                    response = f"Error processing request: {str(e)}"
                    add_thought(f"❌ Error occurred: {str(e)}", session_id)

            except Exception as e:
                logger.error("Error processing query: %s", str(e))
                response = f"Error processing query: {str(e)}"
                add_thought(f"❌ Error occurred: {str(e)}", session_id)

            if logger:
                logger.info(
                    f"Request processing completed - user_input: '{user_input[:50]}...', response_length: {len(str(response)) if response else 0}"
                )

            logger.debug(
                "Received query: %s..., Response: %s...",
                user_input[:50],
                str(response)[:50] if response else "None",
            )

            # Reset thought status to Ready after processing is complete
            add_thought("Ready", session_id)

    # Parse response to separate thinking from actual response
    actual_response = response
    thinking_content = None

    if response:
        # Additional tool call detection from response text
        response_lines = response.split("\n")
        for line in response_lines:
            line = line.strip()
            # Look for tool usage patterns in the response
            tool_patterns = [
                "search_knowledge",
                "github",
                "brave_search",
                "filesystem",
                "puppeteer",
                "Using tool:",
                "Tool used:",
                "Calling",
                "Executing",
            ]

            for pattern in tool_patterns:
                if pattern.lower() in line.lower():
                    # Extract tool name
                    if "(" in line and ")" in line:
                        tool_name = line.split("(")[0].strip()
                        params = line.split("(")[1].split(")")[0]
                    else:
                        tool_name = line.strip()
                        params = ""

                    # Check if this tool call is already captured
                    if not any(
                        tc["name"].lower() == tool_name.lower() for tc in tool_calls
                    ):
                        tool_calls.append(
                            {
                                "name": tool_name,
                                "parameters": params,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        if logger:
                            logger.info(
                                f"Additional tool call detected from response: {tool_name}"
                            )
                    break

        # Try to extract thinking content and actual response
        if "<thinking>" in response and "</thinking>" in response:
            # Extract thinking content
            thinking_start = response.find("<thinking>")
            thinking_end = response.find("</thinking>") + len("</thinking>")
            thinking_content = response[thinking_start:thinking_end]

            # Remove thinking tags and extract content
            thinking_text = response[
                thinking_start + len("<thinking>") : thinking_end - len("</thinking>")
            ].strip()

            # Remove thinking section from actual response
            actual_response = response[:thinking_start] + response[thinking_end:]
            actual_response = actual_response.strip()

            # Add extracted thinking to agent thoughts if not empty
            if thinking_text:
                agent_thoughts.append(f"🤔 Extracted: {thinking_text}")

        elif "<think>" in response and "</think>" in response:
            # Alternative thinking tag format
            thinking_start = response.find("<think>")
            thinking_end = response.find("</think>") + len("</think>")
            thinking_content = response[thinking_start:thinking_end]

            # Remove thinking tags and extract content
            thinking_text = response[
                thinking_start + len("<think>") : thinking_end - len("</think>")
            ].strip()

            # Remove thinking section from actual response
            actual_response = response[:thinking_start] + response[thinking_end:]
            actual_response = actual_response.strip()

            # Add extracted thinking to agent thoughts if not empty
            if thinking_text:
                agent_thoughts.append(f"🤔 Extracted: {thinking_text}")

        # Look for response tags to extract clean response
        if "<response>" in actual_response and "</response>" in actual_response:
            response_start = actual_response.find("<response>")
            response_end = actual_response.find("</response>") + len("</response>")
            actual_response = actual_response[
                response_start + len("<response>") : response_end - len("</response>")
            ].strip()

        # If actual response is empty or just whitespace, use original response
        if not actual_response or actual_response.isspace():
            actual_response = response

    return render_template_string(
        get_main_template(),
        response=actual_response,
        thinking_response=thinking_content,
        context=context,
        agent_thoughts=agent_thoughts,
        is_multi_agent=True,  # agno supports multiple capabilities
        knowledge_connected=agent_info.get("knowledge_enabled", False),
        agents=agents,
        agent_info=agent_info,
        tool_calls=tool_calls,
    )


def clear_kb_route():
    """Route to clear the knowledge base."""
    if logger:
        logger.info("Clear knowledge base route accessed")

    try:
        if clear_knowledge_base_func:
            if logger:
                logger.info("Executing clear knowledge base function")
            result = run_async_in_thread(clear_knowledge_base_func())
        else:
            if logger:
                logger.warning("Clear knowledge base function not available")
            result = "Clear function not available"

        logger.info("Knowledge base cleared via web interface: %s", result)
        return render_template_string(
            get_success_template(),
            result=result,
        )
    except Exception as e:
        logger.error("Error clearing knowledge base via web interface: %s", str(e))
        return render_template_string(
            get_error_template(),
            error=str(e),
        )


def agent_info_route():
    """Route for displaying agent information."""
    if logger:
        logger.info("Agent info route accessed")

    # Get agent info from agno agent
    agent_type = "Agno Framework Agent"
    agent_info = agno_agent.get_agent_info() if agno_agent else {}

    if logger:
        logger.info(f"Retrieved agent info: {agent_info}")

    # Get available tools from the agno agent
    available_tools = []
    if agno_agent:
        try:
            # Extract tool names from agent info
            mcp_servers = agent_info.get("mcp_servers", 0)
            available_tools.append(f"MCP Servers: {mcp_servers}")

            if agent_info.get("knowledge_enabled"):
                available_tools.append("Knowledge Base")

            available_tools.extend(
                ["Async Processing", "Multi-tool Coordination", "Context Enhancement"]
            )

            if logger:
                logger.info(f"Available tools compiled: {available_tools}")

        except Exception as e:
            logger.warning("Could not get tool info: %s", e)

    return render_template_string(
        get_agent_info_template(),
        agent_type=agent_type,
        agent_info=agent_info,
        available_tools=available_tools,
        fallback_agent=None,
    )


def stream_thoughts_route():
    """Route for streaming thoughts."""
    session_id = request.args.get("session_id", "default")

    if logger:
        logger.info(f"Stream thoughts route accessed for session: {session_id}")

    return Response(stream_thoughts(session_id), content_type="text/event-stream")


def clean_response_for_display(response_text):
    """Clean the response text for better display."""
    if not response_text:
        return ""

    # Convert response to string if it's not already
    if not isinstance(response_text, str):
        response_text = str(response_text)

    # Basic cleaning
    cleaned_response = response_text.strip()

    # Remove leading whitespace from each line to prevent indentation issues
    lines = cleaned_response.split("\n")
    cleaned_lines = [line.lstrip() for line in lines]
    cleaned_response = "\n".join(cleaned_lines)

    return cleaned_response


def get_main_template():
    """
    Get the main HTML template for the interface.

    :return: HTML template string
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Personal AI Agent - Agno Framework</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --primary-color: #2563eb;
                --primary-dark: #1d4ed8;
                --success-color: #059669;
                --warning-color: #f59e0b;
                --danger-color: #dc2626;
                --background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --surface: #ffffff;
                --surface-alt: #f8fafc;
                --text-primary: #1e293b;
                --text-secondary: #64748b;
                --border-color: #e2e8f0;
                --shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                --shadow-lg: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                --brain-connected: #10b981;
                --brain-disconnected: #ef4444;
                --status-connected: #10b981;
                --status-disconnected: #ef4444;
                --status-pending: #f59e0b;
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: var(--background);
                color: var(--text-primary);
                line-height: 1.6;
                min-height: 100vh;
                padding-top: 60px;
            }

            .status-bar {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                padding: 0.75rem 1rem;
                border-bottom: 1px solid var(--border-color);
                z-index: 1000;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 0.875rem;
            }

            .status-left {
                display: flex;
                align-items: center;
                gap: 1rem;
            }

            .status-item {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--text-secondary);
                padding: 0.25rem 0.5rem;
                border-radius: 0.5rem;
                background: rgba(0, 0, 0, 0.03);
                border: 1px solid rgba(0, 0, 0, 0.05);
            }

            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: var(--success-color);
                animation: pulse 2s infinite;
            }

            .status-indicator.connected {
                background: var(--status-connected);
            }

            .status-indicator.disconnected {
                background: var(--status-disconnected);
            }

            .status-indicator.pending {
                background: var(--status-pending);
            }

            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }

            .status-right {
                display: flex;
                align-items: center;
                gap: 1rem;
            }

            .nav-button {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem 1rem;
                background: transparent;
                border: 1px solid var(--border-color);
                border-radius: 0.5rem;
                color: var(--text-secondary);
                text-decoration: none;
                transition: all 0.2s;
                font-size: 0.875rem;
            }

            .nav-button:hover {
                background: var(--primary-color);
                color: white;
                border-color: var(--primary-color);
                transform: translateY(-1px);
            }

            .container {
                width: 100%;
                max-width: 1400px;
                margin: 0 auto;
                padding: 2rem;
                display: grid;
                grid-template-columns: 1fr minmax(300px, 350px);
                grid-gap: 2rem;
                align-items: start;
            }

            .main-content {
                grid-column: 1;
            }

            .sidebar {
                grid-column: 2;
                background: var(--surface);
                border-radius: 1rem;
                box-shadow: var(--shadow);
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 1.5rem;
                height: fit-content;
                position: sticky;
                top: 80px;
            }

            .sidebar-title {
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--primary-color);
            }

            .agent-list {
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
            }

            .agent-item {
                display: flex;
                align-items: center;
                padding: 0.75rem;
                background: var(--surface-alt);
                border-radius: 0.5rem;
                border-left: 3px solid var(--primary-color);
                font-size: 0.875rem;
            }

            .agent-icon {
                margin-right: 0.75rem;
                color: var(--primary-color);
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(37, 99, 235, 0.1);
                border-radius: 50%;
                padding: 4px;
            }

            .agent-details {
                flex: 1;
            }

            .agent-name {
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 0.25rem;
            }

            .agent-status {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--text-secondary);
                font-size: 0.75rem;
            }

            .header {
                text-align: center;
                margin-bottom: 2rem;
                color: white;
            }

            .header h1 {
                font-size: 3rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 1rem;
            }

            .header-icon {
                background: rgba(255, 255, 255, 0.2);
                padding: 1rem;
                border-radius: 1rem;
                backdrop-filter: blur(10px);
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .header p {
                font-size: 1.2rem;
                opacity: 0.9;
                font-weight: 300;
            }

            .framework-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background: rgba(37, 99, 235, 0.2);
                border: 1px solid rgba(37, 99, 235, 0.3);
                padding: 0.5rem 1rem;
                border-radius: 2rem;
                font-size: 0.875rem;
                font-weight: 500;
                margin-top: 1rem;
                backdrop-filter: blur(10px);
            }

            .content {
                background: var(--surface);
                padding: 2rem;
                border-radius: 1rem;
                box-shadow: var(--shadow);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            .form-container {
                margin-bottom: 2rem;
            }

            .form-group {
                margin-bottom: 1.5rem;
            }

            .form-group label {
                display: block;
                margin-bottom: 0.75rem;
                font-weight: 600;
                color: var(--text-primary);
                font-size: 1rem;
            }

            .form-input {
                width: 100%;
                padding: 1rem;
                border: 2px solid var(--border-color);
                border-radius: 0.75rem;
                font-size: 1rem;
                transition: all 0.2s;
                background: var(--surface-alt);
            }

            .form-input:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
            }

            .form-textarea {
                min-height: 120px;
                resize: vertical;
            }

            .submit-button {
                background: var(--primary-color);
                color: white;
                border: none;
                padding: 1rem 2rem;
                border-radius: 0.75rem;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin: 0 auto;
            }

            .submit-button:hover {
                background: var (--primary-dark);
                transform: translateY(-2px);
                box-shadow: var(--shadow);
            }

            .submit-button:active {
                transform: translateY(0);
            }

            .response-section {
                margin-top: 2rem;
                padding: 2rem;
                background: var(--surface-alt);
                border-radius: 1rem;
                border-left: 4px solid var(--primary-color);
            }

            .response-header {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                margin-bottom: 1rem;
                font-weight: 600;
                color: var(--text-primary);
            }

            .response-content {
                color: var(--text-secondary);
                line-height: 1.7;
                white-space: pre-wrap;
                word-wrap: break-word;
                font-size: 1rem;
            }

            .response-content pre,
            .response-content code {
                background-color: rgba(0, 0, 0, 0.05);
                border-radius: 0.5rem;
                padding: 1rem;
                overflow-x: auto;
                font-family: 'Fira Code', 'Courier New', monospace;
                font-size: 0.9rem;
                margin: 1rem 0;
            }

            .response-content code {
                padding: 0.2rem 0.5rem;
                margin: 0;
            }

            /* Thoughts Response Section */
            .thoughts-response-section {
                margin-top: 1.5rem;
                padding: 2rem;
                background: rgba(139, 69, 19, 0.05);
                border-radius: 1rem;
                border-left: 4px solid var(--warning-color);
            }

            .thoughts-response-header {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                margin-bottom: 1rem;
                font-weight: 600;
                color: var(--warning-color);
            }

            .thoughts-response-content {
                color: var(--text-secondary);
                line-height: 1.7;
                white-space: pre-wrap;
                word-wrap: break-word;
                font-size: 0.95rem;
            }

            .thought-line {
                margin-bottom: 0.75rem;
                padding: 0.75rem;
                background: rgba(255, 255, 255, 0.7);
                border-radius: 0.5rem;
                border-left: 3px solid var(--warning-color);
                line-height: 1.6;
                font-size: 0.95rem;
            }

            .thought-line:last-child {
                margin-bottom: 0;
            }

            .no-thoughts {
                font-style: italic;
                color: var(--text-secondary);
                opacity: 0.7;
                text-align: center;
                padding: 1rem;
            }

            .context-section {
                margin-top: 1.5rem;
                padding: 1.5rem;
                background: rgba(37, 99, 235, 0.05);
                border-radius: 0.75rem;
                border: 1px solid rgba(37, 99, 235, 0.1);
            }

            .context-header {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 1rem;
                font-weight: 600;
                color: var (--primary-color);
                font-size: 0.875rem;
            }

            .context-content {
                font-size: 0.875rem;
                color: var(--text-secondary);
                line-height: 1.6;
            }

            .thoughts-panel {
                position: fixed;
                top: 4rem;
                right: 1rem;
                width: 320px;
                max-height: 400px;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-radius: 1rem;
                box-shadow: var(--shadow-lg);
                border: 1px solid var(--border-color);
                overflow: hidden;
                z-index: 999;
                display: none;
            }

            .thoughts-header {
                padding: 1rem;
                background: var(--primary-color);
                color: white;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.875rem;
            }

            .thoughts-content {
                padding: 1rem;
                max-height: 320px;
                overflow-y: auto;
            }

            .thought-item {
                margin-bottom: 0.75rem;
                padding: 0.75rem;
                background: var(--surface-alt);
                border-radius: 0.5rem;
                font-size: 0.875rem;
                color: var(--text-secondary);
                border-left: 3px solid var(--primary-color);
                animation: fadeIn 0.3s ease-in;
            }

            .system-info {
                background: rgba(37, 99, 235, 0.05);
                border-radius: 0.5rem;
                padding: 1rem;
                margin: 1rem 0;
                font-size: 0.875rem;
                color: var(--text-secondary);
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .system-info-title {
                font-weight: 600;
                color: var(--primary-color);
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .system-info-item {
                display: flex;
                justify-content: space-between;
                padding: 0.5rem 0;
                border-bottom: 1px dashed rgba(0, 0, 0, 0.05);
            }
            
            .system-info-item:last-child {
                border-bottom: none;
            }
            
            .system-info-label {
                font-weight: 500;
            }
            
            .system-info-value {
                color: var(--text-primary);
            }

            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .thought-time {
                font-size: 0.75rem;
                color: var(--text-secondary);
                opacity: 0.7;
                margin-top: 0.25rem;
            }

            @media (max-width: 1200px) {
                .container {
                    grid-template-columns: 1fr;
                }
                
                .sidebar {
                    grid-column: 1;
                    position: static;
                }
            }

            @media (max-width: 768px) {
                .thoughts-panel {
                    position: static;
                    width: 100%;
                    margin-top: 2rem;
                    display: block !important;
                    max-height: 300px;
                }

                .header h1 {
                    font-size: 2rem;
                    flex-direction: column;
                    gap: 0.5rem;
                }

                .container {
                    padding: 1rem;
                }

                .content {
                    padding: 1.5rem;
                }

                .status-bar {
                    flex-direction: column;
                    gap: 0.5rem;
                    padding: 1rem;
                }

                .status-left,
                .status-right {
                    justify-content: center;
                    flex-wrap: wrap;
                }
            }

            .loading {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top-color: white;
                animation: spin 1s ease-in-out infinite;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }

            .brain-icon {
                color: {{ 'var(--status-connected)' if knowledge_connected else 'var(--status-disconnected)' }};
            }
            
            /* Tool Calls Summary Section */
            .tool-calls-section {
                margin-top: 1.5rem;
                padding: 1.5rem;
                background: rgba(5, 150, 105, 0.05);
                border-radius: 0.75rem;
                border: 1px solid rgba(5, 150, 105, 0.1);
            }
            
            .tool-calls-header {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 1rem;
                font-weight: 600;
                color: var(--success-color);
                font-size: 0.875rem;
            }
            
            .tool-call-item {
                padding: 0.75rem;
                background: rgba(255, 255, 255, 0.5);
                border-radius: 0.5rem;
                font-size: 0.875rem;
                margin-bottom: 0.5rem;
                border-left: 3px solid var(--success-color);
            }
            
            /* Tool Calls Section */
            .tool-calls-section {
                margin-top: 1.5rem;
                padding: 1rem;
                background: rgba(37, 99, 235, 0.05);
                border-radius: 0.5rem;
                border: 1px solid rgba(37, 99, 235, 0.1);
                display: block !important;
            }

            .tool-calls-header {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 0.75rem;
                font-weight: 600;
                color: var(--primary-color);
                font-size: 0.8rem;
            }
            
            .tool-calls-content {
                max-height: 200px;
                overflow-y: auto;
            }
            
            .tool-call-item {
                padding: 0.4rem;
                margin-bottom: 0.4rem;
                border-left: 2px solid var(--success-color);
                background: rgba(255, 255, 255, 0.5);
                border-radius: 0.25rem;
                font-size: 0.75rem;
            }
            
            .tool-call-name {
                font-weight: 600;
                color: var(--text-primary);
                font-size: 0.75rem;
            }
            
            .tool-call-params {
                color: var(--text-secondary);
                font-family: 'Fira Code', 'Courier New', monospace;
                font-size: 0.7rem;
                margin-top: 0.2rem;
                word-break: break-all;
            }
            
            /* Thinking Section */
            .thinking-section {
                margin-top: 1rem;
                padding: 1rem;
                background: rgba(37, 99, 235, 0.05);
                border-radius: 0.5rem;
                border: 1px solid rgba(37, 99, 235, 0.1);
                display: block !important;
            }
            
            .thinking-header {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 0.75rem;
                font-weight: 600;
                color: var(--primary-color);
                font-size: 0.8rem;
            }
            
            .thinking-content {
                color: var(--text-secondary);
                line-height: 1.4;
                font-size: 0.75rem;
                white-space: pre-wrap;
                word-wrap: break-word;
                max-height: 200px;
                overflow-y: auto;
            }
            
            .thinking-content div {
                margin-bottom: 0.3rem;
                padding: 0.3rem;
                background: rgba(255, 255, 255, 0.5);
                border-radius: 0.25rem;
            }
        </style>
    </head>
    <body>
        <div class="status-bar">
            <div class="status-left">
                <div class="status-item">
                    <div class="status-indicator connected"></div>
                    <span>Agno Framework Active</span>
                </div>
                <div class="status-item">
                    <i class="fas fa-database" style="color: {{ 'var(--status-connected)' if knowledge_connected else 'var(--status-disconnected)' }}"></i>
                    <span>Knowledge Base: {{ 'Connected' if knowledge_connected else 'Disconnected' }}</span>
                </div>
                <div class="status-item">
                    <i class="fas fa-plug" style="color: {{ 'var(--status-connected)' if agent_info.get('mcp_enabled', False) else 'var(--status-disconnected)' }}"></i>
                    <span>MCP Tools: {{ agent_info.get('mcp_servers', 0) }} Server{% if agent_info.get('mcp_servers', 0) != 1 %}s{% endif %}</span>
                </div>
                <div class="status-item">
                    <i class="fas fa-robot" style="color: var(--status-connected)"></i>
                    <span>{{ agent_info.get('model_provider', 'LLM').title() }}: {{ agent_info.get('model_name', 'Unknown') }}</span>
                </div>
            </div>
            <div class="status-right">
                <a href="/agent_info" class="nav-button">
                    <i class="fas fa-info-circle"></i>
                    <span>Agent Info</span>
                </a>
                <a href="/clear" class="nav-button">
                    <i class="fas fa-trash-alt"></i>
                    <span>Clear Knowledge Base</span>
                </a>
            </div>
        </div>

        <div class="container">
            <div class="main-content">
                <div class="header">
                    <h1>
                        <div class="header-icon">
                            <i class="fas fa-robot"></i>
                        </div>
                        Personal AI Agent
                    </h1>
                    <p>Powered by modern async agent framework with native MCP integration</p>
                    <div class="framework-badge">
                        <i class="fas fa-rocket"></i>
                        <span>Agno Framework</span>
                    </div>
                </div>

                <div class="content">
                    <form method="post" class="form-container">
                        <div class="form-group">
                            <label for="query">Your Request</label>
                            <textarea 
                                id="query" 
                                name="query" 
                                class="form-input form-textarea"
                                placeholder="Ask me anything... I can help with research, analysis, coding, and more using my MCP-powered tools."
                                required
                            ></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="topic">Topic Category (optional)</label>
                            <input 
                                type="text" 
                                id="topic" 
                                name="topic" 
                                class="form-input"
                                placeholder="e.g., research, coding, analysis, general"
                                value="general"
                            >
                        </div>

                        <input type="hidden" name="session_id" value="default">
                        
                        <button type="submit" class="submit-button" id="submitBtn">
                            <i class="fas fa-paper-plane"></i>
                            <span>Send Request</span>
                        </button>
                    </form>

                    {% if response %}
                    <!-- Actual Response Section -->
                    <div class="response-section">
                        <div class="response-header">
                            <i class="fas fa-comment-dots"></i>
                            <span>Response</span>
                        </div>
                        <div class="response-content">{{ response }}</div>
                    </div>

                    <!-- Thinking Process Section -->
                    <div class="thoughts-response-section">
                        <div class="thoughts-response-header">
                            <i class="fas fa-brain"></i>
                            <span>Agent Thoughts</span>
                        </div>
                        <div class="thoughts-response-content">
                            {% if thinking_response %}
                                {{ thinking_response }}
                            {% elif agent_thoughts and agent_thoughts|length > 0 %}
                                {% for thought in agent_thoughts %}
                                <div class="thought-line">{{ thought }}</div>
                                {% endfor %}
                            {% else %}
                                <div class="no-thoughts">No detailed thinking process captured for this interaction</div>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
                        
                        {% if context %}
                        <div class="context-section">
                            <div class="context-header">
                                <i class="fas fa-brain"></i>
                                <span>Context from Knowledge Base</span>
                            </div>
                            <div class="context-content">
                                {% for ctx in context %}
                                <div>{{ ctx }}</div>
                                {% endfor %}
                            </div>
                        </div>
                        {% endif %}
                </div>
            </div>

            <div class="sidebar">
                <div class="sidebar-title">
                    <i class="fas fa-server"></i>
                    <span>Agent Services</span>
                </div>
                <div class="agent-list">
                    {% for agent in agents %}
                    <div class="agent-item">
                        <div class="agent-icon">
                            <i class="fas fa-{{ agent.icon }}"></i>
                        </div>
                        <div class="agent-details">
                            <div class="agent-name">{{ agent.name }}</div>
                            <div class="agent-status">
                                <div class="status-indicator {% if agent.status == 'Active' or agent.status == 'Connected' %}connected{% elif agent.status == 'Pending' %}pending{% else %}disconnected{% endif %}"></div>
                                <span>{{ agent.status }}</span>
                                {% if agent.get('model') %}
                                <span class="agent-model">({{ agent.model }})</span>
                                {% endif %}
                                {% if agent.get('count') %}
                                <span class="agent-count">({{ agent.count }} servers)</span>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <div class="system-info">
                    <div class="system-info-title">
                        <i class="fas fa-info-circle"></i>
                        <span>System Information</span>
                    </div>
                    <div class="system-info-item">
                        <span class="system-info-label">Framework:</span>
                        <span class="system-info-value">{{ agent_info.get('framework', 'Agno') }}</span>
                    </div>
                    <div class="system-info-item">
                        <span class="system-info-label">Model Provider:</span>
                        <span class="system-info-value">{{ agent_info.get('model_provider', 'Unknown') }}</span>
                    </div>
                    <div class="system-info-item">
                        <span class="system-info-label">Debug Mode:</span>
                        <span class="system-info-value">{{ 'Enabled' if agent_info.get('debug_mode', False) else 'Disabled' }}</span>
                    </div>
                </div>

                <!-- Tool Calls Section -->
                <div class="tool-calls-section">
                    <div class="tool-calls-header">
                        <i class="fas fa-tools"></i>
                        <span>Tool Calls</span>
                    </div>
                    <div class="tool-calls-content">
                        {% if tool_calls and tool_calls|length > 0 %}
                            {% for tool in tool_calls %}
                            <div class="tool-call-item">
                                <div class="tool-call-name">• {{ tool.name }}</div>
                                <div class="tool-call-params">{{ tool.parameters }}</div>
                            </div>
                            {% endfor %}
                        {% else %}
                            <div class="tool-call-item">
                                <div class="tool-call-name">No tools used in this interaction</div>
                            </div>
                        {% endif %}
                    </div>
                </div>
                
                <!-- Thinking Section -->
                <div class="thinking-section">
                    <div class="thinking-header">
                        <i class="fas fa-brain"></i>
                        <span>Agent Thinking</span>
                    </div>
                    <div class="thinking-content">
                        {% if agent_thoughts and agent_thoughts|length > 0 %}
                            {% for thought in agent_thoughts %}
                            <div>{{ thought }}</div>
                            {% endfor %}
                        {% else %}
                            <div>No detailed thinking process captured for this interaction</div>
                        {% endif %}
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Form submission handling
            const form = document.querySelector('form');
            const submitBtn = document.getElementById('submitBtn');
            
            form.addEventListener('submit', function(e) {
                // Generate new session ID for this interaction
                const sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                console.log('Form submitted, new session ID:', sessionId);
                
                // Update hidden session field
                document.querySelector('input[name="session_id"]').value = sessionId;
                
                // Change button to loading state
                submitBtn.innerHTML = '<div class="loading"></div><span>Processing...</span>';
                submitBtn.disabled = true;
                
                // Allow form to submit normally (don't prevent default)
            });

            // Auto-resize textarea
            document.getElementById('query').addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 300) + 'px';
            });
        </script>
    </body>
    </html>
    """


def get_success_template():
    """Get the success page template."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Success - Personal AI Agent</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #1e293b;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
                padding: 2rem;
            }
            .success-container {
                background: white;
                padding: 3rem;
                border-radius: 1rem;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                text-align: center;
                max-width: 500px;
                width: 100%;
            }
            .success-icon {
                color: #059669;
                font-size: 4rem;
                margin-bottom: 1rem;
            }
            .success-title {
                font-size: 2rem;
                font-weight: 700;
                margin-bottom: 1rem;
                color: #1e293b;
            }
            .success-message {
                color: #64748b;
                margin-bottom: 2rem;
                line-height: 1.6;
            }
            .back-button {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background: #2563eb;
                color: white;
                padding: 1rem 2rem;
                border-radius: 0.75rem;
                text-decoration: none;
                font-weight: 600;
                transition: all 0.2s;
            }
            .back-button:hover {
                background: #1d4ed8;
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="success-container">
            <i class="fas fa-check-circle success-icon"></i>
            <h1 class="success-title">Success!</h1>
            <p class="success-message">{{ result }}</p>
            <a href="/" class="back-button">
                <i class="fas fa-arrow-left"></i>
                <span>Back to Agent</span>
            </a>
        </div>
    </body>
    </html>
    """


def get_error_template():
    """Get the error page template."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Error - Personal AI Agent</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #1e293b;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0;
                padding: 2rem;
            }
            .error-container {
                background: white;
                padding: 3rem;
                border-radius: 1rem;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                text-align: center;
                max-width: 500px;
                width: 100%;
            }
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #1e293b;
                min-height: 100vh;
                margin: 0;
                padding: 2rem;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 3rem;
                border-radius: 1rem;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            }
            .header {
                text-align: center;
                margin-bottom: 3rem;
            }
            .header h1 {
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 1rem;
            }
            .header p {
                color: #64748b;
                font-size: 1.1rem;
            }
            .info-section {
                margin-bottom: 2rem;
                padding: 1.5rem;
                background: #f8fafc;
                border-radius: 0.75rem;
                border-left: 4px solid #2563eb;
            }
            .info-title {
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .info-content {
                color: #64748b;
                line-height: 1.6;
            }
            .tools-list {
                list-style: none;
                padding: 0;
            }
            .tools-list li {
                padding: 0.5rem 0;
                border-bottom: 1px solid #e2e8f0;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            .tools-list li:last-child {
                border-bottom: none;
            }
            .back-button {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background: #2563eb;
                color: white;
                padding: 1rem 2rem;
                border-radius: 0.75rem;
                text-decoration: none;
                font-weight: 600;
                transition: all 0.2s;
                margin-top: 2rem;
            }
            .back-button:hover {
                background: #1d4ed8;
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>
                    <i class="fas fa-robot"></i>
                    Agent Information
                </h1>
                <p>Detailed information about your {{ agent_type }}</p>
            </div>

            <div class="info-section">
                <div class="info-title">
                    <i class="fas fa-cogs"></i>
                    Agent Configuration
                </div>
                <div class="info-content">
                    <strong>Type:</strong> {{ agent_type }}<br>
                    {% for key, value in agent_info.items() %}
                    <strong>{{ key.replace('_', ' ').title() }}:</strong> {{ value }}<br>
                    {% endfor %}
                </div>
            </div>

            {% if available_tools %}
            <div class="info-section">
                <div class="info-title">
                    <i class="fas fa-toolbox"></i>
                    Available Capabilities
                </div>
                <div class="info-content">
                    <ul class="tools-list">
                        {% for tool in available_tools %}
                        <li>
                            <i class="fas fa-check"></i>
                            {{ tool }}
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
            {% endif %}

            <div class="info-section">
                <div class="info-title">
                    <i class="fas fa-info-circle"></i>
                    Framework Features
                </div>
                <div class="info-content">
                    <ul class="tools-list">
                        <li><i class="fas fa-rocket"></i> Async/Await Operations</li>
                        <li><i class="fas fa-plug"></i> Native MCP Integration</li>
                        <li><i class="fas fa-database"></i> Knowledge Base System</li>
                        <li><i class="fas fa-tools"></i> Multi-tool Coordination</li>
                        <li><i class="fas fa-shield-alt"></i> Error Handling & Recovery</li>
                    </ul>
                </div>
            </div>

            <a href="/" class="back-button">
                <i class="fas fa-arrow-left"></i>
                <span>Back to Agent</span>
            </a>
        </div>
    </body>
    </html>
    """


def main():
    """Main entry point for the agno interface (used by poetry scripts)."""
    from ..agno_main import run_agno_web

    run_agno_web()


if __name__ == "__main__":
    main()
