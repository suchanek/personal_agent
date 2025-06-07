# -*- coding: utf-8 -*-
# pylint: disable=C0302, W0603, C0103, C0301, W0718
"""
Web interface module for the Personal AI Agent using agno framework.

This module provides a Flask-based web interface that works with agno agents,
maintaining the same UI and functionality as the original interface.py.
"""

import asyncio
import re
import threading
from typing import TYPE_CHECKING

from flask import Flask, render_template_string, request

from ..config import USE_MCP


# Function to check if memory system is available
def is_memory_available() -> bool:
    """Check if agno memory management is available."""
    return agno_agent is not None  # Memory is available when agent is configured


if TYPE_CHECKING:
    from logging import Logger

    from agno.agent import Agent

# These will be injected by the main module
app: Flask = None
agno_agent: "Agent" = None  # Now using native agno Agent
logger: "Logger" = None

# Memory function references - no longer needed with native agno agent
# The native agent handles memory automatically


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    :return: Configured Flask application
    """
    flask_app = Flask(__name__)
    return flask_app


def run_async_in_thread(coroutine):
    """
    Run an async coroutine in a separate thread with its own event loop.

    :param coroutine: The coroutine to run
    :return: The result of the coroutine
    """

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


def remove_thinking_tags(text: str) -> str:
    """
    Remove <think>...</think> tags from the response text.

    :param text: The response text that may contain thinking tags
    :return: Clean text with thinking tags removed
    """
    if not text:
        return text

    # Remove <think>...</think> blocks using regex
    # This handles multiline content within thinking tags
    clean_text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    # Clean up any extra whitespace that might be left
    clean_text = re.sub(r"\n\s*\n\s*\n", "\n\n", clean_text)
    clean_text = clean_text.strip()

    return clean_text


def index():
    """
    Main route for the agent interface using agno framework.

    :return: Rendered HTML template
    """
    if logger:
        logger.info(f"Index route accessed - method: {request.method}")

    response = None

    if request.method == "POST":
        user_input = request.form.get("query", "")

        if logger:
            logger.info(
                f"POST request received - user_input: '{user_input[:100]}{'...' if len(user_input) > 100 else ''}'"
            )

        if user_input:
            try:
                # Native agno agent handles memory/knowledge automatically
                if logger:
                    logger.info(
                        "Native agno agent will handle memory and knowledge automatically"
                    )

                # Execute agno agent directly (agent streams thinking with <think> tags)
                try:
                    if logger:
                        logger.info("Starting agno agent execution")

                    # Use agno agent with async execution
                    response = run_async_in_thread(agno_agent.arun(user_input))

                    if hasattr(response, "content"):
                        response = response.content

                    # Remove thinking tags from response to prevent HTML styling
                    if response:
                        response = remove_thinking_tags(str(response))

                    if logger:
                        logger.info(
                            f"Agno agent response received: '{str(response)[:100]}{'...' if len(str(response)) > 100 else ''}'"
                        )

                    # Remove thinking tags from the response
                    response = remove_thinking_tags(response)

                except Exception as e:
                    if logger:
                        logger.error(f"Error during agno agent execution: {e}")
                    response = f"Sorry, I encountered an error: {str(e)}"

            except Exception as e:
                if logger:
                    logger.error(f"Error in request processing: {e}")
                response = f"Sorry, I encountered an error: {str(e)}"

    # Render the main template
    return render_template_string(
        get_main_template(),
        response=response,
        show_memory_status=is_memory_available(),
        use_mcp=USE_MCP,
    )


def agent_info_route():
    """
    Route to provide agent information.

    :return: JSON response with agent information
    """
    agent_type = "Native Agno Framework Agent"
    agent_info = {}

    if agno_agent:
        try:
            # Get basic agent information
            if hasattr(agno_agent, "name"):
                agent_info["name"] = agno_agent.name
            if hasattr(agno_agent, "description"):
                agent_info["description"] = agno_agent.description
            if hasattr(agno_agent, "instructions"):
                agent_info["instructions"] = (
                    agno_agent.instructions[:200] + "..."
                    if len(agno_agent.instructions) > 200
                    else agno_agent.instructions
                )
        except Exception as e:
            if logger:
                logger.warning(f"Could not get agent info: {e}")
            agent_info["error"] = f"Could not retrieve agent info: {str(e)}"

    return {
        "agent_type": agent_type,
        "agent_info": agent_info,
    }


def get_main_template():
    """
    Generate the main HTML template for the agent interface.

    :return: HTML template string
    """
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal AI Agent</title>
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #2d3748;
        }

        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }

        h1 {
            color: #2d3748;
            text-align: center;
            margin-bottom: 30px;
            font-weight: 700;
            font-size: 2.5em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .status-indicators {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }

        .status-indicator {
            padding: 8px 16px;
            border-radius: 25px;
            font-size: 0.9em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .status-connected {
            background: linear-gradient(135deg, #48bb78, #38a169);
            color: white;
        }

        .status-disconnected {
            background: linear-gradient(135deg, #ed8936, #dd6b20);
            color: white;
        }

        .form-container {
            margin-bottom: 30px;
        }

        textarea {
            width: 100%;
            min-height: 120px;
            padding: 20px;
            border: 2px solid #e2e8f0;
            border-radius: 15px;
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
            box-sizing: border-box;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.8);
        }

        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            background: rgba(255, 255, 255, 1);
        }

        .button-container {
            text-align: center;
            margin-top: 20px;
        }

        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }

        button:active {
            transform: translateY(0);
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        .response-container {
            margin-top: 30px;
            padding: 25px;
            background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
            border-radius: 15px;
            border-left: 5px solid #667eea;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        }

        .response-container h3 {
            margin-top: 0;
            color: #2d3748;
            font-size: 1.3em;
            font-weight: 600;
        }

        .response-content {
            background: white;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e2e8f0;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 14px;
            line-height: 1.6;
            max-height: 500px;
            overflow-y: auto;
        }

        .footer {
            text-align: center;
            margin-top: 40px;
            color: #718096;
            font-size: 0.9em;
        }

        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .container {
                padding: 20px;
            }
            
            h1 {
                font-size: 2em;
            }
            
            .status-indicators {
                gap: 10px;
            }
            
            .status-indicator {
                font-size: 0.8em;
                padding: 6px 12px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Personal AI Agent</h1>
        
        <div class="status-indicators">
            <div class="status-indicator status-connected">
                🚀 Agno Framework Active
            </div>
            {% if show_memory_status %}
                <div class="status-indicator status-connected">
                    🧠 Agno Memory Active
                </div>
            {% else %}
                <div class="status-indicator status-disconnected">
                    🧠 Memory Unavailable
                </div>
            {% endif %}
            {% if use_mcp %}
                <div class="status-indicator status-connected">
                    🔗 MCP Tools Available
                </div>
            {% else %}
                <div class="status-indicator status-disconnected">
                    🔗 MCP Tools Disabled
                </div>
            {% endif %}
        </div>

        <form method="post" id="agentForm">
            <div class="form-container">
                <textarea 
                    name="query" 
                    placeholder="Ask me anything... I can help with research, analysis, creative tasks, and more!"
                    required
                    id="queryInput"
                ></textarea>
            </div>
            <div class="button-container">
                <button type="submit" id="submitButton">
                    Send Message
                </button>
            </div>
        </form>

        {% if response %}
        <div class="response-container">
            <h3>🎯 Agent Response</h3>
            <div class="response-content">{{ response }}</div>
        </div>
        {% endif %}

        <div class="footer">
            <p>Powered by Agno Framework | Native Agent with Streaming Capabilities</p>
        </div>
    </div>

    <script>
        document.getElementById('agentForm').addEventListener('submit', function(e) {
            const submitButton = document.getElementById('submitButton');
            const queryInput = document.getElementById('queryInput');
            
            if (queryInput.value.trim() === '') {
                e.preventDefault();
                return;
            }
            
            // Show loading state on button only
            submitButton.disabled = true;
            submitButton.innerHTML = 'Processing...';
        });

        // Auto-resize textarea
        const textarea = document.getElementById('queryInput');
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });

        // Focus on textarea when page loads
        window.addEventListener('load', function() {
            textarea.focus();
        });
    </script>
</body>
</html>
    """


def get_error_template():
    """
    Generate the error HTML template.

    :return: HTML template string for error display
    """
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal AI Agent - Error</title>
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #2d3748;
        }

        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            text-align: center;
        }

        h1 {
            color: #e53e3e;
            margin-bottom: 20px;
            font-size: 2.5em;
        }

        .error-message {
            background: #fed7d7;
            border: 1px solid #feb2b2;
            color: #c53030;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }

        .back-button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-weight: 600;
            margin-top: 20px;
            transition: all 0.3s ease;
        }

        .back-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚠️ Error</h1>
        <div class="error-message">
            <strong>An error occurred:</strong><br>
            {{ error_message }}
        </div>
        <a href="/" class="back-button">← Back to Agent</a>
    </div>
</body>
</html>
    """


def register_routes(flask_app: Flask):
    """
    Register routes with the Flask application.

    :param flask_app: Flask application instance
    """
    flask_app.route("/", methods=["GET", "POST"])(index)
    flask_app.route("/agent-info", methods=["GET"])(agent_info_route)
