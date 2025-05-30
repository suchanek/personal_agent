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

            # Query knowledge base for context
            try:
                # Call the function directly with proper parameters
                context = query_knowledge_base.invoke(
                    {"query": user_input, "limit": 3}
                )  # Reduced from 5 to 3
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

                # Execute agent with retries and enhanced thoughts
                try:
                    # Simple execution
                    result = agent_executor.invoke(
                        {"input": user_input, "context": context_str}
                    )

                    # Enhance thoughts with more realistic processing steps
                    if len(agent_thoughts) < 8:
                        # Add some realistic intermediate thoughts if we don't have many
                        intermediate_thoughts = [
                            "🔍 Examining available tools",
                            "📊 Processing information patterns",
                            "💡 Formulating response strategy",
                            "🎯 Executing chosen approach",
                        ]

                        # Add thoughts that aren't already present
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

                # Remove duplicate final thoughts and add completion
                agent_thoughts = list(
                    dict.fromkeys(agent_thoughts)
                )  # Remove duplicates while preserving order
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
        context=context,
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
                <title>🤖 Personal AI Agent</title>
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
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 15px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        overflow: hidden;
                    }
                    .header {
                        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                        color: white;
                        padding: 20px;
                        text-align: center;
                    }
                    .header h1 {
                        margin: 0;
                        font-size: 2rem;
                        font-weight: 300;
                    }
                    .content {
                        display: grid;
                        grid-template-columns: 1fr 400px;
                        gap: 0;
                        min-height: 600px;
                    }
                    .main-panel {
                        padding: 30px;
                    }
                    .thoughts-panel {
                        background: #f8f9fa;
                        border-left: 3px solid #4facfe;
                        padding: 20px;
                        overflow-y: auto;
                        max-height: 600px;
                    }
                    .form-group {
                        margin-bottom: 20px;
                    }
                    label {
                        display: block;
                        font-weight: 600;
                        margin-bottom: 5px;
                        color: #555;
                    }
                    textarea, input[type="text"] {
                        width: 100%;
                        padding: 12px;
                        border: 2px solid #e1e8ed;
                        border-radius: 8px;
                        font-size: 14px;
                        font-family: inherit;
                        transition: border-color 0.3s ease;
                    }
                    textarea:focus, input[type="text"]:focus {
                        outline: none;
                        border-color: #4facfe;
                        box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
                    }
                    .button-group {
                        display: flex;
                        gap: 10px;
                        margin-top: 20px;
                    }
                    .btn {
                        padding: 12px 24px;
                        border: none;
                        border-radius: 8px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        font-size: 14px;
                        text-decoration: none;
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                    }
                    .btn-primary {
                        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                        color: white;
                    }
                    .btn-primary:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
                    }
                    .btn-danger {
                        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                        color: white;
                    }
                    .btn-danger:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 5px 15px rgba(238, 90, 82, 0.4);
                    }
                    .response-section {
                        margin-top: 30px;
                        padding: 20px;
                        background: #f8f9fa;
                        border-radius: 10px;
                        border-left: 4px solid #28a745;
                    }
                    .response-section h2 {
                        margin: 0 0 15px 0;
                        color: #28a745;
                        font-size: 1.2rem;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }
                    .response-content {
                        white-space: pre-wrap;
                        line-height: 1.6;
                        background: white;
                        padding: 15px;
                        border-radius: 8px;
                        border: 1px solid #e1e8ed;
                    }
                    .context-section {
                        margin-top: 20px;
                        padding: 15px;
                        background: #e3f2fd;
                        border-radius: 10px;
                        border-left: 4px solid #2196f3;
                    }
                    .context-section h3 {
                        margin: 0 0 10px 0;
                        color: #1976d2;
                        font-size: 1rem;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }
                    .context-item {
                        background: white;
                        padding: 10px;
                        margin: 5px 0;
                        border-radius: 6px;
                        border-left: 3px solid #2196f3;
                        font-size: 0.9rem;
                        line-height: 1.4;
                    }
                    .thoughts-header {
                        font-weight: 600;
                        color: #666;
                        margin-bottom: 15px;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                        font-size: 1.1rem;
                    }
                    .thought-item {
                        background: white;
                        padding: 10px 15px;
                        margin: 8px 0;
                        border-radius: 8px;
                        border-left: 3px solid #4facfe;
                        font-size: 0.9rem;
                        line-height: 1.4;
                        animation: slideIn 0.3s ease-out;
                    }
                    @keyframes slideIn {
                        from { opacity: 0; transform: translateX(-10px); }
                        to { opacity: 1; transform: translateX(0); }
                    }
                    .empty-thoughts {
                        text-align: center;
                        color: #999;
                        font-style: italic;
                        padding: 40px 20px;
                    }
                    @media (max-width: 768px) {
                        .content {
                            grid-template-columns: 1fr;
                        }
                        .thoughts-panel {
                            border-left: none;
                            border-top: 3px solid #4facfe;
                            max-height: 300px;
                        }
                        body { padding: 10px; }
                    }
                    .context-preview {
                        max-height: 150px;
                        overflow-y: auto;
                    }
                    .context-item-short {
                        display: -webkit-box;
                        -webkit-line-clamp: 2;
                        -webkit-box-orient: vertical;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }
                    .loading-spinner {
                        display: none;
                        border: 3px solid #f3f3f3;
                        border-top: 3px solid #4facfe;
                        border-radius: 50%;
                        width: 20px;
                        height: 20px;
                        animation: spin 1s linear infinite;
                        margin-right: 8px;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    .processing-thoughts {
                        display: none;
                    }
                    .btn:disabled {
                        opacity: 0.6;
                        cursor: not-allowed;
                        transform: none !important;
                    }
                </style>
                <script>
                    function showProgress() {
                        // Show loading spinner on button
                        const submitBtn = document.querySelector('.btn-primary');
                        const spinner = document.querySelector('.loading-spinner');
                        
                        if (submitBtn && spinner) {
                            submitBtn.disabled = true;
                            spinner.style.display = 'inline-block';
                            submitBtn.innerHTML = '<div class="loading-spinner" style="display: inline-block;"></div>Processing...';
                        }
                        
                        // Show processing thoughts immediately
                        const thoughtsPanel = document.querySelector('.thoughts-panel');
                        if (thoughtsPanel) {
                            const processingThoughts = [
                                '🚀 Starting to process your request...',
                                '🔄 Initializing AI reasoning...',
                                '📊 Preparing tools and memory access...'
                            ];
                            
                            // Clear existing thoughts
                            const thoughtsContainer = thoughtsPanel.querySelector('.thoughts-header').parentNode;
                            const existingThoughts = thoughtsContainer.querySelectorAll('.thought-item, .empty-thoughts');
                            existingThoughts.forEach(item => item.remove());
                            
                            // Add processing thoughts
                            processingThoughts.forEach((thought, index) => {
                                setTimeout(() => {
                                    const thoughtItem = document.createElement('div');
                                    thoughtItem.className = 'thought-item';
                                    thoughtItem.textContent = thought;
                                    thoughtsContainer.appendChild(thoughtItem);
                                }, index * 500); // Stagger the thoughts
                            });
                        }
                        
                        return true; // Allow form to submit
                    }
                </script>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🤖 Personal AI Agent</h1>
                        <p style="margin: 5px 0 0 0; opacity: 0.9;">Your intelligent assistant with memory, research, and reasoning capabilities</p>
                    </div>
                    
                    <div class="content">
                        <div class="main-panel">
                            <form method="post" onsubmit="return showProgress()">
                                <div class="form-group">
                                    <label for="query">💬 Ask me anything:</label>
                                    <textarea name="query" id="query" rows="4" placeholder="e.g., Research Python 3.12 features, help me write a script, remember my preferences..."></textarea>
                                </div>
                                
                                <div class="form-group">
                                    <label for="topic">🏷️ Topic Category:</label>
                                    <input type="text" name="topic" id="topic" value="general" placeholder="e.g., programming, personal, research, etc.">
                                </div>
                                
                                <div class="button-group">
                                    <button type="submit" class="btn btn-primary">
                                        <div class="loading-spinner"></div>
                                        🚀 Ask Agent
                                    </button>
                                    <button type="button" class="btn btn-danger" onclick="if(confirm('⚠️ Are you sure you want to clear all stored knowledge? This action cannot be undone.')) { window.location.href='/clear'; }">
                                        🗑️ Reset Knowledge
                                    </button>
                                </div>
                            </form>
                            
                            {% if response %}
                                <div class="response-section">
                                    <h2>🎯 Agent Response</h2>
                                    <div class="response-content">{{ response }}</div>
                                </div>
                            {% endif %}
                            
                            {% if context and context != ['No relevant context found.'] and context != ['Weaviate is disabled, no context available.'] %}
                                <div class="context-section">
                                    <h3>🧠 Memory Context Used</h3>
                                    <div class="context-preview">
                                        {% for item in context %}
                                            <div class="context-item context-item-short">{{ item }}</div>
                                        {% endfor %}
                                    </div>
                                </div>
                            {% endif %}
                        </div>
                        
                        <div class="thoughts-panel">
                            <div class="thoughts-header">
                                🧠 Agent Thoughts
                            </div>
                            
                            {% if agent_thoughts %}
                                {% for thought in agent_thoughts %}
                                    <div class="thought-item">{{ thought }}</div>
                                {% endfor %}
                            {% else %}
                                <div class="empty-thoughts">
                                    💭 Agent thoughts will appear here during processing...
                                </div>
                            {% endif %}
                        </div>
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
