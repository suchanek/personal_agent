import json
import logging
import time
from datetime import datetime
from typing import List

import requests
import weaviate.classes.config as wvc
from flask import Flask, render_template_string, request
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_ollama import ChatOllama, OllamaEmbeddings
from urllib3.util import parse_url
from weaviate import WeaviateClient
from weaviate.connect import ConnectionParams
from weaviate.util import generate_uuid5

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
                f"Attempting to connect to Weaviate at {WEAVIATE_URL} (attempt {attempt + 1}/5)"
            )
            response = requests.get(f"{WEAVIATE_URL}/v1/.well-known/ready", timeout=10)
            if response.status_code == 200:
                logger.info("Weaviate is ready")
                break
            else:
                raise Exception(f"Weaviate returned status {response.status_code}")
    except Exception as e:
        logger.error(f"Attempt {attempt + 1}/5: Error connecting to Weaviate: {e}")
        if attempt == 4:
            logger.error(
                f"Cannot connect to Weaviate at {WEAVIATE_URL}, proceeding without Weaviate"
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
                logger.info(f"Creating Weaviate collection: {collection_name}")
                weaviate_client.collections.create(
                    name=collection_name,
                    properties=[
                        wvc.Property(name="text", data_type=wvc.DataType.TEXT),
                        wvc.Property(name="timestamp", data_type=wvc.DataType.DATE),
                        wvc.Property(name="topic", data_type=wvc.DataType.TEXT),
                    ],
                    vectorizer_config=wvc.Configure.Vectorizer.none(),
                )
        except Exception as e:
            logger.error(f"Error initializing Weaviate client or collection: {e}")
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
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        vector_store.add_texts(
            texts=[text],
            metadatas=[{"timestamp": timestamp, "topic": topic}],
            ids=[generate_uuid5(text)],
        )
        logger.info(f"Stored interaction: {text[:50]}...")
        return "Interaction stored successfully."
    except Exception as e:
        logger.error(f"Error storing interaction: {str(e)}")
        return f"Error storing interaction: {str(e)}"


@tool
def query_knowledge_base(query: str, limit: int = 5) -> List[str]:
    """Query Weaviate for relevant context."""
    if not USE_WEAVIATE or vector_store is None:
        logger.warning("Weaviate is disabled, no context available.")
        return ["Weaviate is disabled, no context available."]
    try:
        results = vector_store.similarity_search(query, k=limit)
        logger.info(f"Queried knowledge base with: {query[:50]}...")
        return (
            [doc.page_content for doc in results]
            if results
            else ["No relevant context found."]
        )
    except Exception as e:
        logger.error(f"Error querying knowledge base: {str(e)}")
        return [f"Error querying knowledge base: {str(e)}"]


# Define system prompt for the agent
system_prompt = PromptTemplate(
    template="""You are a personal assistant that learns about the user and provides context-aware responses.

Available tools:
{tools}

Tool names: {tool_names}

Context from knowledge base: {context}

Answer the user's query concisely and professionally, incorporating relevant context. Use tools only when explicitly needed.

When you need to use a tool, follow this exact format:
Thought: [your reasoning]
Action: [tool name]
Action Input: [tool input]
Observation: [tool result]

When you have enough information to answer, respond with:
Thought: [your reasoning]
Final Answer: [your complete answer]

{agent_scratchpad}""",
    input_variables=["context", "tool_names", "tools", "agent_scratchpad"],
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
                context = query_knowledge_base.invoke({"query": user_input})
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
                # Store interaction
                interaction_text = f"Query: {user_input} | Response: {response}"
                store_interaction.invoke({"text": interaction_text, "topic": topic})
            except Exception as e:
                logger.error(f"Error processing query: {str(e)}")
                response = f"Error processing query: {str(e)}"
            logger.info(
                f"Received query: {user_input[:50]}..., Response: {response[:50]}..."
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
                    .response, .context { margin-top: 20px; }
                    .context ul { list-style-type: none; padding: 0; }
                </style>
            </head>
            <body>
                <h1>Personal AI Agent</h1>
                <form method="post">
                    <label for="query">Query:</label><br>
                    <textarea name="query" rows="5" cols="50"></textarea><br>
                    <label for="topic">Topic:</label><br>
                    <input type="text" name="topic" value="general"><br>
                    <input type="submit" value="Submit">
                </form>
                {% if response %}
                    <div class="response">
                        <h2>Response:</h2>
                        <p>{{ response }}</p>
                    </div>
                {% endif %}
                {% if context %}
                    <div class="context">
                        <h2>Context Used:</h2>
                        <ul>
                        {% for item in context %}
                            <li>{{ item }}</li>
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
            logger.error(f"Error closing Weaviate client: {e}")


if __name__ == "__main__":
    import atexit
    atexit.register(cleanup)
    try:
        app.run(host="127.0.0.1", port=5000, debug=True)
    except KeyboardInterrupt:
        cleanup()
