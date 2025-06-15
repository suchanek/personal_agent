# -*- coding: utf-8 -*-
# pylint: disable=C0302, W0603, C0103, C0301
"""
Web interface module for the Personal AI Agent using agno framework.

This module provides a simplified Flask-based web interface with a clean,
straightforward design focused on query input and response display.
"""

import asyncio
import logging
import threading
from typing import TYPE_CHECKING, Any, Callable, Optional

from flask import Flask, render_template_string, request

from ..core.memory import is_memory_connected

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


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    :return: Configured Flask application
    """
    flask_app = Flask(__name__)
    return flask_app


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

    logger.info("Starting route registration for simplified agno interface")

    app.add_url_rule("/", "index", index, methods=["GET", "POST"])
    app.add_url_rule("/clear", "clear_kb", clear_kb_route)
    app.add_url_rule("/agent_info", "agent_info", agent_info_route)

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
        error = result_container["error"]
        if isinstance(error, Exception):
            raise error  # pylint: disable=raising-bad-type
        else:
            raise RuntimeError(f"Async operation failed: {error}")

    if not result_container["done"]:
        raise TimeoutError("Async operation timed out")

    return result_container["result"]


def index():
    """
    Main route for the simplified agent interface.

    :return: Rendered HTML template
    """
    if logger:
        logger.info(f"Index route accessed - method: {request.method}")

    response = None
    error_message = None

    if request.method == "POST":
        user_input = request.form.get("query", "").strip()

        if logger:
            logger.info(f"POST request received - user_input: '{user_input[:100]}{'...' if len(user_input) > 100 else ''}'")

        if user_input:
            try:
                if logger:
                    logger.info("Starting agno agent processing")

                # Execute agno agent in a separate thread
                result_container = {"response": None, "error": None, "done": False}

                def agent_worker():
                    """Worker function to run agno agent in separate thread."""
                    try:
                        if logger:
                            logger.info("Agent worker thread started")

                        # Create enhanced prompt
                        enhanced_prompt = f"""User Request: {user_input}

Please help the user with their request. Use available MCP tools as needed and provide a helpful, comprehensive response."""

                        # Use agno agent with async execution
                        if logger:
                            logger.info("Creating new event loop for agno agent execution")

                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            if logger:
                                logger.info("Starting agno agent run")

                            agent_response = loop.run_until_complete(
                                agno_agent.run(enhanced_prompt)
                            )
                            result_container["response"] = agent_response

                            if logger:
                                logger.info(f"Agno agent completed successfully - response length: {len(str(agent_response))}")

                        finally:
                            loop.close()
                            if logger:
                                logger.info("Event loop closed after agno agent execution")

                    except Exception as e:
                        result_container["error"] = e
                        if logger:
                            logger.error(f"Error during agno agent processing: {str(e)}")
                    finally:
                        result_container["done"] = True

                # Start the agent in a separate thread
                agent_thread = threading.Thread(target=agent_worker)
                agent_thread.daemon = True
                agent_thread.start()

                # Wait for the agent to complete
                if logger:
                    logger.info("Waiting for agent thread to complete")

                agent_thread.join(timeout=60)  # Max 60 seconds wait

                error = result_container.get("error")
                if error is not None:
                    if logger:
                        logger.error(f"Agent thread returned error: {error}")
                    if isinstance(error, Exception):
                        raise error
                    else:
                        raise RuntimeError(f"Agent execution failed: {error}")

                response = result_container.get("response")
                if response is None:
                    if logger:
                        logger.error("Agent thread completed but returned no response")
                    raise RuntimeError("Agno agent execution timed out or returned no response")

                if logger:
                    logger.info(f"Successfully received response from agent thread - length: {len(str(response))}")

                # Store interaction AFTER getting response
                if store_interaction_func:
                    try:
                        if logger:
                            logger.info("Storing interaction in memory using async function")

                        # Use async function via thread
                        run_async_in_thread(store_interaction_func(user_input, response))

                        if logger:
                            logger.info("Interaction successfully stored in memory")

                    except Exception as e:
                        logger.warning("Could not store interaction: %s", e)
                else:
                    if logger:
                        logger.warning("No store_interaction_func available - skipping memory storage")

            except Exception as e:
                logger.error("Error processing query: %s", str(e))
                error_message = f"Error processing request: {str(e)}"

            if logger:
                logger.info(f"Request processing completed - user_input: '{user_input[:50]}...', response_length: {len(str(response)) if response else 0}")

        else:
            error_message = "Please enter a query."

    # Check memory connection status
    memory_status = is_memory_connected()

    return render_template_string(
        get_main_template(),
        response=response,
        error_message=error_message,
        memory_connected=memory_status,
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

            if agent_info.get("memory_enabled"):
                available_tools.append("Weaviate Memory")

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
    )


def get_main_template():
    """
    Get the main HTML template for the simplified interface.

    :return: HTML template string
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Personal AI Agent</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <style>
            :root {
                --primary-color: #2563eb;
                --primary-dark: #1d4ed8;
                --success-color: #059669;
                --danger-color: #dc2626;
                --background: #f8fafc;
                --surface: #ffffff;
                --text-primary: #1e293b;
                --text-secondary: #64748b;
                --border-color: #e2e8f0;
                --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
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
                background: var(--surface);
                border-bottom: 1px solid var(--border-color);
                padding: 1rem 2rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: var(--shadow);
            }

            .status-left {
                display: flex;
                align-items: center;
                gap: 2rem;
            }

            .status-item {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--text-secondary);
                font-size: 0.875rem;
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

            .brain-icon {
                color: {{ 'var(--brain-connected)' if memory_connected else 'var(--brain-disconnected)' }};
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
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }

            .main-content {
                display: grid;
                grid-template-columns: 1fr;
                gap: 2rem;
                max-width: 800px;
                margin: 0 auto;
            }

            .query-section {
                background: var(--surface);
                border-radius: 1rem;
                padding: 2rem;
                box-shadow: var(--shadow);
                border: 1px solid var(--border-color);
            }

            .section-title {
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 1.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                color: var(--text-primary);
            }

            .form-group {
                margin-bottom: 1.5rem;
            }

            .form-input {
                width: 100%;
                padding: 1rem;
                border: 2px solid var(--border-color);
                border-radius: 0.75rem;
                font-size: 1rem;
                transition: all 0.2s;
                background: var(--surface);
                resize: vertical;
                min-height: 120px;
                font-family: inherit;
            }

            .form-input:focus {
                outline: none;
                border-color: var(--primary-color);
                box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
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
                width: 100%;
                justify-content: center;
            }

            .submit-button:hover {
                background: var(--primary-dark);
            }

            .submit-button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            .response-section {
                background: var(--surface);
                border-radius: 1rem;
                padding: 2rem;
                box-shadow: var(--shadow);
                border: 1px solid var(--border-color);
            }

            .response-content {
                color: var(--text-secondary);
                line-height: 1.7;
                white-space: pre-wrap;
                word-wrap: break-word;
                background: #f8fafc;
                padding: 1.5rem;
                border-radius: 0.5rem;
                border-left: 4px solid var(--primary-color);
            }

            .error-message {
                background: #fef2f2;
                border: 1px solid #fecaca;
                border-left: 4px solid var(--danger-color);
                color: #991b1b;
                padding: 1rem;
                border-radius: 0.5rem;
                margin-bottom: 1rem;
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

            @media (max-width: 768px) {
                .container {
                    padding: 1rem;
                }

                .status-bar {
                    flex-direction: column;
                    gap: 1rem;
                    padding: 1rem;
                }

                .status-left {
                    flex-wrap: wrap;
                    justify-content: center;
                }

                .query-section,
                .response-section {
                    padding: 1.5rem;
                }
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
                    <span>Memory: {{ 'Connected' if memory_connected else 'Disconnected' }}</span>
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
            <div class="main-content">
                <div class="query-section">
                    <h2 class="section-title">
                        <i class="fas fa-comment-dots"></i>
                        Ask Your Agent
                    </h2>
                    
                    {% if error_message %}
                    <div class="error-message">
                        <i class="fas fa-exclamation-triangle"></i>
                        {{ error_message }}
                    </div>
                    {% endif %}

                    <form method="post" id="queryForm">
                        <div class="form-group">
                            <textarea 
                                id="query" 
                                name="query" 
                                class="form-input"
                                placeholder="Enter your question or request here... I can help with research, analysis, coding, and more using my MCP-powered tools."
                                required
                            ></textarea>
                        </div>
                        
                        <button type="submit" class="submit-button" id="submitBtn">
                            <i class="fas fa-paper-plane"></i>
                            <span>Send Query</span>
                        </button>
                    </form>
                </div>

                {% if response %}
                <div class="response-section">
                    <h2 class="section-title">
                        <i class="fas fa-robot"></i>
                        Agent Response
                    </h2>
                    <div class="response-content">{{ response }}</div>
                </div>
                {% endif %}
            </div>
        </div>

        <script>
            // Form submission handling
            const form = document.getElementById('queryForm');
            const submitBtn = document.getElementById('submitBtn');
            
            form.addEventListener('submit', function(e) {
                // Change button to loading state
                submitBtn.innerHTML = '<div class="loading"></div><span>Processing...</span>';
                submitBtn.disabled = true;
            });

            // Auto-resize textarea
            const textarea = document.getElementById('query');
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 300) + 'px';
            });

            // Focus on textarea when page loads
            window.addEventListener('load', function() {
                textarea.focus();
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
                background: #f8fafc;
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
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                text-align: center;
                max-width: 500px;
                width: 100%;
                border: 1px solid #e2e8f0;
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
                background: #f8fafc;
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
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                text-align: center;
                max-width: 500px;
                width: 100%;
                border: 1px solid #e2e8f0;
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
                background: #f8fafc;
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
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                border: 1px solid #e2e8f0;
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
