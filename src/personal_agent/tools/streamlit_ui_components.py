"""
Streamlit UI Components
=======================

This module contains reusable UI components and utilities for the
Personal Agent Streamlit application.

It provides functions for theming, tool call display, and other UI utilities.
"""

import streamlit as st
import altair as alt

# Fix Altair deprecation warning by setting theme using new API
alt.theme.enable("default")


def apply_custom_theme():
    """Apply custom CSS for theme switching and configure Altair theme."""
    is_dark_theme = st.session_state.get("dark_theme", False)

    if is_dark_theme:
        # Apply dark theme styling with fixed dimming support
        css_file = "tools/dark_theme_fixed.css"
        try:
            with open(css_file) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            # Fallback to original CSS if fixed version not found
            css_file = "tools/dark_theme.css"
            with open(css_file) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

        # Apply Altair dark theme for charts
        alt.theme.enable("dark")
    else:
        # Light mode: use default Streamlit styling and default Altair theme
        alt.theme.enable("default")

        # Apply light mode dimming CSS for sidebar navigation
        light_mode_dimming_css = """
        <style>
        /* Light mode sidebar dimming during query execution */
        .stApp:has(.stSpinner) [data-testid="stSidebar"],
        .stApp:has([data-testid="stSpinner"]) [data-testid="stSidebar"] {
            opacity: 0.6 !important;
            pointer-events: none !important;
            transition: opacity 0.3s ease !important;
        }

        /* Specifically target navigation elements for dimming in light mode */
        .stApp:has(.stSpinner) [data-testid="stSidebar"] .stRadio,
        .stApp:has(.stSpinner) [data-testid="stSidebar"] h1,
        .stApp:has(.stSpinner) [data-testid="stSidebar"] h2,
        .stApp:has(.stSpinner) [data-testid="stSidebar"] h3,
        .stApp:has([data-testid="stSpinner"]) [data-testid="stSidebar"] .stRadio,
        .stApp:has([data-testid="stSpinner"]) [data-testid="stSidebar"] h1,
        .stApp:has([data-testid="stSpinner"]) [data-testid="stSidebar"] h2,
        .stApp:has([data-testid="stSpinner"]) [data-testid="stSidebar"] h3 {
            opacity: 0.6 !important;
            pointer-events: none !important;
        }
        </style>
        """
        st.markdown(light_mode_dimming_css, unsafe_allow_html=True)


def display_tool_calls(container, tool_call_details):
    """Display tool calls using extracted and standardized tool call details."""
    if not tool_call_details:
        return

    with container.container():
        st.markdown("**🔧 Tool Calls:**")
        for i, tool_info in enumerate(tool_call_details, 1):
            tool_name = tool_info.get("name", "Unknown Tool")
            tool_args = tool_info.get("arguments", {})
            tool_source = tool_info.get("source", "unknown")

            # Add source indicator to the tool name
            source_icon = (
                "🎯"
                if tool_source == "coordinator"
                else "🤖" if tool_source.startswith("member_") else "❓"
            )
            source_label = (
                tool_source.replace("_", " ").title()
                if tool_source != "unknown"
                else "Unknown Source"
            )

            with st.expander(
                f"Tool {i}: ✅ {tool_name} ({source_icon} {source_label})",
                expanded=False,
            ):
                if tool_args:
                    st.json(tool_args)
                else:
                    st.write("No arguments")

                # Show additional tool info if available
                if tool_info.get("result"):
                    st.write("**Result:**")
                    result = tool_info.get("result")
                    if isinstance(result, str) and len(result) > 200:
                        st.write(f"{result[:200]}...")
                    else:
                        st.write(str(result))


def extract_tool_calls_and_metrics(response_obj):
    """
    Unified tool call and metrics extraction using the proper RunResponse pattern.

    This method handles both single agent responses and team responses with member_responses.
    For teams in coordinate mode, it extracts tool calls from both the coordinator and all team members.

    This method follows the pattern:
    if agent.run_response.messages:
        for message in agent.run_response.messages:
            if message.role == "assistant":
                if message.content:
                    print(f"Message: {message.content}")
                elif message.tool_calls:
                    print(f"Tool calls: {message.tool_calls}")
                print("---" * 5, "Metrics", "---" * 5)
                pprint(message.metrics)
                print("---" * 20)

    For teams with member_responses:
    if team.run_response.member_responses:
        for member_response in team.run_response.member_responses:
            if member_response.messages:
                for message in member_response.messages:
                    if message.role == "assistant":
                        # Extract tool calls from member
    """
    tool_calls_made = 0
    tool_call_details = []
    metrics_data = {}

    def extract_tool_calls_from_message(message, source="main"):
        """Helper function to extract tool calls from a single message."""
        nonlocal tool_calls_made, tool_call_details, metrics_data

        if hasattr(message, "role") and message.role == "assistant":
            # Extract metrics directly from the message
            if hasattr(message, "metrics") and message.metrics:
                metrics_data = message.metrics
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Extracted metrics from {source} message: {metrics_data}")

            # Handle tool calls using the proper pattern
            if hasattr(message, "tool_calls") and message.tool_calls:
                tool_calls_made += len(message.tool_calls)
                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    f"Found {len(message.tool_calls)} tool calls in {source} message"
                )

                for tool_call in message.tool_calls:
                    # Try multiple approaches to extract the tool name
                    tool_name = "unknown"
                    tool_args = {}

                    # Handle dictionary-based tool calls first (most common case)
                    if isinstance(tool_call, dict):
                        # Dictionary-based tool call extraction
                        tool_name = "unknown"
                        tool_args = {}

                        # Try different name keys
                        if tool_call.get("name"):
                            tool_name = tool_call.get("name")
                        elif tool_call.get("tool_name"):
                            tool_name = tool_call.get("tool_name")
                        elif isinstance(
                            tool_call.get("function"), dict
                        ) and tool_call.get("function", {}).get("name"):
                            tool_name = tool_call.get("function", {}).get("name")

                        # Try different argument keys
                        if tool_call.get("arguments"):
                            tool_args = tool_call.get("arguments")
                        elif tool_call.get("input"):
                            tool_args = tool_call.get("input")
                        elif tool_call.get("tool_args"):
                            tool_args = tool_call.get("tool_args")
                        elif isinstance(
                            tool_call.get("function"), dict
                        ) and tool_call.get("function", {}).get("arguments"):
                            tool_args = tool_call.get("function", {}).get("arguments")

                        import logging
                        logger = logging.getLogger(__name__)
                        logger.debug(f"Dictionary tool call from {source}: {tool_call}")
                        logger.debug(f"Extracted name from dict: {tool_name}")
                        logger.debug(f"Extracted args from dict: {tool_args}")

                    else:
                        # Object-based tool call extraction (fallback)
                        # Method 1: Check for 'name' attribute (most common)
                        if hasattr(tool_call, "name") and tool_call.name:
                            tool_name = tool_call.name
                        # Method 2: Check for 'tool_name' attribute (ToolExecution objects)
                        elif hasattr(tool_call, "tool_name") and tool_call.tool_name:
                            tool_name = tool_call.tool_name
                        # Method 3: Check for function.name (OpenAI-style)
                        elif hasattr(tool_call, "function") and hasattr(
                            tool_call.function, "name"
                        ):
                            tool_name = tool_call.function.name
                        # Method 4: Check for type name as fallback
                        elif hasattr(tool_call, "__class__"):
                            tool_name = tool_call.__class__.__name__

                        # Try multiple approaches to extract arguments
                        # Method 1: Check for 'arguments' attribute
                        if hasattr(tool_call, "arguments") and tool_call.arguments:
                            tool_args = tool_call.arguments
                        # Method 2: Check for 'input' attribute (agno style)
                        elif hasattr(tool_call, "input") and tool_call.input:
                            tool_args = tool_call.input
                        # Method 3: Check for 'tool_args' attribute (ToolExecution objects)
                        elif hasattr(tool_call, "tool_args") and tool_call.tool_args:
                            tool_args = tool_call.tool_args
                        # Method 4: Check for function.arguments (OpenAI-style)
                        elif hasattr(tool_call, "function") and hasattr(
                            tool_call.function, "arguments"
                        ):
                            tool_args = tool_call.function.arguments

                    # Log debugging information
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(
                        f"Tool call object type from {source}: {type(tool_call).__name__}"
                    )
                    if hasattr(tool_call, "__dict__"):
                        logger.debug(
                            f"Tool call attributes: {[attr for attr in dir(tool_call) if not attr.startswith('_')]}"
                        )
                    logger.debug(
                        f"Final extracted tool name from {source}: {tool_name}"
                    )
                    logger.debug(
                        f"Final extracted tool args from {source}: {tool_args}"
                    )

                    tool_info = {
                        "name": tool_name,
                        "arguments": tool_args,
                        "result": (
                            tool_call.get("result")
                            if isinstance(tool_call, dict)
                            else getattr(tool_call, "result", None)
                        ),
                        "status": "success",
                        "source": source,  # Track whether this came from coordinator or member
                    }
                    tool_call_details.append(tool_info)

    # Extract tool calls from main/coordinator messages
    if hasattr(response_obj, "messages") and response_obj.messages:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Extracting tool calls from coordinator messages")
        for message in response_obj.messages:
            extract_tool_calls_from_message(message, "coordinator")

    # Extract tool calls from team member responses (coordinate mode)
    if hasattr(response_obj, "member_responses") and response_obj.member_responses:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Found {len(response_obj.member_responses)} member responses")
        for i, member_response in enumerate(response_obj.member_responses):
            if hasattr(member_response, "messages") and member_response.messages:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Extracting tool calls from member {i+1} messages")
                for message in member_response.messages:
                    extract_tool_calls_from_message(message, f"member_{i+1}")
            else:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Member response {i+1} has no messages")
    else:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug("No member_responses found in response object")

    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"Total tool calls extracted: {tool_calls_made} from {len(tool_call_details)} tool call details"
    )
    return tool_calls_made, tool_call_details, metrics_data


def format_tool_call_for_debug(tool_call):
    """
    Legacy function kept for backward compatibility.
    New code should use extract_tool_calls_and_metrics() instead.
    """
    tool_name = "Unknown"
    tool_args = {}

    # Handle dictionary-based tool calls first (most common case)
    if isinstance(tool_call, dict):
        # Dictionary-based tool call extraction
        tool_name = "Unknown"
        tool_args = {}

        # Try different name keys
        if tool_call.get("name"):
            tool_name = tool_call.get("name")
        elif tool_call.get("tool_name"):
            tool_name = tool_call.get("tool_name")
        elif isinstance(tool_call.get("function"), dict) and tool_call.get(
            "function", {}
        ).get("name"):
            tool_name = tool_call.get("function", {}).get("name")

        # Try different argument keys
        if tool_call.get("arguments"):
            tool_args = tool_call.get("arguments")
        elif tool_call.get("input"):
            tool_args = tool_call.get("input")
        elif tool_call.get("tool_args"):
            tool_args = tool_call.get("tool_args")
        elif isinstance(tool_call.get("function"), dict) and tool_call.get(
            "function", {}
        ).get("arguments"):
            tool_args = tool_call.get("function", {}).get("arguments")

        return {
            "name": tool_name,
            "arguments": tool_args,
            "result": tool_call.get("result"),
            "status": "success",
        }

    else:
        # Object-based tool call extraction (fallback)
        # Method 1: Check for 'name' attribute (most common)
        if hasattr(tool_call, "name") and tool_call.name:
            tool_name = tool_call.name
        # Method 2: Check for 'tool_name' attribute (ToolExecution objects)
        elif hasattr(tool_call, "tool_name") and tool_call.tool_name:
            tool_name = tool_call.tool_name
        # Method 3: Check for function.name (OpenAI-style)
        elif hasattr(tool_call, "function") and hasattr(tool_call.function, "name"):
            tool_name = tool_call.function.name
        # Method 4: Check for type name as fallback
        elif hasattr(tool_call, "__class__"):
            tool_name = tool_call.__class__.__name__

        # Try multiple approaches to extract arguments
        # Method 1: Check for 'arguments' attribute
        if hasattr(tool_call, "arguments") and tool_call.arguments:
            tool_args = tool_call.arguments
        # Method 2: Check for 'input' attribute (agno style)
        elif hasattr(tool_call, "input") and tool_call.input:
            tool_args = tool_call.input
        # Method 3: Check for 'tool_args' attribute (ToolExecution objects)
        elif hasattr(tool_call, "tool_args") and tool_call.tool_args:
            tool_args = tool_call.tool_args
        # Method 4: Check for function.arguments (OpenAI-style)
        elif hasattr(tool_call, "function") and hasattr(
            tool_call.function, "arguments"
        ):
            tool_args = tool_call.function.arguments

        return {
            "name": tool_name,
            "arguments": tool_args,
            "result": getattr(tool_call, "result", None),
            "status": "success",
        }
