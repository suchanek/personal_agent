# -*- coding: utf-8 -*-
# pylint: disable=C0302, W0603, C0103, C0301
"""
Web interface module for the Personal AI Agent.

This module provides a Flask-based web interface that works with LangChain,
maintaining the same UI and functionality as smol_interface.py.
"""

import json
import queue
import threading
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

from flask import Flask, Response, render_template_string, request
from langchain_core.callbacks import BaseCallbackHandler

from ..core.memory import is_weaviate_connected

if TYPE_CHECKING:
    from logging import Logger

    from langchain.agents import AgentExecutor

# These will be injected by the main module
app: Flask = None
agent_executor: "AgentExecutor" = None
logger: "Logger" = None

# Memory function references (adapted for LangChain)
query_knowledge_base_func = None
store_interaction_func = None
clear_knowledge_base_func = None

# Streaming thoughts management
thoughts_queue = queue.Queue()
active_sessions = set()
current_thoughts = {}  # Store only the latest thought per session


class ToolUsageCallbackHandler(BaseCallbackHandler):
    """Custom callback handler to track tool usage and add thoughts."""

    def __init__(self, session_id: str = "default"):
        """
        Initialize the callback handler.

        :param session_id: Session ID for thought tracking
        """
        super().__init__()
        self.session_id = session_id

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        """Called when a tool starts running."""
        tool_name = serialized.get("name", "Unknown Tool")
        add_thought(f"🔧 I am now using tool: {tool_name}", self.session_id)

    def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        """Called when a tool finishes running."""
        add_thought("✅ Tool execution completed", self.session_id)

    def on_tool_error(self, error: Exception, **kwargs: Any) -> Any:
        """Called when a tool encounters an error."""
        add_thought(f"❌ Tool error: {str(error)}", self.session_id)


# Logger capture setup


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
    executor,
    log,
    query_kb_func,
    store_int_func,
    clear_kb_func,
):
    """
    Register Flask routes with the LangChain-compatible application.

    :param flask_app: Flask application instance
    :param executor: LangChain agent executor
    :param log: Logger instance
    :param query_kb_func: Function to query knowledge base
    :param store_int_func: Function to store interactions
    :param clear_kb_func: Function to clear knowledge base
    """
    global app, agent_executor, logger, query_knowledge_base_func, store_interaction_func, clear_knowledge_base_func

    app = flask_app
    agent_executor = executor
    logger = log
    query_knowledge_base_func = query_kb_func
    store_interaction_func = store_int_func
    clear_knowledge_base_func = clear_kb_func

    # Add initial system ready thought
    add_thought("🟢 System Ready", "default")

    app.add_url_rule("/", "index", index, methods=["GET", "POST"])
    app.add_url_rule("/clear", "clear_kb", clear_kb_route)
    app.add_url_rule("/agent_info", "agent_info", agent_info_route)
    app.add_url_rule("/stream_thoughts", "stream_thoughts", stream_thoughts_route)


def index():
    """
    Main route for the agent interface using LangChain.

    :return: Rendered HTML template
    """
    response = None
    context = None
    agent_thoughts = []

    if request.method == "POST":
        user_input = request.form.get("query", "")
        topic = request.form.get("topic", "general")
        session_id = request.form.get("session_id", "default")

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

            # Start streaming thoughts (these will be buffered until stream connects)
            add_thought("🤔 Thinking about your request...", session_id)
            add_thought("🔍 Searching memory for context...", session_id)

            try:
                # Query knowledge base for context using LangChain tool
                context = None
                if query_knowledge_base_func:
                    try:
                        # Use invoke method for LangChain tool
                        context_result = query_knowledge_base_func.invoke(
                            {"query": user_input, "limit": 3}
                        )

                        if (
                            context_result
                            and context_result != "No relevant context found."
                        ):
                            context = (
                                context_result
                                if isinstance(context_result, list)
                                else [context_result]
                            )
                        else:
                            context = ["No relevant context found."]

                    except (AttributeError, TypeError, ValueError, RuntimeError) as e:
                        logger.warning("Could not query knowledge base: %s", e)
                        context = ["No context available."]
                else:
                    context = ["Memory not available."]

                # Update thoughts after context search
                if (
                    context
                    and context != ["No relevant context found."]
                    and context != ["Memory not available."]
                ):
                    add_thought("✅ Found relevant context in memory", session_id)
                else:
                    add_thought(
                        "📝 No previous context found, starting fresh", session_id
                    )

                # Add processing thoughts
                add_thought("🧠 Analyzing request with AI reasoning", session_id)
                add_thought("🔧 Preparing tools and capabilities", session_id)
                add_thought("⚡ Processing with LangChain framework", session_id)

                # Prepare context string for agent
                context_str = (
                    "\n".join(context) if context else "No relevant context found."
                )

                # Create enhanced prompt with context
                enhanced_prompt = f"""Previous Context:
{context_str}

User Request: {user_input}

Please help the user with their request. Use available tools as needed and provide a helpful, comprehensive response."""

                # Execute LangChain agent in a separate thread for real-time thoughts
                try:
                    # Add more detailed processing thoughts
                    add_thought("🔍 Examining available tools", session_id)
                    add_thought("📊 Processing information patterns", session_id)
                    add_thought("💡 Formulating response strategy", session_id)
                    add_thought("🎯 Executing chosen approach", session_id)

                    # Container for the response and any error from the thread
                    result_container = {"response": None, "error": None, "done": False}

                    def agent_worker():
                        """Worker function to run agent in separate thread."""
                        try:
                            # Add periodic thoughts during processing
                            add_thought("🤖 Agent is thinking...", session_id)
                            time.sleep(0.5)  # Small delay to show the thought

                            add_thought("🔧 Analyzing with AI tools", session_id)
                            time.sleep(0.5)

                            # Create callback handler for tool usage tracking
                            tool_callback = ToolUsageCallbackHandler(session_id)

                            # Use LangChain agent executor with callback
                            agent_response = agent_executor.invoke(
                                {"input": enhanced_prompt},
                                {"callbacks": [tool_callback]},
                            )

                            # Extract response based on LangChain format
                            if isinstance(agent_response, dict):
                                result_container["response"] = agent_response.get(
                                    "output", str(agent_response)
                                )
                            else:
                                result_container["response"] = str(agent_response)

                            add_thought(
                                "✨ Response generated successfully", session_id
                            )

                        except (
                            RuntimeError,
                            AttributeError,
                            TypeError,
                            ValueError,
                        ) as e:
                            result_container["error"] = e
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
                        "🧠 Deep thinking in progress...",
                        "🔍 Exploring possible solutions...",
                        "📝 Gathering relevant information...",
                        "⚙️ Processing with advanced reasoning...",
                        "🎯 Refining the approach...",
                        "💭 Almost there...",
                    ]

                    # Wait for the agent to complete, adding thoughts periodically
                    while not result_container["done"]:
                        time.sleep(2.0)  # Wait 2 seconds between thoughts
                        if not result_container["done"] and thought_counter < len(
                            progress_thoughts
                        ):
                            add_thought(progress_thoughts[thought_counter], session_id)
                            thought_counter += 1

                    # Wait for thread to complete and get the result
                    agent_thread.join(timeout=30)  # Max 30 seconds wait

                    error = result_container.get("error")
                    if error is not None:
                        if isinstance(error, Exception):
                            raise error
                        else:
                            raise RuntimeError(f"Agent execution failed: {error}")

                    response = result_container.get("response")
                    if response is None:
                        raise RuntimeError(
                            "Agent execution timed out or returned no response"
                        )

                    # Store interaction AFTER getting response
                    if store_interaction_func:
                        try:
                            interaction_text = (
                                f"User: {user_input}\nAssistant: {response}"
                            )
                            store_interaction_func.invoke(
                                {"text": interaction_text, "topic": topic}
                            )
                            add_thought("💾 Interaction stored in memory", session_id)
                        except (AttributeError, TypeError, ValueError) as e:
                            logger.warning("Could not store interaction: %s", e)

                except (RuntimeError, AttributeError, TypeError, ValueError) as e:
                    logger.error("Error with LangChain execution: %s", str(e))
                    response = f"Error processing request: {str(e)}"
                    add_thought(f"❌ Error occurred: {str(e)}", session_id)

            except (RuntimeError, AttributeError, TypeError, ValueError, OSError) as e:
                logger.error("Error processing query: %s", str(e))
                response = f"Error processing query: {str(e)}"
                add_thought(f"❌ Error occurred: {str(e)}", session_id)

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
        context=context,
        agent_thoughts=agent_thoughts,
        is_multi_agent=hasattr(agent_executor, "get_agent_info"),
        weaviate_connected=weaviate_status,
    )


def clear_kb_route():
    """Route to clear the knowledge base."""
    try:
        if clear_knowledge_base_func:
            result = clear_knowledge_base_func()
        else:
            result = "Clear function not available"
        logger.info("Knowledge base cleared via web interface: %s", result)
        return render_template_string(
            get_success_template(),
            result=result,
        )
    except (AttributeError, TypeError, ValueError, RuntimeError) as e:
        logger.error("Error clearing knowledge base via web interface: %s", str(e))
        return render_template_string(
            get_error_template(),
            error=str(e),
        )


def get_main_template():
    """
    Get the main HTML template for the interface.

    :return: HTML template string
    """
    return """
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>Personal AI Agent</title>
        <link href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css\" rel=\"stylesheet\">
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

            .content {
                max-width: 90%;
                margin: 0 auto;
                background: var(--surface);
                padding: 2rem;
                border-radius: 1rem;
                box-shadow: var(--shadow);
                border: 1px solid rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
            }

            .form-section {
                margin-bottom: 2rem;
            }

            .form-header {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                margin-bottom: 1.5rem;
                color: var(--text-primary);
                font-size: 1.25rem;
                font-weight: 600;
            }

            .form-icon {
                background: var(--primary-color);
                color: white;
                padding: 0.75rem;
                border-radius: 0.75rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
            }

            .query-container {
                position: relative;
            }

            .query-input {
                width: 100%;
                padding: 1.25rem 1rem 1.25rem 3rem;
                border: 2px solid var(--border-color);
                border-radius: 0.75rem;
                font-size: 1rem;
                font-family: inherit;
                resize: vertical;
                min-height: 120px;
                background: var(--surface-alt);
                transition: all 0.3s;
                line-height: 1.6;
            }

            .query-input:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
                background: white;
            }

            .query-icon {
                position: absolute;
                left: 1rem;
                top: 1.25rem;
                color: var(--text-secondary);
                font-size: 1.125rem;
            }

            .submit-container {
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-top: 1.5rem;
            }

            .btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 0.5rem;
                padding: 0.875rem 2rem;
                background: var(--primary-color);
                color: white;
                border: none;
                border-radius: 0.75rem;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                min-width: 140px;
            }

            .btn:hover {
                background: var(--primary-dark);
                transform: translateY(-2px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            }

            .btn:active {
                transform: translateY(0);
            }

            .btn-secondary {
                background: var(--text-secondary);
                color: white;
            }

            .btn-secondary:hover {
                background: var(--text-primary);
            }

            .processing-indicator {
                display: none;
                align-items: center;
                gap: 0.5rem;
                color: var(--text-secondary);
                font-size: 0.875rem;
            }

            .processing-indicator.active {
                display: flex;
            }

            .spinner {
                width: 16px;
                height: 16px;
                border: 2px solid var(--border-color);
                border-top: 2px solid var(--primary-color);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .response-section {
                display: block; /* Ensure the response pane is always visible */
                margin-top: 2rem;
                padding-top: 2rem;
                border-top: 2px solid var(--border-color);
            }

            /* Brain icon status styles */
            .brain-connected {
                color: var(--brain-connected) !important;
                animation: pulse-connected 2s infinite;
            }

            .brain-disconnected {
                color: var(--brain-disconnected) !important;
                animation: pulse-disconnected 2s infinite;
            }

            @keyframes pulse-connected {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }

            @keyframes pulse-disconnected {
                0% { opacity: 1; }
                50% { opacity: 0.4; }
                100% { opacity: 1; }
            }
            }

            .response-header {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                margin-bottom: 1.5rem;
                color: var(--success-color);
                font-size: 1.25rem;
                font-weight: 600;
            }

            .response-icon {
                background: var(--success-color);
                color: white;
                padding: 0.75rem 1rem;
                border-radius: 0.75rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 1rem;
                font-weight: 600;
            }

            .response-content {
                background: var(--surface-alt);
                padding: 1.5rem;
                border-radius: 0.75rem;
                border-left: 4px solid var(--success-color);
                white-space: pre-line;
                line-height: 1.8;
                color: var(--text-primary);
                font-size: 1rem;
                box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
                min-height: 100px; /* Ensure a minimum height for visibility */
                text-indent: 0; /* Ensure no text indentation */
            }

            /* Responsive Design */
            @media (min-width: 1920px) {
                .container {
                    max-width: 90%;
                }
                
                .content {
                    max-width: 85%;
                    padding: 3rem;
                }
            }

            @media (max-width: 1024px) {
                .status-bar {
                    padding: 0.5rem 1rem;
                }

                .status-left, .status-right {
                    gap: 0.5rem;
                }

                .nav-button {
                    padding: 0.375rem 0.75rem;
                    font-size: 0.8rem;
                }
            }

            @media (max-width: 768px) {
                .container {
                    padding: 4rem 1rem 1rem;
                }

                .header h1 {
                    font-size: 2rem;
                    flex-direction: column;
                    gap: 0.5rem;
                }

                .status-bar {
                    flex-direction: column;
                    gap: 0.5rem;
                    padding: 0.75rem 1rem;
                }

                .content {
                    padding: 1.5rem;
                }
            }
        </style>
    </head>
    <body>
        <!-- Status Bar -->
        <div class=\"status-bar\">
            <div class=\"status-left\">
                <div class=\"status-item\">
                    <div class=\"status-indicator\"></div>
                    <span>AI Agent Online</span>
                </div>
                <div class=\"status-item\">
                    <i class=\"fas fa-robot\"></i>
                    <span>LangChain Agent</span>
                </div>
                <div class=\"status-item\">
                    <i class=\"fas fa-clock\"></i>
                    <span id=\"current-time\"></span>
                </div>
                <div class=\"status-item\" id=\"agent-status-item\">
                    <i class=\"fas fa-brain {% if weaviate_connected %}brain-connected{% else %}brain-disconnected{% endif %}\"></i>
                    <span id=\"agent-status-text\">Ready</span>
                </div>
            </div>
            <div class=\"status-right\">
                <a href=\"/agent_info\" class=\"nav-button\">
                    <i class=\"fas fa-info-circle\"></i>
                    <span>Agent Info</span>
                </a>
                <a href=\"/clear\" class=\"nav-button\">
                    <i class=\"fas fa-trash-alt\"></i>
                    <span>Clear</span>
                </a>
            </div>
        </div>

        <div class=\"container\">
            <div class=\"header\">
                <h1>
                    <div class=\"header-icon\">
                        <i class=\"fas fa-brain {% if weaviate_connected %}brain-connected{% else %}brain-disconnected{% endif %}\"></i>
                    </div>
                    Personal AI Agent
                </h1>
                <p>Your intelligent assistant powered by LangChain architecture</p>
            </div>
            
            <div class=\"content\">
                <div class=\"form-section\">
                    <div class=\"form-header\">
                        <div class=\"form-icon\">
                            <i class=\"fas fa-comment-dots\"></i>
                        </div>
                        Ask me anything
                    </div>
                    <form method=\"post\" id=\"query-form\">
                        <input type=\"hidden\" id=\"session_id\" name=\"session_id\" value=\"default\">
                        <div class=\"query-container\">
                            <i class=\"fas fa-pen query-icon\"></i>
                            <textarea 
                                id=\"query\" 
                                name=\"query\" 
                                class=\"query-input\"
                                placeholder=\"Type your question or request here...\"
                                required
                            ></textarea>
                        </div>
                        <div class=\"submit-container\">
                            <button type=\"submit\" class=\"btn\">
                                <i class=\"fas fa-paper-plane\"></i>
                                Send Query
                            </button>
                            <button type=\"button\" class=\"btn btn-secondary\" onclick=\"clearForm()\">
                                <i class=\"fas fa-eraser\"></i>
                                Clear
                            </button>
                            <div class=\"processing-indicator\" id=\"processing\">
                                <div class=\"spinner\"></div>
                                <span>Processing your request...</span>
                            </div>
                        </div>
                    </form>
                </div>
                
                <div class=\"response-section\">
                    <div class=\"response-header\">
                        <div class=\"response-icon\">
                            <i class=\"fas fa-check-circle\"></i>
                            Agent Response
                        </div>
                    </div>
                    <div class=\"response-content\">
                        {% if response %}{{ response }}{% else %}Your response will appear here...{% endif %}
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Update current time
            function updateTime() {
                try {
                    const now = new Date();
                    if (isNaN(now.getTime())) {
                        console.warn('Invalid date created, using fallback');
                        document.getElementById('current-time').textContent = '--:--';
                        return;
                    }
                    const timeString = now.toLocaleTimeString('en-US', { 
                        hour12: false,
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                    document.getElementById('current-time').textContent = timeString;
                } catch (e) {
                    console.warn('Error updating time:', e);
                    document.getElementById('current-time').textContent = '--:--';
                }
            }
            
            updateTime();
            setInterval(updateTime, 1000);

            // Form handling
            const form = document.getElementById('query-form');
            const processing = document.getElementById('processing');
            
            form.addEventListener('submit', function(e) {
                processing.classList.add('active');
                
                // Auto-focus query input after response
                setTimeout(() => {
                    document.getElementById('query').focus();
                }, 100);
            });

            // Monitor processing state to reset thought to "Ready" when complete
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        const target = mutation.target;
                        if (target.id === 'processing' && !target.classList.contains('active')) {
                            // Processing completed, reset thought to Ready
                            console.log('Processing completed - resetting status to Ready');
                            const agentStatusText = document.getElementById('agent-status-text');
                            if (agentStatusText) {
                                agentStatusText.textContent = 'Ready';
                            }
                        }
                    }
                });
            });
            
            // Start observing the processing indicator
            observer.observe(processing, { attributes: true });

            // Clear form function
            function clearForm() {
                document.getElementById('query').value = '';
                document.getElementById('query').focus();
            }

            // Auto-resize textarea
            const textarea = document.getElementById('query');
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.max(120, this.scrollHeight) + 'px';
            });

            // Focus on load and reset thought status if needed
            window.addEventListener('load', function() {
                document.getElementById('query').focus();
                
                // Reset status text to Ready if page just loaded with a response
                const agentStatusText = document.getElementById('agent-status-text');
                const responseContent = document.querySelector('.response-content');
                
                // If there's a response visible and status text isn't "Ready", reset it
                if (agentStatusText && responseContent && responseContent.textContent.trim() !== 'Your response will appear here...') {
                    if (agentStatusText.textContent !== 'Ready') {
                        console.log('Page loaded with response, resetting thought to Ready');
                        thoughtContent.textContent = 'Ready';
                    }
                }
            });

            // Keyboard shortcuts
            document.addEventListener('keydown', function(e) {
                // Ctrl/Cmd + Enter to submit
                if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                    e.preventDefault();
                    form.submit();
                }
                
                // Ctrl/Cmd + K to focus query input
                if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                    e.preventDefault();
                    document.getElementById('query').focus();
                }
            });

            // Current thought display streaming
            let eventSource = null;
            let sessionId = 'default';
            let currentSessionId = 'default'; // Track the current active session
            
            function startThoughtsStream() {
                console.log('Starting thoughts stream for session:', sessionId);
                
                if (eventSource) {
                    eventSource.close();
                }
                
                eventSource = new EventSource('/stream_thoughts?session_id=' + sessionId);
                const agentStatusText = document.getElementById('agent-status-text');
                
                eventSource.onopen = function() {
                    console.log('EventSource connection opened for session:', sessionId);
                };
                
                eventSource.onmessage = function(event) {
                    console.log('Received SSE message:', event.data);
                    try {
                        const data = JSON.parse(event.data);
                        console.log('Parsed SSE data:', data);
                        
                        // Handle connection confirmation
                        if (data.type === 'connected') {
                            console.log('Stream connection confirmed for session:', data.session_id);
                            return;
                        }
                        
                        // Handle keep-alive messages
                        if (data.type === 'keep-alive') {
                            console.log('Received keep-alive');
                            return;
                        }
                        
                        // Handle thought messages - show the actual thoughts
                        // Accept thoughts from any session if they're more recent than our current session
                        if (data.thought) {
                            console.log('Processing thought:', data.thought, 'from session:', data.session_id);
                            
                            // Update the status text with the actual thought
                            if (agentStatusText) {
                                agentStatusText.textContent = data.thought;
                            }
                            
                            console.log('Updated agent status text with:', data.thought);
                        }
                    } catch (e) {
                        console.error('Error parsing thought data:', e, 'Raw data:', event.data);
                    }
                };
                
                eventSource.onerror = function(error) {
                    console.error('EventSource error:', error);
                    
                    // Retry connection after 3 seconds
                    setTimeout(() => {
                        if (eventSource.readyState === EventSource.CLOSED) {
                            console.log('Retrying EventSource connection...');
                            startThoughtsStream();
                        }
                    }, 3000);
                };
            }
            
            // Enhanced form handling with session management
            form.addEventListener('submit', function(e) {
                // Generate new session ID for this interaction
                sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                console.log('Form submitted, new session ID:', sessionId);
                
                // Update hidden form field
                document.getElementById('session_id').value = sessionId;
                console.log('Updated hidden session_id field to:', sessionId);
                
                // Don't restart connection immediately - wait a bit to avoid timing issues
                setTimeout(() => {
                    console.log('Restarting thoughts stream with new session ID');
                    startThoughtsStream();
                }, 200); // Small delay to allow form submission to complete
                
                processing.classList.add('active');
                
                // Auto-focus query input after response
                setTimeout(() => {
                    document.getElementById('query').focus();
                }, 100);
                
                // Add a timeout to reset the status text if processing takes too long or gets stuck
                setTimeout(() => {
                    const agentStatusText = document.getElementById('agent-status-text');
                    if (agentStatusText && !processing.classList.contains('active')) {
                        console.log('Timeout reached, ensuring status is reset to Ready');
                        agentStatusText.textContent = 'Ready';
                    }
                }, 10000); // 10 second timeout
            });
            
            // Start initial stream
            startThoughtsStream();
        </script>
    </body>
    </html>
    """


def get_success_template():
    """
    Get the success page template.

    :return: HTML template string for success page
    """
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Success - Personal AI Agent</title>
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8fafc;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .success-card {
            background: white;
            padding: 3rem;
            border-radius: 1rem;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            text-align: center;
            max-width: 500px;
        }
        .success-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }
        .success-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #059669;
            margin-bottom: 1rem;
        }
        .success-message {
            color: #374151;
            margin-bottom: 2rem;
        }
        .btn {
            background: #2563eb;
            color: white;
            padding: 0.75rem 2rem;
            border: none;
            border-radius: 0.5rem;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            transition: background 0.2s;
        }
        .btn:hover {
            background: #1d4ed8;
        }
    </style>
</head>
<body>
    <div class="success-card">
        <div class="success-icon">✅</div>
        <h1 class="success-title">Operation Successful</h1>
        <p class="success-message">{{ result }}</p>
        <a href="/" class="btn">🏠 Back to Agent</a>
    </div>
</body>
</html>
"""


def get_agent_info_template():
    """
    Get the agent information template.

    :return: HTML template string for agent info page
    """
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Information - Personal AI Agent</title>
    <style>
        :root {
            --primary-color: #2563eb;
            --primary-dark: #1d4ed8;
            --success-color: #059669;
            --background: #f8fafc;
            --surface: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
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
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem 1rem;
        }

        .header {
            text-align: center;
            margin-bottom: 3rem;
        }

        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }

        .header p {
            font-size: 1.1rem;
            color: var(--text-secondary);
        }

        .badge {
            display: inline-block;
            background: var(--primary-color);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }

        .badge.multi-agent {
            background: var(--success-color);
        }

        .card {
            background: var(--surface);
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
            margin-bottom: 2rem;
        }

        .card h2 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
        }

        .agent-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        .agent-card {
            background: linear-gradient(135deg, #f8fafc, #e2e8f0);
            border-radius: 0.75rem;
            padding: 1.5rem;
            border-left: 4px solid var(--primary-color);
        }

        .agent-card h3 {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            color: var(--primary-color);
        }

        .agent-description {
            color: var(--text-secondary);
            font-size: 0.95rem;
            line-height: 1.5;
        }

        .tools-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 0.5rem;
            margin-top: 1rem;
        }

        .tool-item {
            background: #f1f5f9;
            padding: 0.5rem 0.75rem;
            border-radius: 0.5rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
            border-left: 3px solid var(--primary-color);
        }

        .navigation-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding: 1rem;
            background: var(--surface);
            border-radius: 0.75rem;
            border: 1px solid var(--border-color);
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 0.5rem;
            font-size: 0.95rem;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.2s;
            gap: 0.5rem;
        }

        .btn-primary {
            background: var(--primary-color);
            color: white;
        }

        .btn-primary:hover {
            background: var(--primary-dark);
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: var(--text-secondary);
            color: white;
        }

        .btn-secondary:hover {
            background: var(--text-primary);
        }

        .system-info {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
            color: white;
            border-radius: 1rem;
            padding: 2rem;
            margin-bottom: 2rem;
        }

        .system-info h2 {
            color: white;
            margin-bottom: 1rem;
        }

        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }

        .info-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 1rem;
            border-radius: 0.5rem;
        }

        .info-label {
            font-size: 0.85rem;
            opacity: 0.8;
            margin-bottom: 0.25rem;
        }

        .info-value {
            font-size: 1.1rem;
            font-weight: 600;
        }

        .fallback-info {
            background: #fef3c7;
            border: 1px solid #f59e0b;
            border-radius: 0.75rem;
            padding: 1.5rem;
            margin-top: 1rem;
        }

        .fallback-info h3 {
            color: #92400e;
            margin-bottom: 0.75rem;
        }

        .fallback-info p {
            color: #92400e;
            font-size: 0.9rem;
        }

        .footer {
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Agent Information
                {% if agent_type == "Multi-Agent System" %}
                    <span class="badge multi-agent">Multi-Agent</span>
                {% else %}
                    <span class="badge">LangChain Agent</span>
                {% endif %}
            </h1>
            <p>Current system architecture and capabilities</p>
        </div>

        <div class="navigation-bar">
            <a href="/" class="btn btn-primary">🏠 Back to Chat</a>
            <a href="/clear" class="btn btn-secondary">🗑️ Clear Memory</a>
        </div>

        <div class="system-info">
            <h2>🤖 System Overview</h2>
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Agent Type</div>
                    <div class="info-value">{{ agent_type }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Available Agents</div>
                    <div class="info-value">{{ agent_info|length }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Total Tools</div>
                    <div class="info-value">{{ available_tools|length }}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Framework</div>
                    <div class="info-value">LangChain</div>
                </div>
            </div>
        </div>

        {% if agent_type == "Multi-Agent System" %}
        <div class="card">
            <h2>🔧 Specialized Agents</h2>
            <div class="agent-grid">
                {% for agent_name, description in agent_info.items() %}
                <div class="agent-card">
                    <h3>{{ agent_name.title() }} Agent</h3>
                    <div class="agent-description">{{ description }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% else %}
        <div class="card">
            <h2>🔧 Agent Configuration</h2>
            {% for name, description in agent_info.items() %}
            <div class="agent-card">
                <h3>{{ name.title() }}</h3>
                <div class="agent-description">{{ description }}</div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="card">
            <h2>🛠️ Available Tools</h2>
            {% if available_tools %}
            <div class="tools-list">
                {% for tool in available_tools %}
                <div class="tool-item">{{ tool }}</div>
                {% endfor %}
            </div>
            {% else %}
            <p class="agent-description">No tools information available.</p>
            {% endif %}
        </div>

        {% if fallback_agent %}
        <div class="fallback-info">
            <h3>🔄 Fallback Agent Available</h3>
            <p>A single-agent fallback system is configured with {{ fallback_agent.tools|length }} tools for redundancy.</p>
        </div>
        {% endif %}

        <div class="footer">
            <p>Personal AI Agent • LangChain Framework • Multi-Tool Coordination</p>
        </div>
    </div>
</body>
</html>
"""


def get_error_template() -> str:
    """Get the error HTML template for knowledge base clearing."""
    return """
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
            """


def clean_response_from_thinking_process(response: str) -> str:
    """
    Remove thinking process content from agent response.

    :param response: Raw agent response that may contain thinking process
    :return: Cleaned response with thinking process removed
    """
    import re

    # Remove common thinking process patterns
    patterns_to_remove = [
        r"🤔.*?\n",  # Thinking emoji lines
        r"🔍.*?\n",  # Search emoji lines
        r"✅.*?\n",  # Checkmark emoji lines
        r"📝.*?\n",  # Note emoji lines
        r"🧠.*?\n",  # Brain emoji lines
        r"🔧.*?\n",  # Tool emoji lines
        r"⚡.*?\n",  # Lightning emoji lines
        r"🛠️.*?\n",  # Hammer emoji lines
        r"🔄.*?\n",  # Refresh emoji lines
        r"💡.*?\n",  # Lightbulb emoji lines
        r"📊.*?\n",  # Chart emoji lines
        r"🎯.*?\n",  # Target emoji lines
        r"✨.*?\n",  # Sparkle emoji lines
        r"❌.*?\n",  # X emoji lines
        r"Thinking about.*?\n",
        r"Searching memory.*?\n",
        r"Processing.*?\n",
        r"Analyzing.*?\n",
        r"I'm thinking.*?\n",
        r"Let me think.*?\n",
        r"Hmm.*?\n",
        r".*thinking process.*?\n",
        r".*agent thoughts.*?\n",
    ]

    cleaned_response = response
    for pattern in patterns_to_remove:
        cleaned_response = re.sub(pattern, "", cleaned_response, flags=re.IGNORECASE)

    # Remove multiple consecutive newlines
    cleaned_response = re.sub(r"\n\s*\n", "\n\n", cleaned_response)

    # Strip leading/trailing whitespace from the entire response
    cleaned_response = cleaned_response.strip()

    # Remove leading whitespace from each line to prevent indentation issues
    lines = cleaned_response.split("\n")
    cleaned_lines = [line.lstrip() for line in lines]
    cleaned_response = "\n".join(cleaned_lines)

    return cleaned_response


def stream_thoughts_route():
    """Route for streaming thoughts."""
    session_id = request.args.get("session_id", "default")
    return Response(stream_thoughts(session_id), content_type="text/event-stream")


def agent_info_route():
    """Route for displaying agent information."""
    # Get agent info - adapted for LangChain
    agent_type = "LangChain Agent"
    agent_info = {"langchain": "Multi-tool agent executor with memory capabilities"}

    # Get available tools from the agent executor
    available_tools = []
    if agent_executor and hasattr(agent_executor, "tools"):
        available_tools = [tool.name for tool in agent_executor.tools]

    return render_template_string(
        get_agent_info_template(),
        agent_type=agent_type,
        agent_info=agent_info,
        available_tools=available_tools,
        fallback_agent=None,
    )
