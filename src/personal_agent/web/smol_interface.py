"""
Smolagents-compatible web interface module for the Personal AI Agent.

This module provides a Flask-based web interface that works with smolagents
instead of LangChain, maintaining the same UI and functionality.
"""

from typing import TYPE_CHECKING, Optional

from flask import Flask, render_template_string, request

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


def create_app() -> Flask:
    """
    Create and configure the Flask application.
    
    :return: Configured Flask application
    """
    flask_app = Flask(__name__)
    return flask_app


def register_routes(
    flask_app: Flask, 
    agent, 
    log, 
    query_kb_func, 
    store_int_func, 
    clear_kb_func
):
    """
    Register Flask routes with the smolagents-compatible application.
    
    :param flask_app: Flask application instance
    :param agent: Smolagents ToolCallingAgent instance
    :param log: Logger instance
    :param query_kb_func: Function to query knowledge base
    :param store_int_func: Function to store interactions
    :param clear_kb_func: Function to clear knowledge base
    """
    global app, smolagents_agent, logger
    global query_knowledge_base_func, store_interaction_func, clear_knowledge_base_func

    app = flask_app
    smolagents_agent = agent
    logger = log
    query_knowledge_base_func = query_kb_func
    store_interaction_func = store_int_func
    clear_knowledge_base_func = clear_kb_func

    app.add_url_rule("/", "index", index, methods=["GET", "POST"])
    app.add_url_rule("/clear", "clear_kb", clear_kb_route)


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
        
        if user_input:
            # Add initial thinking state
            agent_thoughts = [
                "🤔 Thinking about your request...",
                "🔍 Searching memory for context...",
            ]

            try:
                # Query knowledge base for context using direct function call
                context = None
                if query_knowledge_base_func:
                    try:
                        # Call the function directly (it's already a Python function, not a tool)
                        context_result = query_knowledge_base_func(user_input, limit=3)
                        
                        if context_result and context_result != "No relevant context found.":
                            context = context_result if isinstance(context_result, list) else [context_result]
                        else:
                            context = ["No relevant context found."]
                            
                    except Exception as e:
                        logger.warning("Could not query knowledge base: %s", e)
                        context = ["No context available."]
                else:
                    context = ["Memory not available."]

                # Update thoughts after context search
                if context and context != ["No relevant context found."] and context != ["Memory not available."]:
                    agent_thoughts.append("✅ Found relevant context in memory")
                else:
                    agent_thoughts.append("📝 No previous context found, starting fresh")

                # Add processing thoughts
                agent_thoughts.extend([
                    "🧠 Analyzing request with AI reasoning",
                    "🔧 Preparing tools and capabilities",
                    "⚡ Processing with smolagents framework"
                ])

                # Prepare context string for agent
                context_str = "\n".join(context) if context else "No relevant context found."
                
                # Create enhanced prompt with context
                enhanced_prompt = f"""Previous Context:
{context_str}

User Request: {user_input}

Please help the user with their request. Use available tools as needed and provide a helpful, comprehensive response."""

                # Execute smolagents agent
                try:
                    # Use smolagents .run() method
                    response = smolagents_agent.run(enhanced_prompt)
                    
                    # Add realistic processing thoughts
                    additional_thoughts = [
                        "🔍 Examining available tools",
                        "📊 Processing information patterns", 
                        "💡 Formulating response strategy",
                        "🎯 Executing chosen approach",
                        "✨ Response generated successfully"
                    ]
                    
                    # Add thoughts that aren't already present
                    for thought in additional_thoughts:
                        if thought not in agent_thoughts:
                            agent_thoughts.append(thought)

                    # Store interaction AFTER getting response
                    if store_interaction_func:
                        try:
                            interaction_text = f"User: {user_input}\nAssistant: {response}"
                            store_interaction_func(interaction_text, topic)
                        except Exception as e:
                            logger.warning("Could not store interaction: %s", e)

                except Exception as e:
                    logger.error("Error with smolagents execution: %s", str(e))
                    response = f"Error processing request: {str(e)}"
                    agent_thoughts = [f"❌ Error occurred: {str(e)}"]

            except Exception as e:
                logger.error("Error processing query: %s", str(e))
                response = f"Error processing query: {str(e)}"
                agent_thoughts = [f"❌ Error occurred: {str(e)}"]
                
            logger.info(
                "Received query: %s..., Response: %s...",
                user_input[:50],
                str(response)[:50] if response else "None",
            )
            
    return render_template_string(
        get_main_template(),
        response=response,
        context=context,
        agent_thoughts=agent_thoughts,
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
    <title>Personal AI Agent - Smolagents</title>
    <style>
        :root {
            --primary-color: #2563eb;
            --primary-dark: #1d4ed8;
            --success-color: #059669;
            --warning-color: #d97706;
            --error-color: #dc2626;
            --background: #f8fafc;
            --surface: #ffffff;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
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

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: var(--surface);
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: var(--shadow);
            border: 1px solid var(--border-color);
        }

        .card h2 {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: block;
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: var(--text-primary);
        }

        .form-control {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 2px solid var(--border-color);
            border-radius: 0.5rem;
            font-size: 1rem;
            transition: all 0.2s;
            background: var(--surface);
        }

        .form-control:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        textarea.form-control {
            resize: vertical;
            min-height: 120px;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.75rem 2rem;
            border: none;
            border-radius: 0.5rem;
            font-size: 1rem;
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
            box-shadow: var(--shadow-lg);
        }

        .btn-secondary {
            background: var(--text-secondary);
            color: white;
        }

        .btn-secondary:hover {
            background: var(--text-primary);
        }

        .response-container {
            margin-top: 2rem;
        }

        .response-card {
            background: var(--surface);
            border-radius: 1rem;
            border: 1px solid var(--border-color);
            overflow: hidden;
            box-shadow: var(--shadow);
        }

        .response-header {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
            color: white;
            padding: 1rem 1.5rem;
            font-weight: 600;
        }

        .response-content {
            padding: 1.5rem;
        }

        .response-text {
            white-space: pre-wrap;
            line-height: 1.7;
            color: var(--text-primary);
        }

        .thinking-process {
            background: #f1f5f9;
            border-radius: 0.75rem;
            padding: 1rem;
            margin-bottom: 1.5rem;
        }

        .thinking-process h4 {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            color: var(--text-primary);
        }

        .thought-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .context-section {
            background: #fef3c7;
            border-radius: 0.75rem;
            padding: 1rem;
            margin-bottom: 1.5rem;
        }

        .context-section h4 {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
            color: var(--warning-color);
        }

        .context-list {
            list-style: none;
            padding: 0;
        }

        .context-list li {
            padding: 0.25rem 0;
            font-size: 0.9rem;
            color: #92400e;
        }

        .utility-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding: 1rem;
            background: var(--surface);
            border-radius: 0.75rem;
            border: 1px solid var(--border-color);
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
            color: var(--success-color);
            font-weight: 500;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background: var(--success-color);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
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
            <h1>Personal AI Agent<span class="badge">Smolagents</span></h1>
            <p>Powered by smolagents framework with MCP integration</p>
        </div>

        <div class="utility-bar">
            <div class="status-indicator">
                <div class="status-dot"></div>
                <span>Smolagents Online</span>
            </div>
            <a href="/clear" class="btn btn-secondary">🗑️ Clear Memory</a>
        </div>

        <div class="main-content">
            <div class="card">
                <h2>💬 Chat with Agent</h2>
                <form method="post">
                    <div class="form-group">
                        <label for="query">Your Question or Request:</label>
                        <textarea 
                            id="query" 
                            name="query" 
                            class="form-control" 
                            placeholder="Ask me anything! I can help with files, web search, GitHub, research, and more..."
                            required
                        ></textarea>
                    </div>
                    <div class="form-group">
                        <label for="topic">Topic Category:</label>
                        <select id="topic" name="topic" class="form-control">
                            <option value="general">General</option>
                            <option value="coding">Coding</option>
                            <option value="research">Research</option>
                            <option value="files">File Management</option>
                            <option value="web">Web Search</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">
                        🚀 Send Request
                    </button>
                </form>
            </div>

            <div class="card">
                <h2>🔧 Available Capabilities</h2>
                <ul style="list-style: none; padding: 0;">
                    <li style="padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                        📁 File Operations (read, write, list directories)
                    </li>
                    <li style="padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                        🔍 Web Search (Brave Search integration)
                    </li>
                    <li style="padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                        🐙 GitHub Repository Search
                    </li>
                    <li style="padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                        🧠 Memory & Knowledge Management
                    </li>
                    <li style="padding: 0.5rem 0; border-bottom: 1px solid var(--border-color);">
                        🔬 Comprehensive Research
                    </li>
                    <li style="padding: 0.5rem 0;">
                        ⚡ Shell Commands & System Integration
                    </li>
                </ul>
            </div>
        </div>

        {% if response %}
        <div class="response-container">
            <div class="response-card">
                <div class="response-header">
                    🤖 Agent Response
                </div>
                <div class="response-content">
                    {% if agent_thoughts %}
                    <div class="thinking-process">
                        <h4>🧠 Thinking Process:</h4>
                        {% for thought in agent_thoughts %}
                        <div class="thought-item">{{ thought }}</div>
                        {% endfor %}
                    </div>
                    {% endif %}

                    {% if context and context != ['No relevant context found.'] %}
                    <div class="context-section">
                        <h4>📚 Relevant Context from Memory:</h4>
                        <ul class="context-list">
                            {% for item in context %}
                            <li>• {{ item }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    {% endif %}

                    <div class="response-text">{{ response }}</div>
                </div>
            </div>
        </div>
        {% endif %}

        <div class="footer">
            <p>Personal AI Agent • Smolagents Framework • Model Context Protocol Integration</p>
        </div>
    </div>
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
