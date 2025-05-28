# pylint: disable=C0301,C0116
# ,C0115,W0613,E0611,C0413,E0401,W0601,W0621,C0302,E1101,C0103,W0718

import logging
import time
import warnings
from datetime import datetime
from typing import List

import requests
import weaviate.classes.config as wvc
from flask import Flask, render_template_string, request
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_ollama import ChatOllama, OllamaEmbeddings
from rich.logging import RichHandler
from urllib3.util import parse_url
from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams
from weaviate.util import generate_uuid5

# Suppress Pydantic deprecation warnings from Ollama
warnings.filterwarnings("ignore", category=DeprecationWarning, module="ollama")
warnings.filterwarnings(
    "ignore", message=".*model_fields.*", category=DeprecationWarning
)

# Setup logging
logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])
logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Reduce httpx logging verbosity to WARNING to reduce noise
logging.getLogger("httpx").setLevel(logging.WARNING)


# Configuration
WEAVIATE_URL = "http://localhost:8080"
OLLAMA_URL = "http://localhost:11434"
USE_WEAVIATE = True  # Set to False to bypass Weaviate for testing

# Initialize Flask app
app = Flask(__name__)

# Initialize Weaviate client and vector store
vector_store = None
weaviate_client = None
if USE_WEAVIATE:
    try:
        # Verify Weaviate is running with retries
        for attempt in range(5):
            logger.info(
                "Attempting to connect to Weaviate at %s (attempt %d/5)",
                WEAVIATE_URL,
                attempt + 1,
            )
            response = requests.get(f"{WEAVIATE_URL}/v1/.well-known/ready", timeout=10)
            if response.status_code == 200:
                logger.info("Weaviate is ready")
                break
            else:
                raise RuntimeError(f"Weaviate returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error("Attempt %d/5: Error connecting to Weaviate: %s", attempt + 1, e)
        if attempt == 4:
            logger.error(
                "Cannot connect to Weaviate at %s, proceeding without Weaviate",
                WEAVIATE_URL,
            )
            USE_WEAVIATE = False
        time.sleep(10)

    if USE_WEAVIATE:
        # Parse WEAVIATE_URL to create ConnectionParams
        parsed_url = parse_url(WEAVIATE_URL)
        connection_params = ConnectionParams.from_params(
            http_host=parsed_url.host or "localhost",
            http_port=parsed_url.port or 8080,
            http_secure=parsed_url.scheme == "https",
            grpc_host=parsed_url.host or "localhost",
            grpc_port=50051,  # Weaviate's default gRPC port
            grpc_secure=parsed_url.scheme == "https",
        )

        # Initialize Weaviate client
        try:
            weaviate_client = WeaviateClient(connection_params, skip_init_checks=True)
            weaviate_client.connect()  # Explicitly connect
            collection_name = "UserKnowledgeBase"

            # Create Weaviate collection if it doesn't exist
            if not weaviate_client.collections.exists(collection_name):
                logger.info("Creating Weaviate collection: %s", collection_name)
                weaviate_client.collections.create(
                    name=collection_name,
                    properties=[
                        wvc.Property(name="text", data_type=wvc.DataType.TEXT),
                        wvc.Property(name="timestamp", data_type=wvc.DataType.DATE),
                        wvc.Property(name="topic", data_type=wvc.DataType.TEXT),
                    ],
                    vectorizer_config=wvc.Configure.Vectorizer.none(),
                )
        except ImportError as e:
            logger.error(
                "Import error initializing Weaviate client or collection: %s", e
            )
            USE_WEAVIATE = False
        except AttributeError as e:
            logger.error(
                "Attribute error initializing Weaviate client or collection: %s", e
            )
            USE_WEAVIATE = False
        except Exception as e:
            logger.error(
                "Unexpected error initializing Weaviate client or collection: %s", e
            )
            USE_WEAVIATE = False

        if USE_WEAVIATE:
            # Initialize Weaviate vector store
            from langchain_weaviate import WeaviateVectorStore

            vector_store = WeaviateVectorStore(
                client=weaviate_client,
                index_name=collection_name,
                text_key="text",
                embedding=OllamaEmbeddings(
                    model="nomic-embed-text", base_url=OLLAMA_URL
                ),
                attributes=["timestamp", "topic"],
            )

# Initialize Ollama LLM
llm = ChatOllama(model="qwen2.5:7b-instruct", temperature=0.7, base_url=OLLAMA_URL)


# Define tools
@tool
def store_interaction(text: str, topic: str = "general") -> str:
    """Store user interaction in Weaviate."""
    if not USE_WEAVIATE or vector_store is None:
        logger.warning("Weaviate is disabled, interaction not stored.")
        return "Weaviate is disabled, interaction not stored."
    try:
        # Format timestamp as RFC3339 (with 'Z' for UTC)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        vector_store.add_texts(
            texts=[text],
            metadatas=[{"timestamp": timestamp, "topic": topic}],
            ids=[generate_uuid5(text)],
        )
        logger.info("Stored interaction: %s...", text[:50])
        return "Interaction stored successfully."
    except Exception as e:
        logger.error("Error storing interaction: %s", str(e))
        return f"Error storing interaction: {str(e)}"


@tool
def query_knowledge_base(query: str, limit: int = 5) -> List[str]:
    """Query Weaviate for relevant context."""
    if not USE_WEAVIATE or vector_store is None:
        logger.warning("Weaviate is disabled, no context available.")
        return ["Weaviate is disabled, no context available."]
    try:
        results = vector_store.similarity_search(query, k=limit)
        logger.info("Queried knowledge base with: %s...", query[:50])
        return (
            [doc.page_content for doc in results]
            if results
            else ["No relevant context found."]
        )
    except Exception as e:
        logger.error("Error querying knowledge base: %s", str(e))
        return [f"Error querying knowledge base: {str(e)}"]


# Define system prompt for the agent
system_prompt = PromptTemplate(
    template="""You are a helpful personal assistant named "Personal Agent" that learns about the user and provides context-aware responses.

You have access to these tools:
{tools}

Tool names: {tool_names}

IMPORTANT INSTRUCTIONS:
1. ALWAYS respond to the user's current question/request first
2. Use the context from knowledge base to enhance your response when relevant
3. Store important interactions for future reference
4. Be conversational and helpful

Current context from knowledge base: {context}

User's current input: {input}

To use a tool, follow this exact format:
Thought: I need to [reason for using tool]
Action: [exact tool name from: {tool_names}]
Action Input: {{"param": "value"}}
Observation: [tool result will appear here]

When you have enough information, provide your final answer:
Thought: I can now answer the user's question
Final Answer: [your complete response to the user's current input]

Remember: Answer the user's CURRENT question first, then optionally use context to enhance your response.

{agent_scratchpad}""",
    input_variables=["input", "context", "tool_names", "tools", "agent_scratchpad"],
)

# Initialize ReAct agent
tools = [store_interaction, query_knowledge_base]
agent = create_react_agent(llm=llm, tools=tools, prompt=system_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=3,
    early_stopping_method="generate",
)


# Flask routes
@app.route("/", methods=["GET", "POST"])
def index():
    response = None
    context = None
    if request.method == "POST":
        user_input = request.form.get("query", "")
        topic = request.form.get("topic", "general")
        if user_input:
            # Query knowledge base for context
            try:
                # Call the function directly with proper parameters
                context = query_knowledge_base.invoke({"query": user_input, "limit": 5})
                context_str = (
                    "\n".join(context) if context else "No relevant context found."
                )
                # Generate response
                result = agent_executor.invoke(
                    {"input": user_input, "context": context_str}
                )
                if isinstance(result, dict):
                    response = result.get("output", "No response generated.")
                else:
                    response = str(result)
                # Store interaction AFTER getting response
                interaction_text = f"User: {user_input}\nAssistant: {response}"
                store_interaction.invoke({"text": interaction_text, "topic": topic})
            except Exception as e:
                logger.error("Error processing query: %s", str(e))
                response = f"Error processing query: {str(e)}"
            logger.info(
                "Received query: %s..., Response: %s...",
                user_input[:50],
                response[:50],
            )
    return render_template_string(
        """
        <html>
            <head>
                <title>Personal AI Agent</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #333; }
                    textarea, input[type="text"] { width: 100%; max-width: 600px; }
                    input[type="submit"] { margin-top: 10px; padding: 10px 20px; }
                    .response, .context { margin-top: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
                    .context { background-color: #f9f9f9; }
                    .context ul { list-style-type: none; padding: 0; }
                </style>
            </head>
            <body>
                <h1>Personal AI Agent</h1>
                <form method="post">
                    <label for="query">Query:</label><br>
                    <textarea name="query" rows="5" cols="50" placeholder="Ask me anything..."></textarea><br>
                    <label for="topic">Topic:</label><br>
                    <input type="text" name="topic" value="general" placeholder="e.g., programming, personal, etc."><br>
                    <input type="submit" value="Submit">
                </form>
                {% if response %}
                    <div class="response">
                        <h2>Response:</h2>
                        <p style="white-space: pre-wrap;">{{ response }}</p>
                    </div>
                {% endif %}
                {% if context and context != ['No relevant context found.'] %}
                    <div class="context">
                        <h2>Context Used:</h2>
                        <ul>
                        {% for item in context %}
                            <li style="margin: 5px 0; padding: 5px; background: #f0f0f0; border-radius: 3px;">{{ item }}</li>
                        {% endfor %}
                        </ul>
                    </div>
                {% endif %}
            </body>
        </html>
        """,
        response=response,
        context=context,
    )


def cleanup():
    """Clean up resources on shutdown."""
    global weaviate_client
    if weaviate_client:
        try:
            weaviate_client.close()
            logger.info("Weaviate client closed successfully")
        except Exception as e:
            logger.error("Error closing Weaviate client: %s", e)


if __name__ == "__main__":
    import atexit

    atexit.register(cleanup)
    try:
        app.run(host="127.0.0.1", port=5000, debug=True)
    except KeyboardInterrupt:
        cleanup()
