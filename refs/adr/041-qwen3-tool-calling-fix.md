# ADR-041: Revert to Standard Ollama Class for Reliable Tool Calling

## Status

**Accepted**

## Context

The `agno` library offers two primary classes for interacting with Ollama models: `agno.models.ollama.Ollama` and the specialized `agno.models.ollama.tools.OllamaTools`. The `OllamaTools` class is designed to provide a more structured and simplified interface for handling tool calls.

However, extensive testing with our primary `qwen3:8b` model revealed a critical flaw: `OllamaTools` consistently fails to correctly parse model output or trigger tool calls. When prompted to use a tool, the agent would instead generate a conversational response, effectively ignoring the tool-use request. This failure was verified through a series of diagnostic scripts (`diagnose_qwen3_tool_calling.py`, `test_qwen3_tool_calling_final.py`), which confirmed that the `OllamaTools` wrapper was the point of failure.

In contrast, tests using the standard `agno.models.ollama.Ollama` class showed that the `qwen3` model itself generates tool calls correctly in its native XML-based format. The issue lies entirely within the `OllamaTools` abstraction layer.

## Decision

We will officially revert the `AgentModelManager` to use the standard `agno.models.ollama.Ollama` class for all Ollama models, and discontinue the use of `OllamaTools`.

This change ensures that the agent can reliably leverage the native tool-calling capabilities of the underlying models, particularly `qwen3`. While `OllamaTools` aimed for a cleaner abstraction, its current unreliability with our core models makes it a liability. The standard `Ollama` class provides a proven, functional path for tool integration.

## Consequences

### Positive
- **Immediate Fix:** Tool calling with `qwen3` models is immediately restored and becomes reliable.
- **Increased Robustness:** The agent's core functionality is no longer dependent on a fragile abstraction layer.
- **Simplification:** The `AgentModelManager` is slightly simplified by removing the dependency on `OllamaTools` and its specific configurations (e.g., reasoning parameters that were not being effectively used).

### Negative
- **Loss of Abstraction:** We lose the potential convenience and cleaner interface that a fully functional `OllamaTools` class might have provided. This is an acceptable trade-off for core functionality.
- **Future Maintenance:** If `agno` updates or fixes `OllamaTools` in the future, we may need to revisit this decision, but for now, stability is paramount.
