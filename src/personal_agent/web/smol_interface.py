"""
Smolagents-compatible web interface module for the Personal AI Agent.

This module provides a Flask-based web interface that works with smolagents
instead of LangChain, maintaining the same UI and functionality.
"""

# pylint: disable=W0718,C0103,C0301,
import json
import logging
import queue
import threading
import time
from datetime import datetime
from io import StringIO
from typing import TYPE_CHECKING, Optional

from flask import Flask, Response, render_template_string, request

if TYPE_CHECKING:
    from logging import Logger

    from smolagents import ToolCallingAgent

# These will be injected by the main module
app: Optional[Flask] = None
smolagents_agent: Optional["ToolCallingAgent"] = None
logger: Optional["Logger"] = None

# Memory function references (from smol_tools)
query_knowledge_base_func = None
store_interaction_func = None
clear_knowledge_base_func = None

# Streaming thoughts management
thoughts_queue = queue.Queue()
active_sessions = set()
current_thoughts = {}  # Store only the latest thought per session

# Logger capture setup
log_capture_string = StringIO()
log_handler = None


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    :return: Configured Flask application
    """
    flask_app = Flask(__name__)
    return flask_app


def setup_log_capture():
    """Setup log capture for streaming to web interface."""
    global log_handler, log_capture_string

    if log_handler is not None:
        return  # Already set up

    log_capture_string = StringIO()
    log_handler = logging.StreamHandler(log_capture_string)
    log_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    log_handler.setFormatter(formatter)

    # Add to root logger to capture all logs
    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)


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
    # This ensures thoughts are streamed even if the specific session becomes inactive
    if active_sessions:  # If any sessions are active
        thoughts_queue.put(thought_data)
        if logger:
            logger.info(f"Added latest thought for session {session_id}: {thought}")
    else:
        # For when no sessions are active, just store the latest thought
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
                # Stream all thoughts to all active sessions - let the client decide what to show
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


def stream_logs():
    """Generator for streaming log output."""
    global log_capture_string

    last_position = 0
    while True:
        try:
            current_content = log_capture_string.getvalue()
            if len(current_content) > last_position:
                new_content = current_content[last_position:]
                last_position = len(current_content)

                for line in new_content.strip().split("\n"):
                    if line.strip():
                        # Format timestamp as ISO string for JavaScript Date parsing
                        timestamp = datetime.now().isoformat() + "Z"
                        yield f"data: {json.dumps({'log': line, 'timestamp': timestamp})}\n\n"

            time.sleep(0.5)  # Poll every 500ms
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            break


def register_routes(
    flask_app: Flask,
    agent,
    log,
    query_kb_func,
    store_int_func,
    clear_kb_func,
    fallback_agent=None,
):
    """
    Register Flask routes with the smolagents-compatible application.

    :param flask_app: Flask application instance
    :param agent: Primary agent (MultiAgentSystem or ToolCallingAgent)
    :param log: Logger instance
    :param query_kb_func: Function to query knowledge base
    :param store_int_func: Function to store interactions
    :param clear_kb_func: Function to clear knowledge base
    :param fallback_agent: Optional fallback single agent
    """
    global app, smolagents_agent, logger
    global query_knowledge_base_func, store_interaction_func, clear_knowledge_base_func

    app = flask_app
    smolagents_agent = agent
    logger = log
    query_knowledge_base_func = query_kb_func
    store_interaction_func = store_int_func
    clear_knowledge_base_func = clear_kb_func

    # Store fallback agent if provided
    app.config["FALLBACK_AGENT"] = fallback_agent

    # Setup log capture for streaming
    setup_log_capture()

    app.add_url_rule("/", "index", index, methods=["GET", "POST"])
    app.add_url_rule("/clear", "clear_kb", clear_kb_route)
    app.add_url_rule("/agent_info", "agent_info", agent_info_route)
    app.add_url_rule("/stream_thoughts", "stream_thoughts", stream_thoughts_route)
    app.add_url_rule("/stream_logs", "stream_logs", stream_logs_route)
    app.add_url_rule("/logger", "logger", logger_route)


def index():
    """
    Main route for the agent interface using smolagents.

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
            # (We'll let the stream handler manage active_sessions)
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
                # Query knowledge base for context using direct function call
                context = None
                if query_knowledge_base_func:
                    try:
                        # Call the function directly (it's already a Python function, not a tool)
                        context_result = query_knowledge_base_func(user_input, limit=3)

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

                    except Exception as e:
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
                add_thought("⚡ Processing with smolagents framework", session_id)

                # Prepare context string for agent
                context_str = (
                    "\n".join(context) if context else "No relevant context found."
                )

                # Create enhanced prompt with context
                enhanced_prompt = f"""Previous Context:
{context_str}

User Request: {user_input}

Please help the user with their request. Use available tools as needed and provide a helpful, comprehensive response."""

                # Execute smolagents agent in a separate thread for real-time thoughts
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

                            # Use smolagents .run() method
                            agent_response = smolagents_agent.run(enhanced_prompt)
                            result_container["response"] = agent_response

                            add_thought(
                                "✨ Response generated successfully", session_id
                            )

                        except Exception as e:
                            result_container["error"] = e
                            add_thought(
                                f"❌ Error during processing: {str(e)}", session_id
                            )
                        finally:
                            result_container["done"] = True

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

                    if result_container["error"]:
                        raise result_container["error"]

                    response = result_container["response"]
                    if response is None:
                        raise Exception(
                            "Agent execution timed out or returned no response"
                        )

                    # Store interaction AFTER getting response
                    if store_interaction_func:
                        try:
                            interaction_text = (
                                f"User: {user_input}\nAssistant: {response}"
                            )
                            store_interaction_func(interaction_text, topic)
                            add_thought("💾 Interaction stored in memory", session_id)
                        except Exception as e:
                            logger.warning("Could not store interaction: %s", e)

                except Exception as e:
                    logger.error("Error with smolagents execution: %s", str(e))
                    response = f"Error processing request: {str(e)}"
                    add_thought(f"❌ Error occurred: {str(e)}", session_id)

            except Exception as e:
                logger.error("Error processing query: %s", str(e))
                response = f"Error processing query: {str(e)}"
                add_thought(f"❌ Error occurred: {str(e)}", session_id)

            logger.debug(
                "Received query: %s..., Response: %s...",
                user_input[:50],
                str(response)[:50] if response else "None",
            )

    return render_template_string(
        get_main_template(),
        response=response,
        context=context,
        agent_thoughts=agent_thoughts,
        is_multi_agent=hasattr(smolagents_agent, "get_agent_info"),
    )


def clear_kb_route():
    """
    Route to clear the knowledge base using smolagents-compatible functions.

    :return: Rendered success template
    """
    try:
        if clear_knowledge_base_func:
            result = clear_knowledge_base_func()
            logger.info("Knowledge base cleared via web interface: %s", result)
            return render_template_string(
                get_success_template(),
                result=result,
            )
        else:
            result = "Knowledge base function not available"
            logger.warning("Clear knowledge base function not available")
            return render_template_string(
                get_success_template(),
                result=result,
            )
    except Exception as e:
        logger.error("Error clearing knowledge base via web interface: %s", str(e))
        return render_template_string(
            get_success_template(),
            result=f"Error: {str(e)}",
        )


def agent_info_route():
    """
    Route to display information about available agents and their capabilities.

    :return: Rendered agent info template
    """
    try:
        agent_info = {}
        agent_type = "Single Agent"
        available_tools = []

        # Check if we have a multi-agent system
        if hasattr(smolagents_agent, "get_agent_info"):
            agent_type = "Multi-Agent System"
            agent_info = smolagents_agent.get_agent_info()
            if hasattr(smolagents_agent, "list_available_tools"):
                available_tools = smolagents_agent.list_available_tools()
        else:
            # Single agent case
            agent_info = {"primary": "Single smolagents ToolCallingAgent"}
            if hasattr(smolagents_agent, "tools"):
                # smolagents_agent.tools is a dictionary, keys are tool names
                available_tools = list(smolagents_agent.tools.keys())

        fallback_agent = app.config.get("FALLBACK_AGENT")
        fallback_info = None
        if fallback_agent:
            fallback_info = {"type": "Single Agent Fallback", "tools": []}
            if hasattr(fallback_agent, "tools"):
                # Handle both dict and list cases for fallback agent tools
                if isinstance(fallback_agent.tools, dict):
                    fallback_info["tools"] = list(fallback_agent.tools.keys())
                else:
                    fallback_info["tools"] = [
                        tool.name for tool in fallback_agent.tools
                    ]

        return render_template_string(
            get_agent_info_template(),
            agent_type=agent_type,
            agent_info=agent_info,
            available_tools=available_tools,
            fallback_agent=fallback_info,
        )
    except Exception as e:
        logger.error("Error getting agent info: %s", str(e))
        return render_template_string(
            get_agent_info_template(),
            agent_type="Error",
            agent_info={"error": str(e)},
            available_tools=[],
            fallback_agent=None,
        )


def stream_thoughts_route():
    """
    SSE route for streaming agent thoughts in real-time.

    :return: Server-sent events stream
    """
    session_id = request.args.get("session_id", "default")

    def generate():
        for thought_data in stream_thoughts(session_id):
            yield thought_data

    response = Response(generate(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


def stream_logs_route():
    """
    SSE route for streaming logger output in real-time.

    :return: Server-sent events stream
    """

    def generate():
        for log_data in stream_logs():
            yield log_data

    response = Response(generate(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


def logger_route():
    """
    Route to display the logger output window.

    :return: Rendered logger template
    """
    return render_template_string(get_logger_template())


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

            .current-thought {
                margin-bottom: 2rem;
                padding: 1.25rem;
                background: linear-gradient(135deg, #dbeafe, #bfdbfe);
                border-radius: 0.75rem;
                border-left: 4px solid var(--primary-color);
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                transition: all 0.3s ease;
            }

            .thought-header {
                display: flex;
                align-items: center;
                gap: 0.75rem;
                margin-bottom: 0.75rem;
                color: var(--primary-color);
                font-size: 1.1rem;
                font-weight: 600;
            }

            .thought-icon {
                background: var(--primary-color);
                color: white;
                padding: 0.6rem;
                border-radius: 0.6rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
            }

            .thought-content {
                color: var(--text-primary);
                font-size: 1.2rem;
                line-height: 1.5;
                font-weight: 500;
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
                padding: 0.75rem;
                border-radius: 0.75rem;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
            }

            .response-content {
                background: var(--surface-alt);
                padding: 1.5rem;
                border-radius: 0.75rem;
                border-left: 4px solid var(--success-color);
                white-space: pre-wrap;
                line-height: 1.8;
                color: var(--text-primary);
                font-size: 1rem;
                box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
                min-height: 100px; /* Ensure a minimum height for visibility */
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
                    <span>Multi-Agent System</span>
                </div>
                <div class=\"status-item\">
                    <i class=\"fas fa-clock\"></i>
                    <span id=\"current-time\"></span>
                </div>
            </div>
            <div class=\"status-right\">
                <a href=\"/agent_info\" class=\"nav-button\">
                    <i class=\"fas fa-info-circle\"></i>
                    <span>Agent Info</span>
                </a>
                <a href=\"/logger\" class=\"nav-button\">
                    <i class=\"fas fa-terminal\"></i>
                    <span>Logger</span>
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
                        <i class=\"fas fa-brain\"></i>
                    </div>
                    Personal AI Agent
                </h1>
                <p>Your intelligent assistant powered by advanced multi-agent architecture</p>
            </div>
            
            <div class=\"content\">
                <!-- Current Thought Display - Always Visible -->
                <div class=\"current-thought\" id=\"current-thought\">
                    <div class=\"thought-header\">
                        <div class=\"thought-icon\">
                            <i class=\"fas fa-brain\"></i>
                        </div>
                        <span>Agent Status</span>
                    </div>
                    <div class=\"thought-content\" id=\"thought-content\">
                        Ready
                    </div>
                </div>
                
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
                
                {% if response %}
                <div class=\"response-section\">
                    <div class=\"response-header\">
                        <div class=\"response-icon\">
                            <i class=\"fas fa-check-circle\"></i>
                        </div>
                        Agent Response
                    </div>
                    <div class=\"response-content\">{{ response }}</div>
                </div>
                {% endif %}
            </div>
        </div>

        <script>
            // Update current time
            function updateTime() {
                const now = new Date();
                const timeString = now.toLocaleTimeString('en-US', { 
                    hour12: false,
                    hour: '2-digit',
                    minute: '2-digit'
                });
                document.getElementById('current-time').textContent = timeString;
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

            // Check if page loaded with a response - means processing is complete
            window.addEventListener('load', function() {
                const responseContent = document.querySelector('.response-content');
                if (responseContent && responseContent.textContent.trim()) {
                    // Page loaded with response - processing is complete
                    setTimeout(() => {
                        processing.classList.remove('active');
                        console.log('Page loaded with response - processing complete');
                    }, 500);
                }
            });

            // Monitor processing state to reset thought to "Ready" when complete
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        const target = mutation.target;
                        if (target.id === 'processing' && !target.classList.contains('active')) {
                            // Processing completed, reset thought to Ready after a longer delay
                            const thoughtContent = document.getElementById('thought-content');
                            if (thoughtContent && thoughtContent.textContent !== 'Ready') {
                                setTimeout(() => {
                                    // Only reset if we're not currently streaming new thoughts
                                    if (thoughtContent.textContent !== 'Ready') {
                                        thoughtContent.textContent = 'Ready';
                                        console.log('Reset thought to Ready state');
                                    }
                                }, 3000); // Longer delay to let all thoughts show
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

            // Focus on load
            window.addEventListener('load', function() {
                document.getElementById('query').focus();
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
                const currentThought = document.getElementById('current-thought');
                const thoughtContent = document.getElementById('thought-content');
                
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
                            
                            // Show the current thought display if hidden
                            if (currentThought && currentThought.style.display === 'none') {
                                currentThought.style.display = 'block';
                            }
                            
                            // Update the thought content with the actual thought
                            if (thoughtContent) {
                                thoughtContent.textContent = data.thought;
                            }
                            
                            console.log('Updated current thought display with:', data.thought);
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
            max-width: 95%;
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

        /* Responsive Design */
        @media (min-width: 1920px) {
            .container {
                max-width: 90%;
            }
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
                    <span class="badge">Single Agent</span>
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
                    <div class="info-value">Smolagents</div>
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
            <p>Personal AI Agent • Multi-Agent Coordination System • Smolagents Framework</p>
        </div>
    </div>
</body>
</html>
"""


def get_logger_template():
    """
    Get the logger output window template.

    :return: HTML template string for logger window
    """
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Logger Output - Personal AI Agent</title>
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

        .container {
            max-width: 95%;
            margin: 0 auto;
            padding: 2rem 1rem;
        }

        .header {
            text-align: center;
            margin-bottom: 2rem;
            color: white;
        }

        .header h1 {
            font-size: 2.5rem;
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
            padding: 0.75rem;
            border-radius: 0.75rem;
            backdrop-filter: blur(10px);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .navigation-bar {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1.5rem;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            text-decoration: none;
            border-radius: 0.5rem;
            font-weight: 500;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s;
        }

        .btn:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        .btn-primary {
            background: var(--primary-color);
            border-color: var(--primary-color);
        }

        .btn-primary:hover {
            background: var(--primary-dark);
        }

        .logger-panel {
            background: var(--surface);
            border-radius: 1rem;
            box-shadow: var(--shadow);
            overflow: hidden;
            min-height: 70vh;
            display: flex;
            flex-direction: column;
        }

        .logger-header {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
            color: white;
            padding: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .logger-title {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-size: 1.25rem;
            font-weight: 600;
        }

        .controls {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .control-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            transition: all 0.2s;
        }

        .control-btn:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
        }

        .status-dot {
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

        .logger-content {
            flex: 1;
            background: #1a1a1a;
            color: #e2e8f0;
            font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
            font-size: 0.9rem;
            overflow: auto;
            padding: 0;
        }

        .log-entry {
            padding: 0.5rem 1rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
            transition: background-color 0.2s;
        }

        .log-entry:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .log-timestamp {
            color: #64748b;
            font-size: 0.8rem;
            min-width: 180px;
            flex-shrink: 0;
        }

        .log-level {
            padding: 0.125rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-weight: 600;
            min-width: 60px;
            text-align: center;
            flex-shrink: 0;
        }

        .log-level.INFO {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
        }

        .log-level.WARNING {
            background: rgba(245, 158, 11, 0.2);
            color: #f59e0b;
        }

        .log-level.ERROR {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
        }

        .log-level.DEBUG {
            background: rgba(148, 163, 184, 0.2);
            color: #94a3b8;
        }

        .log-message {
            flex: 1;
            word-break: break-word;
        }

        .log-placeholder {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 300px;
            color: #64748b;
            text-align: center;
            gap: 1rem;
        }

        .log-placeholder i {
            font-size: 3rem;
            opacity: 0.5;
        }

        /* Scrollbar styling */
        .logger-content::-webkit-scrollbar {
            width: 12px;
        }

        .logger-content::-webkit-scrollbar-track {
            background: #2a2a2a;
        }

        .logger-content::-webkit-scrollbar-thumb {
            background: #4a5568;
            border-radius: 6px;
        }

        .logger-content::-webkit-scrollbar-thumb:hover {
            background: #718096;
        }

        /* Responsive Design */
        @media (min-width: 1920px) {
            .container {
                max-width: 90%;
            }
        }

        @media (max-width: 768px) {
            .container {
                padding: 1rem 0.5rem;
            }

            .header h1 {
                font-size: 2rem;
                flex-direction: column;
                gap: 0.5rem;
            }

            .navigation-bar {
                gap: 0.5rem;
            }

            .btn {
                padding: 0.5rem 1rem;
                font-size: 0.875rem;
            }

            .controls {
                flex-direction: column;
                gap: 0.5rem;
            }

            .log-entry {
                flex-direction: column;
                gap: 0.5rem;
            }

            .log-timestamp {
                min-width: auto;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <div class="header-icon">
                    <i class="fas fa-terminal"></i>
                </div>
                Logger Output
            </h1>
            <p>Real-time system logs and debug information</p>
        </div>

        <div class="navigation-bar">
            <a href="/" class="btn btn-primary">
                <i class="fas fa-home"></i>
                Back to Chat
            </a>
            <a href="/agent_info" class="btn">
                <i class="fas fa-info-circle"></i>
                Agent Info
            </a>
            <a href="/clear" class="btn">
                <i class="fas fa-trash-alt"></i>
                Clear Memory
            </a>
        </div>

        <div class="logger-panel">
            <div class="logger-header">
                <div class="logger-title">
                    <i class="fas fa-stream"></i>
                    Live Log Stream
                </div>
                <div class="controls">
                    <div class="status-indicator">
                        <div class="status-dot"></div>
                        <span>Connected</span>
                    </div>
                    <button class="control-btn" onclick="clearLogs()">
                        <i class="fas fa-eraser"></i>
                        Clear
                    </button>
                    <button class="control-btn" onclick="toggleAutoScroll()" id="scroll-btn">
                        <i class="fas fa-arrow-down"></i>
                        Auto-scroll
                    </button>
                </div>
            </div>
            <div class="logger-content" id="logger-content">
                <div class="log-placeholder">
                    <i class="fas fa-hourglass-half"></i>
                    <div>
                        <p><strong>Waiting for log output...</strong></p>
                        <p>Log entries will appear here in real-time</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let autoScroll = true;
        let logCount = 0;
        const maxLogs = 25; // Limit to prevent memory issues

        // Connect to log stream
        const logEventSource = new EventSource('/stream_logs');
        
        logEventSource.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                
                if (data.error) {
                    addLogEntry('ERROR', 'Stream Error', data.error);
                    return;
                }
                
                if (data.log) {
                    parseAndAddLogEntry(data.log);
                }
            } catch (e) {
                console.error('Error parsing log data:', e);
            }
        };

        logEventSource.onerror = function(event) {
            addLogEntry('ERROR', 'Connection Error', 'Lost connection to log stream. Attempting to reconnect...');
        };

        function parseAndAddLogEntry(logLine) {
            // Parse log format: timestamp - logger - level - message
            const parts = logLine.split(' - ');
            if (parts.length >= 4) {
                const timestamp = parts[0];
                const logger = parts[1];
                const level = parts[2];
                const message = parts.slice(3).join(' - ');
                addLogEntry(level, timestamp, `[${logger}] ${message}`);
            } else {
                // Fallback for unparsed logs
                addLogEntry('INFO', new Date().toISOString(), logLine);
            }
        }

        function addLogEntry(level, timestamp, message) {
            const logContent = document.getElementById('logger-content');
            
            // Remove placeholder if it exists
            const placeholder = logContent.querySelector('.log-placeholder');
            if (placeholder) {
                placeholder.remove();
            }

            // Create log entry
            const logEntry = document.createElement('div');
            logEntry.className = 'log-entry';
            
            logEntry.innerHTML = `
                <div class="log-timestamp">${formatTimestamp(timestamp)}</div>
                <div class="log-level ${level.toUpperCase()}">${level.toUpperCase()}</div>
                <div class="log-message">${escapeHtml(message)}</div>
            `;

            logContent.appendChild(logEntry);
            logCount++;

            // Limit number of log entries
            if (logCount > maxLogs) {
                const firstEntry = logContent.querySelector('.log-entry');
                if (firstEntry) {
                    firstEntry.remove();
                    logCount--;
                }
            }

            // Auto-scroll to bottom
            if (autoScroll) {
                logContent.scrollTop = logContent.scrollHeight;
            }
        }

        function formatTimestamp(timestamp) {
            try {
                const date = new Date(timestamp);
                return date.toLocaleTimeString('en-US', { 
                    hour12: false,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                }) + '.' + String(date.getMilliseconds()).padStart(3, '0');
            } catch (e) {
                return timestamp;
            }
        }

        function escapeHtml(unsafe) {
            return unsafe
                 .replace(/&/g, "&amp;")
                 .replace(/</g, "&lt;")
                 .replace(/>/g, "&gt;")
                 .replace(/"/g, "&quot;")
                 .replace(/'/g, "&#039;");
        }

        function clearLogs() {
            const logContent = document.getElementById('logger-content');
            logContent.innerHTML = `
                <div class="log-placeholder">
                    <i class="fas fa-hourglass-half"></i>
                    <div>
                        <p><strong>Logs cleared</strong></p>
                        <p>New log entries will appear here</p>
                    </div>
                </div>
            `;
            logCount = 0;
        }

        function toggleAutoScroll() {
            autoScroll = !autoScroll;
            const btn = document.getElementById('scroll-btn');
            
            if (autoScroll) {
                btn.innerHTML = '<i class="fas fa-arrow-down"></i> Auto-scroll';
                const logContent = document.getElementById('logger-content');
                logContent.scrollTop = logContent.scrollHeight;
            } else {
                btn.innerHTML = '<i class="fas fa-pause"></i> Manual';
            }
        }

        // Handle page unload
        window.addEventListener('beforeunload', function() {
            if (logEventSource) {
                logEventSource.close();
            }
        });
    </script>
</body>
</html>
"""
