# ADR-040: Explicit LightRAG URL Parameterization

## Status

Accepted

## Context

The agent interacts with multiple LightRAG server instances, primarily a general knowledge server and a user-specific memory server. Previously, the URL for the target LightRAG server was often implicitly derived from a single, global configuration setting (`settings.LIGHTRAG_URL`). This approach created ambiguity and a risk of misrouting requests. For example, a tool intending to query the memory server might inadvertently default to the knowledge server's URL, leading to incorrect data access, failed operations, and difficult-to-diagnose bugs.

## Decision

We will refactor all methods and tools that interact with LightRAG to accept an explicit `url` parameter. This makes the target server for every API call unambiguous.

- All internal methods that wrap LightRAG API calls (e.g., `_upload_to_lightrag`) will now require a `url` argument.
- Higher-level tools (e.g., `query_knowledge_base`, `ingest_knowledge_file`) will also accept an optional `url` parameter, which defaults to the primary knowledge server (`settings.LIGHTRAG_URL`) but can be overridden to target other instances like the memory server.

This change ensures that the caller is always responsible for specifying the correct LightRAG instance, making the data flow explicit and preventing cross-instance contamination.

## Consequences

### Positive

- **Improved Clarity**: The target of every LightRAG operation is now explicit in the code, making it easier to read, understand, and debug.
- **Enhanced Robustness**: Eliminates the risk of accidentally sending data to or querying the wrong LightRAG instance.
- **Greater Flexibility**: Simplifies the integration of future LightRAG instances without the need for complex routing logic.

### Negative

- **Increased Verbosity**: Requires passing the `url` parameter through several layers of method calls, which can make the code slightly more verbose. However, this is a worthwhile trade-off for the gain in clarity and safety.
