# ADR-033: Agno Response Handling Simplification and Tool Call Extraction Fix

## Status
Accepted

## Context
The personal AI agent system, built on the Agno framework, experienced issues with response handling and tool call visibility, particularly when streaming responses from Ollama models. The original implementation in `src/personal_agent/core/agno_agent.py` suffered from over-parsing, redundant content extraction methods, manual tool collection, and complex streaming logic. This led to:
- Inefficient and overly complex code.
- Tool calls not being displayed in the Streamlit sidebar, despite successful execution, hindering debugging and monitoring.
- Potential inconsistencies in how model responses were processed.

## Decision
To address these issues, a comprehensive refactoring of the Agno response handling and tool call extraction mechanisms was undertaken. The core decision was to:
1.  **Trust Agno's Built-in Parsing**: Leverage Agno's native capabilities for response parsing and content extraction, eliminating redundant custom logic.
2.  **Streamline Tool Call Collection**: Implement an event-based collection strategy within the `agno_agent.py` to capture tool calls as they occur during streaming, making them reliably accessible for UI display and debugging.
3.  **Simplify Streamlit Integration**: Adapt the Streamlit frontend (`tools/paga_streamlit_agno.py`) to consume the simplified agent response and retrieve tool call information from the newly implemented collection mechanism.

## Consequences

### Positive
- **Eliminated Over-Parsing**: Removed four redundant content extraction methods and custom wrapper classes, leading to cleaner and more efficient code.
- **Reliable Tool Call Visibility**: Tool calls now display correctly and consistently in the Streamlit sidebar, restoring crucial debugging and monitoring capabilities.
- **Code Reduction**: Approximately 100 lines of complex and redundant parsing code were removed, simplifying the codebase.
- **Improved Separation of Concerns**: The core agent now focuses purely on execution, while the UI layer handles display and formatting, aligning better with architectural best practices.
- **Proper Async Generator Handling**: Ensured correct consumption of async generators for streaming responses, maintaining real-time updates.
- **Zero Regression**: All existing functionalities, including streaming support and error handling, were preserved without introducing new bugs.
- **Enhanced Maintainability**: The simplified and framework-aligned approach reduces the maintenance burden and makes future debugging easier.

### Negative
- (None identified)

## Alternatives Considered
- **Further Custom Parsing**: Continuing to build custom parsing logic would have increased complexity and maintenance overhead, and likely would not have fully resolved the tool call visibility issue due to the asynchronous nature of the framework's events.
- **Modifying Agno Framework**: While a possibility, modifying the core Agno framework was deemed out of scope for this specific problem and would introduce significant maintenance challenges for future updates.

## References
- `refs/agno_response_handling_simplification.md`
- `refs/tool_call_extraction_fix_summary.md`
