# -*- coding: utf-8 -*-
# pylint: disable=C0302, W0603, C0103, C0301, W0718
"""
Web interface module for the Personal AI Agent using agno framework.

This module provides a Flask-based web interface that works with agno agents,
maintaining the same UI and functionality as the original interface.py.
"""

import asyncio
import json
import queue
import threading
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from flask import Flask, Response, render_template_string, request

from ..config import USE_MCP


# Simple function to replace archived memory functionality
def is_weaviate_connected() -> bool:
    """Check if Weaviate is configured and potentially connected."""
    return False  # Always return False since we don't use Weaviate anymore


if TYPE_CHECKING:
    from logging import Logger

    from agno.agent import Agent

# These will be injected by the main module
app: Flask = None
agno_agent: "Agent" = None  # Now using native agno Agent
logger: "Logger" = None

# Memory function references - no longer needed with native agno agent
# The native agent handles memory automatically

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
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
    agent: "Agent",
    log: "Logger",
):
    """
    Register Flask routes with the native agno agent.

    :param flask_app: Flask application instance
    :param agent: Native agno Agent instance
    :param log: Logger instance
    """
    global app, agno_agent, logger

    app = flask_app
    agno_agent = agent
    logger = log

    logger.info("Starting route registration for native agno interface")

    # Add initial system ready thought
    add_thought("🟢 Native Agno System Ready", "default")
    logger.info("Added initial system ready thought")

    app.add_url_rule("/", "index", index, methods=["GET", "POST"])
    app.add_url_rule("/clear", "clear_kb", clear_kb_route)
    app.add_url_rule("/agent_info", "agent_info", agent_info_route)
    app.add_url_rule("/stream_thoughts", "stream_thoughts", stream_thoughts_route)

    logger.info("All native agno interface routes registered successfully")


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

    error = result_container.get("error")
    if error is not None:
        if isinstance(error, Exception):
            raise error
        # Convert non-Exception errors to RuntimeError
        raise RuntimeError(f"Unknown error: {error}")

    if not result_container["done"]:
        raise TimeoutError("Async operation timed out")

    return result_container["result"]


def index():
    """
    Main route for the agent interface using agno framework.

    :return: Rendered HTML template
    """
    if logger:
        logger.info(f"Index route accessed - method: {request.method}")

    response = None
    agent_thoughts = []

    if request.method == "POST":
        user_input = request.form.get("query", "")
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
            add_thought("🔍 Searching memory for context...", session_id)

            try:
                # Native agno agent handles memory/knowledge automatically
                if logger:
                    logger.info(
                        "Native agno agent will handle memory and knowledge automatically"
                    )

                # Update thoughts after context search
                if agno_agent.memory or agno_agent.knowledge:
                    add_thought(
                        "✅ Native memory and knowledge systems active", session_id
                    )
                else:
                    add_thought("📝 Running without persistent memory", session_id)

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

                            # Prepare enhanced prompt with user request
                            # The native agno agent will automatically:
                            # - Search knowledge base if enabled
                            # - Retrieve relevant memory context
                            # - Store the interaction after completion

                            if logger:
                                logger.info(
                                    f"Prepared user input with {len(user_input)} characters"
                                )

                            # Use agno agent with async execution
                            if logger:
                                logger.info(
                                    "Creating new event loop for agno agent execution"
                                )

                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                if logger:
                                    logger.info(
                                        "Starting native agno agent run with user query"
                                    )

                                # Use native agno agent which handles memory automatically
                                agent_response = loop.run_until_complete(
                                    agno_agent.arun(user_input)
                                )
                                result_container["response"] = agent_response.content

                                if logger:
                                    logger.info(
                                        f"Native agno agent completed successfully - response length: {len(str(agent_response.content))}"
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
                        raise error

                    response = result_container.get("response")
                    if response is None:
                        if logger:
                            logger.error(
                                "Agent thread completed but returned no response"
                            )
                        raise RuntimeError(
                            "Native agno agent execution timed out or returned no response"
                        )

                    if logger:
                        logger.info(
                            f"Successfully received response from agent thread - length: {len(str(response))}"
                        )

                    # Native agno agent handles interaction storage automatically
                    add_thought(
                        "💾 Interaction stored automatically by agno", session_id
                    )

                    if logger:
                        logger.info(
                            "Native agno agent handles memory storage automatically"
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

    # Check Weaviate connection status
    weaviate_status = is_weaviate_connected()

    return render_template_string(
        get_main_template(),
        response=response,
        context=None,  # Native agno agent handles context automatically
        agent_thoughts=agent_thoughts,
        is_multi_agent=True,  # agno supports multiple capabilities
        weaviate_connected=weaviate_status,
    )


def clear_kb_route():
    """Route to clear the knowledge base."""
    if logger:
        logger.info("Clear knowledge base route accessed")

    try:
        result = "Knowledge base clearing not supported with native agno agent"

        # With native agno agent, knowledge/memory management is handled differently
        # The agent's memory and knowledge systems manage their own lifecycle
        if agno_agent and hasattr(agno_agent, "knowledge") and agno_agent.knowledge:
            result = "Native agno agent knowledge system is managed automatically"
        elif agno_agent and hasattr(agno_agent, "memory") and agno_agent.memory:
            result = "Native agno agent memory system is managed automatically"
        else:
            result = "No knowledge base or memory system detected"

        logger.info("Knowledge base status via web interface: %s", result)
        return render_template_string(
            get_success_template(),
            result=result,
        )
    except Exception as e:
        logger.error("Error checking knowledge base via web interface: %s", str(e))
        return render_template_string(
            get_error_template(),
            error=str(e),
        )


def agent_info_route():
    """Route for displaying agent information."""
    if logger:
        logger.info("Agent info route accessed")

    # Get agent info from native agno agent
    agent_type = "Native Agno Framework Agent"
    agent_info = {}

    if agno_agent:
        try:
            # Get info about the native agno agent
            agent_info = {
                "model": str(
                    agno_agent.model.id
                    if hasattr(agno_agent.model, "id")
                    else agno_agent.model
                ),
                "memory_enabled": agno_agent.memory is not None,
                "knowledge_enabled": agno_agent.knowledge is not None,
                "tools_count": len(agno_agent.tools) if agno_agent.tools else 0,
                "session_id": getattr(agno_agent, "session_id", "Not available"),
                "user_id": getattr(agno_agent, "user_id", "Not available"),
                "agentic_memory": getattr(agno_agent, "enable_agentic_memory", False),
                "user_memories": getattr(agno_agent, "enable_user_memories", False),
                "session_summaries": getattr(
                    agno_agent, "enable_session_summaries", False
                ),
            }

            if logger:
                logger.info(f"Retrieved native agno agent info: {agent_info}")

        except Exception as e:
            logger.warning("Could not get native agno agent info: %s", e)
            agent_info = {"error": str(e)}

    # Get available tools from the native agno agent
    available_tools = []
    if agno_agent:
        try:
            # Extract tool information from native agent
            if agno_agent.tools:
                for tool in agno_agent.tools:
                    tool_name = getattr(tool, "name", str(tool))
                    available_tools.append(tool_name)

            # Add native agno capabilities
            if agent_info.get("memory_enabled"):
                available_tools.append("Native Agno Memory System")

            if agent_info.get("knowledge_enabled"):
                available_tools.append("Native Agno Knowledge Base")

            if agent_info.get("agentic_memory"):
                available_tools.append("Agentic Memory Management")

            if agent_info.get("user_memories"):
                available_tools.append("User Memory Tracking")

            if agent_info.get("session_summaries"):
                available_tools.append("Session Summary Generation")

            # Add core agno features
            available_tools.extend(
                [
                    "Async Processing",
                    "Message History",
                    "Multi-tool Coordination",
                    "Context Enhancement",
                ]
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
            }

            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: var(--success-color);
                animation: pulse 2s infinite;
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
                max-width: 95%;
                margin: 0 auto;
                padding: 5rem 2rem 2rem;
            }

            .header {
                text-align: center;
                margin-bottom: 3rem;
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
                max-width: 90%;
                margin: 0 auto;
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
                margin-bottom: 0.5rem;
                font-weight: 600;
                color: var(--text-primary);
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
                    padding: 5rem 1rem 2rem;
                }

                .content {
                    max-width: 100%;
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
                color: {{ 'var(--brain-connected)' if weaviate_connected else 'var(--brain-disconnected)' }};
            }
        </style>
    </head>
    <body>
        <div class="status-bar">
            <div class="status-left">
                <div class="status-item">
                    <div class="status-indicator"></div>
                    <span>Agno Framework Active</span>
                </div>
                <div class="status-item">
                    <i class="fas fa-brain brain-icon"></i>
                    <span>Memory: {{ 'Connected' if weaviate_connected else 'Disconnected' }}</span>
                </div>
                <div class="status-item">
                    <i class="fas fa-plug"></i>
                    <span>MCP Tools Ready</span>
                </div>
            </div>
            <div class="status-right">
                <a href="/agent_info" class="nav-button">
                    <i class="fas fa-info-circle"></i>
                    <span>Agent Info</span>
                </a>
                <a href="/clear" class="nav-button">
                    <i class="fas fa-trash-alt"></i>
                    <span>Clear Memory</span>
                </a>
            </div>
        </div>

        <div class="container">
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
                <div class="response-section">
                    <div class="response-header">
                        <i class="fas fa-robot"></i>
                        <span>Agno Agent Response</span>
                    </div>
                    <div class="response-content">{{ response }}</div>
                    
                    {% if context %}
                    <div class="context-section">
                        <div class="context-header">
                            <i class="fas fa-brain"></i>
                            <span>Context from Memory</span>
                        </div>
                        <div class="context-content">
                            {% for ctx in context %}
                            <div>{{ ctx }}</div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </div>

        <div class="thoughts-panel" id="thoughtsPanel">
            <div class="thoughts-header">
                <i class="fas fa-brain"></i>
                <span>Agent Thoughts</span>
            </div>
            <div class="thoughts-content" id="thoughtsContent">
                <!-- Thoughts will be populated here -->
            </div>
        </div>

        <script>
            // Form submission handling
            const form = document.querySelector('form');
            const submitBtn = document.getElementById('submitBtn');
            let sessionId = 'default';
            
            form.addEventListener('submit', function(e) {
                // Generate new session ID for this interaction
                sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                console.log('Form submitted, new session ID:', sessionId);
                
                // Update hidden session field
                document.querySelector('input[name="session_id"]').value = sessionId;
                
                // Show thoughts panel
                const thoughtsPanel = document.getElementById('thoughtsPanel');
                thoughtsPanel.style.display = 'block';
                
                // Change button to loading state
                submitBtn.innerHTML = '<div class="loading"></div><span>Processing...</span>';
                submitBtn.disabled = true;
                
                // Start listening for thoughts after small delay
                setTimeout(() => {
                    startThoughtStream();
                }, 200);
                
                // Allow form to submit normally (don't prevent default)
            });

            function startThoughtStream() {
                const thoughtsContent = document.getElementById('thoughtsContent');
                
                // Clear existing thoughts
                thoughtsContent.innerHTML = '';
                
                // Create EventSource for streaming with current session ID
                const eventSource = new EventSource(`/stream_thoughts?session_id=${sessionId}`);
                
                eventSource.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        
                        if (data.type === 'connected') {
                            console.log('Connected to thought stream');
                            return;
                        }
                        
                        if (data.type === 'keep-alive') {
                            return;
                        }
                        
                        if (data.thought && data.thought !== 'Ready') {
                            addThoughtToPanel(data.thought, data.timestamp);
                        } else if (data.thought === 'Ready') {
                            // Processing complete - reset form and hide thoughts panel
                            eventSource.close();
                            
                            // Reset submit button
                            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i><span>Send Request</span>';
                            submitBtn.disabled = false;
                            
                            // Hide thoughts panel after a delay
                            setTimeout(() => {
                                document.getElementById('thoughtsPanel').style.display = 'none';
                            }, 2000);
                        }
                    } catch (e) {
                        console.error('Error parsing thought data:', e);
                    }
                };
                
                eventSource.onerror = function(event) {
                    console.error('Thought stream error:', event);
                    eventSource.close();
                    
                    // Reset button on error
                    submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i><span>Send Request</span>';
                    submitBtn.disabled = false;
                };
            }

            function addThoughtToPanel(thought, timestamp) {
                const thoughtsContent = document.getElementById('thoughtsContent');
                const thoughtElement = document.createElement('div');
                thoughtElement.className = 'thought-item';
                
                const time = new Date(timestamp).toLocaleTimeString();
                thoughtElement.innerHTML = `
                    <div>${thought}</div>
                    <div class="thought-time">${time}</div>
                `;
                
                thoughtsContent.appendChild(thoughtElement);
                thoughtsContent.scrollTop = thoughtsContent.scrollHeight;
            }

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
            .error-icon {
                color: #dc2626;
                font-size: 4rem;
                margin-bottom: 1rem;
            }
            .error-title {
                font-size: 2rem;
                font-weight: 700;
                margin-bottom: 1rem;
                color: #1e293b;
            }
            .error-message {
                color: #64748b;
                margin-bottom: 2rem;
                line-height: 1.6;
                word-break: break-word;
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
        <div class="error-container">
            <i class="fas fa-exclamation-triangle error-icon"></i>
            <h1 class="error-title">Error</h1>
            <p class="error-message">{{ error }}</p>
            <a href="/" class="back-button">
                <i class="fas fa-arrow-left"></i>
                <span>Back to Agent</span>
            </a>
        </div>
    </body>
    </html>
    """


def get_agent_info_template():
    """Get the agent info page template."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Agent Info - Personal AI Agent</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            body {
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
                        <li><i class="fas fa-brain"></i> Weaviate Memory System</li>
                        <li><i class="fas fa-sync"></i> Real-time Thought Streaming</li>
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
