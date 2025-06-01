"""
Web interface module for the Personal AI Agent.

This module provides the Flask-based web interface for interacting with the agent,
including HTML templates, routes, and styling.
"""

from typing import TYPE_CHECKING

from flask import Flask, render_template_string, request

if TYPE_CHECKING:
    from logging import Logger

    from langchain.agents import AgentExecutor

# These will be injected by the main module
app: Flask = None
agent_executor: "AgentExecutor" = None
logger: "Logger" = None
query_knowledge_base = None
store_interaction = None
clear_knowledge_base = None


def create_app() -> Flask:
    """Create and configure the Flask application."""
    flask_app = Flask(__name__)
    return flask_app


def register_routes(flask_app: Flask, executor, log, query_kb, store_int, clear_kb):
    """Register Flask routes with the application."""
    global app, agent_executor, logger, query_knowledge_base, store_interaction, clear_knowledge_base

    app = flask_app
    agent_executor = executor
    logger = log
    query_knowledge_base = query_kb
    store_interaction = store_int
    clear_knowledge_base = clear_kb

    app.add_url_rule("/", "index", index, methods=["GET", "POST"])
    app.add_url_rule("/clear", "clear_kb", clear_kb_route)


def index():
    """Main route for the agent interface."""
    response = None
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

            # Query knowledge base for context (used internally only)
            try:
                # Call the function directly with proper parameters
                context = query_knowledge_base.invoke({"query": user_input, "limit": 3})
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
                    agent_thoughts.append(
                        "📝 No previous context found, starting fresh"
                    )

                # Add processing thoughts
                agent_thoughts.extend(
                    [
                        "🧠 Analyzing request with AI reasoning",
                        "🔧 Preparing tools and capabilities",
                    ]
                )

                # Execute agent
                try:
                    result = agent_executor.invoke(
                        {"input": user_input, "context": context_str}
                    )

                    # Enhance thoughts with more realistic processing steps
                    if len(agent_thoughts) < 8:
                        intermediate_thoughts = [
                            "🔍 Examining available tools",
                            "📊 Processing information patterns",
                            "💡 Formulating response strategy",
                            "🎯 Executing chosen approach",
                        ]

                        for thought in intermediate_thoughts:
                            if (
                                thought not in agent_thoughts
                                and len(agent_thoughts) < 8
                            ):
                                agent_thoughts.append(thought)

                    # If we still have very few thoughts, add some generic ones
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

                # Clean any thinking process content from the response
                response = clean_response_from_thinking_process(response)

                # Remove duplicate final thoughts and add completion
                agent_thoughts = list(dict.fromkeys(agent_thoughts))
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
        get_main_template(),
        response=response,
        agent_thoughts=agent_thoughts,
    )


def clear_kb_route():
    """Route to clear the knowledge base."""
    try:
        result = clear_knowledge_base.invoke({})
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


def get_main_template() -> str:
    """Get the main HTML template for the agent interface."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Personal AI Agent</title>
        <style>
            /* General styles */
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f4f4f9;
                color: #333;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .header {
                text-align: center;
                margin-bottom: 20px;
            }
            .content {
                background: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .response-section {
                margin-top: 20px;
            }
            .response-content {
                white-space: pre-wrap;
                line-height: 1.6;
                color: #444;
            }
            .btn {
                display: inline-block;
                padding: 10px 20px;
                margin-top: 20px;
                background-color: #007bff;
                color: #fff;
                text-decoration: none;
                border-radius: 5px;
                transition: background-color 0.3s;
            }
            .btn:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Personal AI Agent</h1>
            </div>
            <div class="content">
                <form method="post">
                    <label for="query">Enter your query:</label>
                    <textarea id="query" name="query" rows="4" style="width: 100%;"></textarea>
                    <button type="submit" class="btn">Submit</button>
                </form>
                {% if response %}
                <div class="response-section">
                    <h2>Response</h2>
                    <div class="response-content">{{ response }}</div>
                </div>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    """


def get_success_template() -> str:
    """Get the success HTML template for knowledge base clearing."""
    return """
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

    # Strip leading/trailing whitespace
    cleaned_response = cleaned_response.strip()

    return cleaned_response
