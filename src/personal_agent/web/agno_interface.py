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
    raw_agent_info = agno_agent.get_agent_info() if agno_agent else {}

    if logger:
        logger.info(f"Retrieved agent info: {raw_agent_info}")

    # Process agent info for better display
    agent_info = {}
    for key, value in raw_agent_info.items():
        if isinstance(value, dict):
            # Format dictionary values nicely
            if key == "mcp_servers" and value:
                agent_info[key] = f"{len(value)} servers configured"
                # Add server details to available tools
            else:
                agent_info[key] = f"{len(value)} items" if value else "None configured"
        elif isinstance(value, list):
            agent_info[key] = f"{len(value)} items" if value else "None"
        else:
            agent_info[key] = value

    # Get available tools from the agno agent
    available_tools = []
    if agno_agent:
        try:
            # Extract MCP server information
            mcp_servers = raw_agent_info.get("mcp_servers", {})
            if isinstance(mcp_servers, dict) and mcp_servers:
                for server_name, server_info in mcp_servers.items():
                    if isinstance(server_info, dict):
                        # Check for tools in different possible structures
                        tools = server_info.get("tools", [])
                        if not tools:
                            # Try alternative structures
                            tools = server_info.get("available_tools", [])
                        if not tools and "tool_count" in server_info:
                            tools_count = server_info["tool_count"]
                        else:
                            tools_count = len(tools) if tools else "Unknown"
                        
                        if tools_count == 0 or tools_count == "Unknown":
                            available_tools.append(f"{server_name}: Connected")
                        else:
                            available_tools.append(f"{server_name}: {tools_count} tools")
                    else:
                        available_tools.append(f"{server_name}: Active")
            elif isinstance(mcp_servers, int) and mcp_servers > 0:
                available_tools.append(f"MCP Servers: {mcp_servers}")
            
            # Only add memory system if it's actually enabled and not Weaviate
            memory_type = raw_agent_info.get("memory_type", "")
            if raw_agent_info.get("memory_enabled") and memory_type and "weaviate" not in memory_type.lower():
                available_tools.append(f"{memory_type} Memory System")

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
        mcp_servers_count=len(raw_agent_info.get("mcp_servers", {})) if isinstance(raw_agent_info.get("mcp_servers"), dict) else raw_agent_info.get("mcp_servers", 0),
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
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-color: #2563eb;
                --primary-dark: #1d4ed8;
                --primary-light: #3b82f6;
                --success-color: #10b981;
                --warning-color: #f59e0b;
                --danger-color: #ef4444;
                --background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --surface: #ffffff;
                --surface-alt: #f8fafc;
                --text-primary: #1e293b;
                --text-secondary: #64748b;
                --text-muted: #94a3b8;
                --border-color: #e2e8f0;
                --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
                --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
                --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
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
                min-height: 100vh;
                line-height: 1.6;
                padding: 2rem 1rem;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
            }

            .header {
                text-align: center;
                margin-bottom: 3rem;
                color: white;
            }

            .header h1 {
                font-size: 3rem;
                font-weight: 700;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 1rem;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }

            .header .robot-icon {
                background: linear-gradient(135deg, #667eea, #764ba2);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
            }

            .header p {
                font-size: 1.2rem;
                opacity: 0.9;
                font-weight: 300;
            }

            .agent-status {
                background: var(--surface);
                border-radius: 1.5rem;
                padding: 2rem;
                margin-bottom: 2rem;
                box-shadow: var(--shadow-xl);
                border: 1px solid var(--border-color);
                position: relative;
                overflow: hidden;
            }

            .agent-status::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, var(--primary-color), var(--success-color), var(--warning-color));
            }

            .status-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
                margin-top: 1.5rem;
            }

            .status-item {
                text-align: center;
                padding: 1.5rem;
                background: var(--surface-alt);
                border-radius: 1rem;
                border: 1px solid var(--border-color);
                transition: all 0.3s ease;
            }

            .status-item:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-lg);
            }

            .status-icon {
                font-size: 2.5rem;
                margin-bottom: 1rem;
                display: block;
            }

            .status-icon.active {
                color: var(--success-color);
                animation: pulse 2s infinite;
            }

            .status-icon.warning {
                color: var(--warning-color);
            }

            .status-icon.info {
                color: var(--primary-color);
            }

            .status-label {
                font-weight: 600;
                color: var(--text-primary);
                margin-bottom: 0.5rem;
            }

            .status-value {
                color: var(--text-secondary);
                font-size: 0.9rem;
            }

            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 2rem;
                margin-bottom: 2rem;
            }

            .info-card {
                background: var(--surface);
                border-radius: 1.5rem;
                padding: 2rem;
                box-shadow: var(--shadow-lg);
                border: 1px solid var(--border-color);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }

            .info-card:hover {
                transform: translateY(-4px);
                box-shadow: var(--shadow-xl);
            }

            .info-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: var(--primary-color);
            }

            .card-header {
                display: flex;
                align-items: center;
                gap: 1rem;
                margin-bottom: 1.5rem;
                padding-bottom: 1rem;
                border-bottom: 1px solid var(--border-color);
            }

            .card-icon {
                width: 50px;
                height: 50px;
                background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
                border-radius: 1rem;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 1.5rem;
                box-shadow: var(--shadow);
            }

            .card-title {
                font-size: 1.4rem;
                font-weight: 600;
                color: var(--text-primary);
            }

            .card-content {
                color: var(--text-secondary);
                line-height: 1.7;
            }

            .config-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.75rem 0;
                border-bottom: 1px solid var(--border-color);
            }

            .config-item:last-child {
                border-bottom: none;
            }

            .config-label {
                font-weight: 500;
                color: var(--text-primary);
            }

            .config-value {
                color: var(--text-secondary);
                font-family: 'Monaco', 'Menlo', monospace;
                background: var(--surface-alt);
                padding: 0.25rem 0.5rem;
                border-radius: 0.375rem;
                font-size: 0.875rem;
            }

            .capabilities-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1rem;
            }

            .capability-item {
                display: flex;
                align-items: center;
                gap: 1rem;
                padding: 1rem;
                background: var(--surface-alt);
                border-radius: 0.75rem;
                border: 1px solid var(--border-color);
                transition: all 0.2s ease;
            }

            .capability-item:hover {
                background: white;
                transform: translateX(4px);
                box-shadow: var(--shadow);
            }

            .capability-icon {
                width: 40px;
                height: 40px;
                background: linear-gradient(135deg, var(--success-color), #34d399);
                border-radius: 0.75rem;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 1.1rem;
                flex-shrink: 0;
            }

            .capability-text {
                font-weight: 500;
                color: var(--text-primary);
            }

            .features-list {
                list-style: none;
                padding: 0;
            }

            .feature-item {
                display: flex;
                align-items: center;
                gap: 1rem;
                padding: 1rem 0;
                border-bottom: 1px solid var(--border-color);
                transition: all 0.2s ease;
            }

            .feature-item:last-child {
                border-bottom: none;
            }

            .feature-item:hover {
                background: var(--surface-alt);
                margin: 0 -1rem;
                padding: 1rem;
                border-radius: 0.5rem;
            }

            .feature-icon {
                width: 35px;
                height: 35px;
                background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
                border-radius: 0.5rem;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 1rem;
                flex-shrink: 0;
            }

            .feature-text {
                font-weight: 500;
                color: var(--text-primary);
            }

            .action-buttons {
                display: flex;
                gap: 1rem;
                justify-content: center;
                margin-top: 3rem;
                flex-wrap: wrap;
            }

            .btn {
                display: inline-flex;
                align-items: center;
                gap: 0.75rem;
                padding: 1rem 2rem;
                border-radius: 1rem;
                text-decoration: none;
                font-weight: 600;
                font-size: 1rem;
                transition: all 0.3s ease;
                border: none;
                cursor: pointer;
                box-shadow: var(--shadow);
            }

            .btn-primary {
                background: linear-gradient(135deg, var(--primary-color), var(--primary-light));
                color: white;
            }

            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: var(--shadow-lg);
                background: linear-gradient(135deg, var(--primary-dark), var(--primary-color));
            }

            .btn-secondary {
                background: var(--surface);
                color: var(--text-primary);
                border: 2px solid var(--border-color);
            }

            .btn-secondary:hover {
                background: var(--surface-alt);
                border-color: var(--primary-color);
                transform: translateY(-2px);
                box-shadow: var(--shadow-lg);
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.6; }
            }

            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .info-card {
                animation: fadeInUp 0.6s ease-out;
            }

            .info-card:nth-child(2) {
                animation-delay: 0.1s;
            }

            .info-card:nth-child(3) {
                animation-delay: 0.2s;
            }

            @media (max-width: 768px) {
                body {
                    padding: 1rem 0.5rem;
                }

                .header h1 {
                    font-size: 2rem;
                    flex-direction: column;
                    gap: 0.5rem;
                }

                .info-grid {
                    grid-template-columns: 1fr;
                }

                .status-grid {
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                }

                .capabilities-grid {
                    grid-template-columns: 1fr;
                }

                .action-buttons {
                    flex-direction: column;
                    align-items: center;
                }

                .btn {
                    width: 100%;
                    max-width: 300px;
                    justify-content: center;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>
                    <i class="fas fa-robot robot-icon"></i>
                    Agent Information
                </h1>
                <p>Comprehensive overview of your {{ agent_type }}</p>
            </div>

            <div class="agent-status">
                <div class="card-header">
                    <div class="card-icon">
                        <i class="fas fa-heartbeat"></i>
                    </div>
                    <div class="card-title">System Status</div>
                </div>
                <div class="status-grid">
                    <div class="status-item">
                        <i class="fas fa-power-off status-icon active"></i>
                        <div class="status-label">Agent Status</div>
                        <div class="status-value">Online & Ready</div>
                    </div>
                    <div class="status-item">
                        <i class="fas fa-brain status-icon {{ 'active' if agent_info.get('memory_enabled') else 'warning' }}"></i>
                        <div class="status-label">Memory System</div>
                        <div class="status-value">{{ 'Connected' if agent_info.get('memory_enabled') else 'Disconnected' }}</div>
                    </div>
                    <div class="status-item">
                        <i class="fas fa-plug status-icon info"></i>
                        <div class="status-label">MCP Servers</div>
                        <div class="status-value">{{ mcp_servers_count }} Active</div>
                    </div>
                    <div class="status-item">
                        <i class="fas fa-cogs status-icon active"></i>
                        <div class="status-label">Framework</div>
                        <div class="status-value">Agno v2.0</div>
                    </div>
                </div>
            </div>

            <div class="info-grid">
                <div class="info-card">
                    <div class="card-header">
                        <div class="card-icon">
                            <i class="fas fa-cogs"></i>
                        </div>
                        <div class="card-title">Configuration</div>
                    </div>
                    <div class="card-content">
                        <div class="config-item">
                            <span class="config-label">Agent Type</span>
                            <span class="config-value">{{ agent_type }}</span>
                        </div>
                        {% for key, value in agent_info.items() %}
                        <div class="config-item">
                            <span class="config-label">{{ key.replace('_', ' ').title() }}</span>
                            <span class="config-value">{{ value }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                {% if available_tools %}
                <div class="info-card">
                    <div class="card-header">
                        <div class="card-icon">
                            <i class="fas fa-toolbox"></i>
                        </div>
                        <div class="card-title">Available Capabilities</div>
                    </div>
                    <div class="card-content">
                        <div class="capabilities-grid">
                            {% for tool in available_tools %}
                            <div class="capability-item">
                                <div class="capability-icon">
                                    <i class="fas fa-check"></i>
                                </div>
                                <div class="capability-text">{{ tool }}</div>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
                {% endif %}

                <div class="info-card">
                    <div class="card-header">
                        <div class="card-icon">
                            <i class="fas fa-rocket"></i>
                        </div>
                        <div class="card-title">Framework Features</div>
                    </div>
                    <div class="card-content">
                        <ul class="features-list">
                            <li class="feature-item">
                                <div class="feature-icon">
                                    <i class="fas fa-rocket"></i>
                                </div>
                                <div class="feature-text">Async/Await Operations</div>
                            </li>
                            <li class="feature-item">
                                <div class="feature-icon">
                                    <i class="fas fa-plug"></i>
                                </div>
                                <div class="feature-text">Native MCP Integration</div>
                            </li>
                            <li class="feature-item">
                                <div class="feature-icon">
                                    <i class="fas fa-brain"></i>
                                </div>
                                <div class="feature-text">Agno Memory System</div>
                            </li>
                            <li class="feature-item">
                                <div class="feature-icon">
                                    <i class="fas fa-tools"></i>
                                </div>
                                <div class="feature-text">Multi-tool Coordination</div>
                            </li>
                            <li class="feature-item">
                                <div class="feature-icon">
                                    <i class="fas fa-shield-alt"></i>
                                </div>
                                <div class="feature-text">Error Handling & Recovery</div>
                            </li>
                            <li class="feature-item">
                                <div class="feature-icon">
                                    <i class="fas fa-sync-alt"></i>
                                </div>
                                <div class="feature-text">Real-time Processing</div>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="action-buttons">
                <a href="/" class="btn btn-primary">
                    <i class="fas fa-arrow-left"></i>
                    <span>Back to Agent</span>
                </a>
                <a href="/clear" class="btn btn-secondary">
                    <i class="fas fa-trash-alt"></i>
                    <span>Clear Memory</span>
                </a>
            </div>
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
