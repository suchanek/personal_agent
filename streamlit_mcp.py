"""
app.py
Single-file Streamlit app that demonstrates a Local RAG flow:
You (UI) -> MCP client -> MindsDB (list_databases / query) -> Ollama LLM -> Answer

Notes:
- Requires MindsDB running on http://localhost:47334 (MindsDB Docker).
- Requires local Ollama / LLM accessible via ollama Python bindings.
- The mcp_use Python client is assumed; if your environment differs,
  adapt the small wrapper functions below to call the correct methods.

Run:
streamlit run app.py
"""

import json
import time
import traceback
from typing import Any, Dict, List, Optional

import streamlit as st
import requests

# Attempt imports for mcp_use and ollama. If missing, the app will still start and show instructions.
try:
    from mcp_use import MCPClient  # expected in your environment per the earlier examples
    _HAS_MCP_USE = True
except Exception:
    MCPClient = None
    _HAS_MCP_USE = False

try:
    # Ollama python client shape differs by versions; this mirrors earlier usage: ChatModel(...)
    from ollama import ChatModel
    _HAS_OLLAMA = True
except Exception:
    ChatModel = None
    _HAS_OLLAMA = False


# ---------------------------
# Utility / Wrappers
# ---------------------------
DEFAULT_MCP_CONFIG = {
    "servers": {
        "mindsdb": {
            "url": "http://localhost:47334",
            "tools": ["list_databases", "query"]
        }
    }
}


def ensure_mcp_config_file(path: str = "mcp_config.json"):
    """Write a default MCP config if file not present."""
    try:
        with open(path, "x") as f:
            json.dump(DEFAULT_MCP_CONFIG, f, indent=2)
        print(f"Created default MCP config at {path}")
    except FileExistsError:
        pass


class SimpleMCPWrapper:
    """
    Small compatibility wrapper around mcp_use.MCPClient to provide
    list_databases() and query() calls in a forgiving way.
    """

    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = config_path
        self.client = None
        if _HAS_MCP_USE and MCPClient is not None:
            try:
                self.client = MCPClient.from_config(config_path)
            except Exception as e:
                # Some versions might have a different constructor - attempt alternatives
                try:
                    self.client = MCPClient(config_path)
                except Exception as e2:
                    print("Failed to init MCPClient from library. Will fallback to HTTP where possible.")
                    print("mcp_use error:", e, e2)

        # Also store MindsDB base URL for HTTP fallback
        with open(config_path, "r") as f:
            cfg = json.load(f)
        try:
            self.mindsdb_url = cfg["servers"]["mindsdb"]["url"].rstrip("/")
        except Exception:
            self.mindsdb_url = "http://localhost:47334"

    def list_databases(self) -> List[str]:
        """Return list of databases / sources. Try client, then HTTP fallback."""
        # Try MCP client call
        if self.client:
            # try common method names
            for name in ("list_databases", "list_databases_tool", "list_tools", "tools"):
                fn = getattr(self.client, name, None)
                if callable(fn):
                    try:
                        out = fn()
                        # if returned a dict with 'databases' or similar, normalize
                        if isinstance(out, dict):
                            if "databases" in out:
                                return out["databases"]
                            # try to parse other shapes
                            return list(out.keys())
                        if isinstance(out, (list, tuple)):
                            return list(out)
                    except Exception:
                        pass
            # try a generic 'call' or 'invoke' interface if present
            for name in ("call_tool", "invoke_tool", "call"):
                fn = getattr(self.client, name, None)
                if callable(fn):
                    try:
                        # some mcp clients expect server/tool names
                        try:
                            out = fn("mindsdb", "list_databases", {})
                        except TypeError:
                            out = fn("list_databases")
                        if isinstance(out, (list, tuple)):
                            return list(out)
                        if isinstance(out, dict) and "databases" in out:
                            return out["databases"]
                    except Exception:
                        pass

        # HTTP fallback to MindsDB REST (best-effort)
        # MindsDB doesn't have a single standardized public "list databases" endpoint across versions,
        # but we can attempt to call the schema or connectors endpoints.
        try:
            # attempt common API endpoints for MindsDB
            resp = requests.get(f"{self.mindsdb_url}/api/databases", timeout=6)
            if resp.ok:
                payload = resp.json()
                # try common shapes
                if isinstance(payload, dict):
                    if "data" in payload and isinstance(payload["data"], list):
                        return [d.get("name") or d.get("database") or str(d) for d in payload["data"]]
                    return list(payload.keys())
                if isinstance(payload, list):
                    return [p.get("name") if isinstance(p, dict) else str(p) for p in payload]
        except Exception:
            pass

        # If we reach here, return a helpful message
        return ["(unable to enumerate - check MCP client or MindsDB)"]

    def query(self, query_text: str, max_rows: int = 50) -> Dict[str, Any]:
        """
        Ask MindsDB to run a federated query (best-effort).
        This wrapper tries the MCP client first; otherwise tries a MindsDB SQL endpoint.
        """
        # Try MCP client
        if self.client:
            for name in ("query", "run_query", "invoke_query", "call_tool"):
                fn = getattr(self.client, name, None)
                if callable(fn):
                    try:
                        # try several argument shapes
                        try:
                            out = fn("mindsdb", "query", {"query": query_text, "max_rows": max_rows})
                        except TypeError:
                            out = fn(query_text)
                        return {"source": "mcp_client", "result": out}
                    except Exception:
                        # continue trying other method names
                        pass

        # Fallback: try MindsDB query HTTP endpoint (best-effort use of /api/sql)
        try:
            # Some MindsDB versions expose /api/sql or /api/query; try both
            for endpoint in ("/api/sql", "/api/query", "/api/query/execute", "/api/sql/execute"):
                try:
                    resp = requests.post(self.mindsdb_url + endpoint, json={"query": query_text}, timeout=15)
                except Exception:
                    continue
                if not resp.ok:
                    continue
                try:
                    data = resp.json()
                except Exception:
                    data = resp.text
                return {"source": "mindsdb_http", "result": data}
        except Exception:
            pass

        # If all fail:
        return {"source": "error", "error": "Unable to run query. Check MCP client or MindsDB HTTP API."}


class OllamaWrapper:
    """Minimal wrapper to send a prompt to Ollama (local LLM)."""

    def __init__(self, model_name: str = "llama3"):
        self.model_name = model_name
        self.model = None
        if _HAS_OLLAMA and ChatModel is not None:
            try:
                # API varies — some libs are ChatModel(name=...), other use client.chat(...)
                try:
                    self.model = ChatModel(model_name)
                except Exception:
                    # try constructing differently
                    self.model = ChatModel(model=model_name)
            except Exception as e:
                print("Failed to init ollama.ChatModel:", e)
                self.model = None

    def chat(self, prompt: str, max_tokens: int = 512) -> str:
        # Try python binding
        if self.model:
            for fnname in ("chat", "generate", "complete", "__call__"):
                fn = getattr(self.model, fnname, None)
                if callable(fn):
                    try:
                        out = fn(prompt)
                        # many wrappers return complex object; normalize to string
                        if isinstance(out, (str,)):
                            return out
                        if isinstance(out, dict) and "text" in out:
                            return out["text"]
                        # try to stringify
                        return str(out)
                    except Exception:
                        continue

        # Fallback: attempt to use local Ollama HTTP (if Ollama daemon listening on 11434)
        try:
            ollama_url = "http://localhost:11434/api/generate"
            payload = {"model": self.model_name, "prompt": prompt}
            resp = requests.post(ollama_url, json=payload, timeout=20)
            if resp.ok:
                data = resp.json()
                # shape will vary; try to extract common fields
                if isinstance(data, dict):
                    if "text" in data:
                        return data["text"]
                    if "response" in data:
                        return str(data["response"])
                return str(data)
        except Exception:
            pass

        return "(LLM unavailable: could not talk to Ollama Python client or HTTP endpoint.)"


# ---------------------------
# Build Streamlit UI
# ---------------------------

st.set_page_config(page_title="Local RAG (MCP + MindsDB + Ollama)", layout="wide")
st.title("Local RAG — one-frame demo (MCP → MindsDB → Ollama)")

st.markdown(
    """
This demo expects:
- MindsDB running locally (Docker) at `http://localhost:47334`  
- A local Ollama LLM (or Ollama HTTP endpoint at http://localhost:11434)  
- The `mcp_use` and `ollama` python libs if you want direct bindings.

If any piece is missing, the UI will still let you run queries via HTTP fallback where possible.
"""
)

# ensure default config exists
ensure_mcp_config_file("mcp_config.json")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("MCP / MindsDB")
    st.write("Edit the MCP config (JSON):")
    mcp_config_text = st.text_area("mcp_config.json", value=json.dumps(DEFAULT_MCP_CONFIG, indent=2), height=220)
    if st.button("Save MCP config"):
        with open("mcp_config.json", "w") as f:
            f.write(mcp_config_text)
        st.success("Saved mcp_config.json")
        time.sleep(0.2)

    if st.button("List data sources"):
        wrapper = SimpleMCPWrapper("mcp_config.json")
        try:
            dbs = wrapper.list_databases()
            st.write("Data sources / databases:")
            st.json(dbs)
        except Exception as e:
            st.error("Failed to list databases: " + str(e))
            st.text(traceback.format_exc())

    st.markdown("---")
    st.write("Run a raw federated SQL query against MindsDB (best-effort):")
    raw_query = st.text_area("Raw SQL (example):", value="SELECT * FROM gmail_db.inbox WHERE is_unread = true LIMIT 20;", height=140)

    if st.button("Run raw query"):
        wrapper = SimpleMCPWrapper("mcp_config.json")
        res = wrapper.query(raw_query)
        if res.get("source") == "error":
            st.error(res.get("error"))
        else:
            st.write("Result (source = %s)" % res.get("source"))
            st.json(res.get("result"))

with col2:
    st.subheader("Chat + RAG (Query → MindsDB tool → Ollama)")
    st.write("High-level query (plain English). The app will: identify the data source via MCP wrapper, run a query, and summarize with the local LLM.")
    user_q = st.text_input("Ask (e.g., 'Show unread Slack messages from last 7 days'):")

    model_name = st.text_input("Ollama model name:", value="llama3")
    max_rows = st.slider("Max rows to fetch (federated query)", 1, 500, 50)

    if st.button("Run RAG query") and user_q.strip():
        st.info("Running RAG flow...")

        # 1) Call MCP wrapper to run a mindsdb 'query' tool (best-effort)
        wrapper = SimpleMCPWrapper("mcp_config.json")
        # Very simple heuristics — in practice you'd call the MCP "query" tool that translates
        # user text to SQL or asks MindsDB's SQL transformer. Here we just forward the user text.
        try:
            mindsdb_resp = wrapper.query(user_q, max_rows=max_rows)
        except Exception as e:
            st.error("MindsDB query step failed: " + str(e))
            mindsdb_resp = {"source": "error", "error": str(e)}

        if mindsdb_resp.get("source") == "error":
            st.error("MindsDB step couldn't run. See details below.")
            st.json(mindsdb_resp)
        else:
            st.success("MindsDB returned results (best-effort).")
            st.subheader("Raw data from MindsDB")
            st.json(mindsdb_resp.get("result"))

            # 2) Summarize / generate answer with local LLM
            st.subheader("LLM summary / answer")
            ollama = OllamaWrapper(model_name=model_name)

            # craft summarization prompt: include user question + raw output (stringified)
            # keep the prompt short to avoid token explosion — if result large, sample or summarize schema instead
            raw_text = mindsdb_resp.get("result")
            # convert complex payload into a compact string
            try:
                raw_preview = json.dumps(raw_text, indent=2)[:4000]
            except Exception:
                raw_preview = str(raw_text)[:4000]

            prompt = (
                "You are a helpful assistant. The user asked:\n\n"
                f"\"{user_q}\"\n\n"
                "Here are results retrieved from federated data sources (truncated):\n"
                f"{raw_preview}\n\n"
                "Please provide a concise, clear and actionable answer that references relevant facts from the data."
            )

            # call chat model
            llm_response = ollama.chat(prompt)
            st.write(llm_response)

st.markdown("---")
st.caption("This example is intentionally defensive: it tries Python bindings first and then HTTP fallbacks. "
           "Adapt the small wrappers to match the exact mcp_use / ollama APIs you have installed.")
