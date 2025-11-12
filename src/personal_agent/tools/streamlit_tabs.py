"""
Streamlit Tabs
==============

This module contains all tab rendering functions for the Personal Agent
Streamlit application.

It provides the main UI tabs: Chat, Memory Manager, and Knowledge Base.
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from personal_agent.config import AGNO_KNOWLEDGE_DIR, USER_DATA_DIR
from personal_agent.tools.streamlit_session import (
    SESSION_KEY_AGENT,
    SESSION_KEY_AGENT_MODE,
    SESSION_KEY_AVAILABLE_MODELS,
    SESSION_KEY_CURRENT_MODEL,
    SESSION_KEY_CURRENT_OLLAMA_URL,
    SESSION_KEY_DARK_THEME,
    SESSION_KEY_DEBUG_METRICS,
    SESSION_KEY_KNOWLEDGE_HELPER,
    SESSION_KEY_MEMORY_HELPER,
    SESSION_KEY_MESSAGES,
    SESSION_KEY_PERFORMANCE_STATS,
    SESSION_KEY_RAG_SERVER_LOCATION,
    SESSION_KEY_SHOW_DEBUG,
    SESSION_KEY_TEAM,
)
from personal_agent.tools.streamlit_ui_components import (
    display_tool_calls,
    extract_tool_calls_and_metrics,
)

logger = logging.getLogger(__name__)


def render_chat_tab():
    """Render the chat tab interface."""
    # Dynamic title based on mode
    if st.session_state[SESSION_KEY_AGENT_MODE] == "team":
        st.markdown("### Chat with your AI Team")
    else:
        st.markdown("### Have a conversation with your AI friend")

    for message in st.session_state[SESSION_KEY_MESSAGES]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to talk about?"):
        st.session_state[SESSION_KEY_MESSAGES].append(
            {"role": "user", "content": prompt}
        )
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Create containers for tool calls and response
            tool_calls_container = st.empty()
            resp_container = st.empty()

            # Dynamic spinner message based on mode
            spinner_message = (
                "🤖 Team is thinking..."
                if st.session_state[SESSION_KEY_AGENT_MODE] == "team"
                else "🤔 Thinking..."
            )

            with st.spinner(spinner_message):
                start_time = time.time()
                start_timestamp = datetime.now()
                response = ""
                tool_calls_made = 0
                tool_call_details = []
                all_tools_used = []

                try:
                    if st.session_state[SESSION_KEY_AGENT_MODE] == "team":
                        # Team mode handling
                        team = st.session_state[SESSION_KEY_TEAM]

                        if team:
                            # DIAGNOSTIC: Log team information
                            logger.info(
                                "🔍 DIAGNOSTIC: Team has %d members",
                                len(getattr(team, "members", [])),
                            )
                            if hasattr(team, "members"):
                                for i, member in enumerate(team.members):
                                    member_name = getattr(member, "name", "Unknown")
                                    member_model = getattr(
                                        getattr(member, "model", None), "id", "Unknown"
                                    )
                                    logger.info(
                                        "🔍 DIAGNOSTIC: Member %d: %s (model: %s)",
                                        i,
                                        member_name,
                                        member_model,
                                    )

                            # Use the standard agno Team arun method (async)
                            logger.info(
                                "🔍 DIAGNOSTIC: Running team query: %s", prompt[:50]
                            )
                            response_obj = asyncio.run(
                                team.arun(prompt, user_id=USER_DATA_DIR)
                            )

                            # DIAGNOSTIC: Log response structure
                            logger.info(
                                "🔍 DIAGNOSTIC: Response type: %s",
                                type(response_obj).__name__,
                            )
                            logger.info(
                                "🔍 DIAGNOSTIC: Response has content: %s",
                                hasattr(response_obj, "content"),
                            )
                            logger.info(
                                "🔍 DIAGNOSTIC: Response has messages: %s",
                                hasattr(response_obj, "messages"),
                            )
                            if (
                                hasattr(response_obj, "messages")
                                and response_obj.messages
                            ):
                                logger.info(
                                    "🔍 DIAGNOSTIC: Number of messages: %d",
                                    len(response_obj.messages),
                                )
                                for i, msg in enumerate(response_obj.messages):
                                    logger.info(
                                        "🔍 DIAGNOSTIC: Message %d: role=%s, content_length=%d",
                                        i,
                                        getattr(msg, "role", "unknown"),
                                        len(getattr(msg, "content", "")),
                                    )

                            response = (
                                response_obj.content
                                if hasattr(response_obj, "content")
                                else str(response_obj)
                            )

                            # Use the unified extraction method for team mode
                            (
                                tool_calls_made,
                                tool_call_details,
                                metrics_data,
                            ) = extract_tool_calls_and_metrics(response_obj)

                            # 🚨 SIMPLIFIED RESPONSE PARSING - NO FILTERING
                            print(
                                f"🔍 SIMPLE_DEBUG: Starting response parsing for query: '{prompt[:50]}...'"
                            )

                            # Step 1: Try main response content first
                            if (
                                hasattr(response_obj, "content")
                                and response_obj.content
                            ):
                                response = str(response_obj.content)
                                print(
                                    f"🔍 SIMPLE_DEBUG: Using main response content: '{response[:100]}...' ({len(response)} chars)"
                                )
                            else:
                                response = ""
                                print(
                                    f"🔍 SIMPLE_DEBUG: No main response content found"
                                )

                            # Step 2: If no main content or it's empty, check member responses
                            if (
                                not response.strip()
                                and hasattr(response_obj, "member_responses")
                                and response_obj.member_responses
                            ):
                                print(
                                    f"🔍 SIMPLE_DEBUG: Main response empty, checking {len(response_obj.member_responses)} member responses"
                                )

                                # Get ALL assistant messages from ALL members - no filtering
                                all_assistant_messages = []
                                for i, member_resp in enumerate(
                                    response_obj.member_responses
                                ):
                                    if (
                                        hasattr(member_resp, "messages")
                                        and member_resp.messages
                                    ):
                                        for j, msg in enumerate(member_resp.messages):
                                            if (
                                                hasattr(msg, "role")
                                                and msg.role == "assistant"
                                                and hasattr(msg, "content")
                                                and msg.content
                                            ):
                                                all_assistant_messages.append(
                                                    {
                                                        "member": i,
                                                        "message": j,
                                                        "content": str(msg.content),
                                                        "length": len(str(msg.content)),
                                                    }
                                                )
                                                print(
                                                    f"🔍 SIMPLE_DEBUG: Found assistant message from member {i}: '{str(msg.content)[:100]}...' ({len(str(msg.content))} chars)"
                                                )

                                # Use the LAST assistant message (most recent)
                                if all_assistant_messages:
                                    last_message = all_assistant_messages[-1]
                                    response = last_message["content"]
                                    print(
                                        f"🔍 SIMPLE_DEBUG: Using LAST assistant message from member {last_message['member']}: '{response[:100]}...' ({len(response)} chars)"
                                    )
                                else:
                                    print(
                                        f"🔍 SIMPLE_DEBUG: No assistant messages found in member responses"
                                    )

                            # Step 3: Handle </think> tags if present - PRESERVE them for now (don't strip)
                            if "</think>" in response:
                                print(
                                    f"🔍 SIMPLE_DEBUG: Found <think> tags in response, preserving them as requested"
                                )
                                # Keep the full response including <think> tags
                                # Original stripping logic commented out:
                                # parts = response.split('</think>')
                                # if len(parts) > 1:
                                #     after_think = parts[-1].strip()
                                #     if after_think:
                                #         response = after_think

                            print(
                                f"🔍 SIMPLE_DEBUG: ✅ FINAL RESPONSE: '{response[:200]}...' ({len(response)} chars)"
                            )

                            # Display tool calls if any
                            if tool_call_details:
                                display_tool_calls(
                                    tool_calls_container, tool_call_details
                                )
                        else:
                            response = "Team not initialized properly"
                    else:
                        # Single agent mode handling
                        agent = st.session_state[SESSION_KEY_AGENT]

                        # Handle AgnoPersonalAgent with new RunResponse pattern
                        from personal_agent.core.agno_agent import AgnoPersonalAgent

                        if isinstance(agent, AgnoPersonalAgent):

                            async def run_agent_with_streaming():
                                nonlocal response, tool_calls_made, tool_call_details, all_tools_used

                                try:
                                    # Use agent.arun() instead of agent.run() for async tool compatibility
                                    # The arun() method returns a RunResponse object directly, not a string
                                    run_response = await agent.arun(
                                        prompt, stream=False, add_thought_callback=None
                                    )

                                    # Extract content from the RunResponse object
                                    if (
                                        hasattr(run_response, "content")
                                        and run_response.content
                                    ):
                                        response_content = run_response.content
                                    elif (
                                        hasattr(run_response, "messages")
                                        and run_response.messages
                                    ):
                                        # Extract content from the last assistant message
                                        response_content = ""
                                        for message in run_response.messages:
                                            if (
                                                hasattr(message, "role")
                                                and message.role == "assistant"
                                            ):
                                                if (
                                                    hasattr(message, "content")
                                                    and message.content
                                                ):
                                                    response_content += message.content
                                    else:
                                        response_content = str(run_response)

                                    # Use the unified extraction method for single agent mode
                                    (
                                        tool_calls_made,
                                        tool_call_details,
                                        metrics_data,
                                    ) = extract_tool_calls_and_metrics(run_response)

                                    # Display tool calls if any
                                    if tool_call_details:
                                        display_tool_calls(
                                            tool_calls_container, tool_call_details
                                        )
                                        logger.info(
                                            f"Displayed {len(tool_call_details)} tool calls using unified method"
                                        )
                                    else:
                                        logger.info(
                                            "No tool calls found in RunResponse using unified method"
                                        )

                                    return response_content

                                except Exception as e:
                                    raise Exception(
                                        f"Error in agent execution: {e}"
                                    ) from e

                            response_content = asyncio.run(run_agent_with_streaming())
                            response = response_content if response_content else ""
                        else:
                            # Non-AgnoPersonalAgent fallback
                            agent_response = agent.run(prompt)
                            response = (
                                agent_response.content
                                if hasattr(agent_response, "content")
                                else str(agent_response)
                            )

                    # Display the final response
                    resp_container.markdown(response)

                    end_time = time.time()
                    response_time = end_time - start_time

                    # Calculate token estimates
                    input_tokens = len(prompt.split()) * 1.3
                    output_tokens = len(response.split()) * 1.3 if response else 0
                    total_tokens = input_tokens + output_tokens

                    response_metadata = {}
                    response_type = "AgnoResponse"

                    # Update performance stats with real-time tool call count
                    stats = st.session_state[SESSION_KEY_PERFORMANCE_STATS]
                    stats["total_requests"] += 1
                    stats["total_response_time"] += response_time
                    stats["average_response_time"] = (
                        stats["total_response_time"] / stats["total_requests"]
                    )
                    stats["total_tokens"] += total_tokens
                    stats["average_tokens"] = (
                        stats["total_tokens"] / stats["total_requests"]
                    )
                    stats["fastest_response"] = min(
                        stats["fastest_response"], response_time
                    )
                    stats["slowest_response"] = max(
                        stats["slowest_response"], response_time
                    )
                    stats["tool_calls_count"] += tool_calls_made

                    # Store debug metrics with standardized format
                    debug_entry = {
                        "timestamp": start_timestamp.strftime("%H:%M:%S"),
                        "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                        "response_time": round(response_time, 3),
                        "input_tokens": round(input_tokens),
                        "output_tokens": round(output_tokens),
                        "total_tokens": round(total_tokens),
                        "tool_calls": tool_calls_made,
                        "tool_call_details": tool_call_details,
                        "response_type": (
                            "PersonalAgentTeam"
                            if st.session_state[SESSION_KEY_AGENT_MODE] == "team"
                            else (
                                "AgnoPersonalAgent"
                                if st.session_state[SESSION_KEY_AGENT_MODE] == "single"
                                else "Unknown"
                            )
                        ),
                        "success": True,
                    }
                    st.session_state[SESSION_KEY_DEBUG_METRICS].append(debug_entry)
                    if len(st.session_state[SESSION_KEY_DEBUG_METRICS]) > 10:
                        st.session_state[SESSION_KEY_DEBUG_METRICS].pop(0)

                    # Display structured response metadata if available
                    if response_metadata and response_type == "StructuredResponse":
                        confidence = response_metadata.get("confidence")
                        sources = response_metadata.get("sources", [])
                        metadata_response_type = response_metadata.get(
                            "response_type", "structured"
                        )

                        # Create a compact metadata display
                        metadata_parts = []
                        if confidence is not None:
                            confidence_color = (
                                "🟢"
                                if confidence > 0.8
                                else "🟡" if confidence > 0.6 else "🔴"
                            )
                            metadata_parts.append(
                                f"{confidence_color} **Confidence:** {confidence:.2f}"
                            )

                        if sources:
                            metadata_parts.append(
                                f"📚 **Sources:** {', '.join(sources[:3])}"
                            )  # Show first 3 sources

                        metadata_parts.append(f"🔧 **Type:** {metadata_response_type}")

                        if metadata_parts:
                            with st.expander("📊 Response Metadata", expanded=False):
                                st.markdown(" | ".join(metadata_parts))
                                if len(sources) > 3:
                                    st.markdown(
                                        f"**All Sources:** {', '.join(sources)}"
                                    )

                    # Display debug info if enabled (moved to sidebar)
                    if st.session_state.get(SESSION_KEY_SHOW_DEBUG, False):
                        with st.expander("🔍 **Basic Debug Info**", expanded=False):
                            st.write(f"**Response Type:** {response_type}")
                            st.write(f"**Tool Calls Made:** {tool_calls_made}")
                            st.write(f"**Response Time:** {response_time:.3f}s")
                            st.write(f"**Total Tokens:** {total_tokens:.0f}")

                            if response_metadata:
                                st.write("**Structured Response Metadata:**")
                                st.json(response_metadata)

                    # Store message with metadata for future reference
                    message_data = {
                        "role": "assistant",
                        "content": response,
                        "metadata": (
                            response_metadata
                            if response_type == "StructuredResponse"
                            else None
                        ),
                        "response_type": response_type,
                        "tool_calls": tool_call_details,  # Store the standardized list
                        "response_time": response_time,
                    }
                    st.session_state[SESSION_KEY_MESSAGES].append(message_data)
                    st.rerun()

                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state[SESSION_KEY_MESSAGES].append(
                        {"role": "assistant", "content": error_msg}
                    )

                    # Log failed request
                    debug_entry = {
                        "timestamp": start_timestamp.strftime("%H:%M:%S"),
                        "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                        "response_time": round(response_time, 3),
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                        "tool_calls": 0,
                        "tool_call_details": [],
                        "response_type": "Error",
                        "success": False,
                        "error": str(e),
                    }
                    st.session_state[SESSION_KEY_DEBUG_METRICS].append(debug_entry)
                    if len(st.session_state[SESSION_KEY_DEBUG_METRICS]) > 10:
                        st.session_state[SESSION_KEY_DEBUG_METRICS].pop(0)

                    if st.session_state.get(SESSION_KEY_SHOW_DEBUG, False):
                        with st.expander("❌ **Error Debug Info**", expanded=True):
                            import traceback

                            st.write(f"**Error Time:** {response_time:.3f}s")
                            st.write(f"**Error Type:** {type(e).__name__}")
                            st.write(f"**Error Message:** {str(e)}")
                            st.code(traceback.format_exc())
                    st.rerun()


def render_memory_tab():
    """Render the memory management tab interface."""
    st.markdown("### Comprehensive Memory Management")
    memory_helper = st.session_state[SESSION_KEY_MEMORY_HELPER]

    # Store New Facts Section
    st.markdown("---")
    st.subheader("📝 Store New Facts")
    st.markdown("*Add facts directly to memory without agent inference*")
    categories = [
        "automatic",
        "personal",
        "work",
        "education",
        "hobbies",
        "preferences",
        "goals",
        "health",
        "family",
        "travel",
        "technology",
        "journal",
        "other",
    ]
    selected_category = st.selectbox("Category:", categories, key="fact_category")
    # Inline input for storing facts (uniform with knowledge tools)
    # Clear-on-success using a flag to avoid Streamlit key mutation errors
    if st.session_state.get("clear_fact_input_text", False):
        st.session_state["fact_input_text"] = ""
        st.session_state["clear_fact_input_text"] = False

    with st.form("store_fact_form"):
        fact_input = st.text_input(
            "Enter a fact to store (e.g., I work at Google as a software engineer)",
            key="fact_input_text",
        )
        submitted = st.form_submit_button("💾 Save Fact")
    if submitted and fact_input and fact_input.strip():
        topic_list = None if selected_category == "automatic" else [selected_category]
        result = memory_helper.add_memory(
            memory_text=fact_input.strip(),
            topics=topic_list,
            input_text="Direct fact storage",
        )

        # Handle both MemoryStorageResult objects and legacy tuple returns
        if hasattr(result, "is_success"):
            # MemoryStorageResult object
            success = result.is_success
            message = result.message
            memory_id = getattr(result, "memory_id", None)
        elif isinstance(result, tuple) and len(result) >= 2:
            # Legacy tuple format (success, message, memory_id, topics)
            success, message = result[0], result[1]
            memory_id = result[2] if len(result) > 2 else None
        else:
            # Fallback
            success = False
            message = f"Unexpected result format: {result}"
            memory_id = None

        if success:
            # Show success notification
            st.toast("🎉 Fact saved to memory", icon="✅")
            time.sleep(2.0)  # 2 second delay
            # Defer clearing the input to the next run to comply with Streamlit rules
            st.session_state["clear_fact_input_text"] = True
            st.rerun()
        else:
            st.error(f"❌ Failed to store fact: {message}")

    # Search Memories Section
    st.markdown("---")
    st.subheader("🔍 Search Memories")
    st.markdown("*Search through stored memories using semantic similarity*")
    col1, col2 = st.columns(2)
    with col1:
        similarity_threshold = st.slider(
            "Similarity Threshold",
            0.1,
            1.0,
            0.3,
            0.1,
            key="memory_similarity_threshold",
        )
    with col2:
        search_limit = st.number_input(
            "Max Results", 1, 50, 10, key="memory_search_limit"
        )
    with st.form("memory_search_form"):
        search_query = st.text_input(
            "Enter keywords to search your memories",
            key="memory_search_query_text",
        )
        submitted_memory_search = st.form_submit_button("🔎 Search")
    if submitted_memory_search and search_query and search_query.strip():
        search_results = memory_helper.search_memories(
            query=search_query.strip(),
            limit=search_limit,
            similarity_threshold=similarity_threshold,
        )
        if search_results:
            st.subheader(f"🔍 Search Results for: '{search_query.strip()}'")
            for i, (memory, score) in enumerate(search_results, 1):
                # Get enhanced fields
                confidence = getattr(memory, "confidence", 1.0)
                is_proxy = getattr(memory, "is_proxy", False)
                proxy_agent = getattr(memory, "proxy_agent", None)

                # Build title with enhanced indicators
                if confidence >= 0.8:
                    conf_emoji = "🟢"
                elif confidence >= 0.6:
                    conf_emoji = "🟡"
                elif confidence >= 0.4:
                    conf_emoji = "🟠"
                else:
                    conf_emoji = "🔴"

                proxy_indicator = (
                    f" | 🤖 {proxy_agent}"
                    if is_proxy and proxy_agent
                    else " | 🤖 Proxy" if is_proxy else " | 👤 User"
                )

                with st.expander(
                    f"Result {i} (Score: {score:.3f}): {memory.memory[:50]}... | {conf_emoji} {int(confidence * 100)}%{proxy_indicator}"
                ):
                    st.write(f"**Memory:** {memory.memory}")
                    st.write(f"**Similarity Score:** {score:.3f}")
                    st.write(f"**{conf_emoji} Confidence:** {int(confidence * 100)}%")

                    if is_proxy:
                        st.write(
                            f"**🤖 Proxy Memory** (Agent: {proxy_agent or 'Unknown'})"
                        )
                    else:
                        st.write(f"**👤 User Memory**")

                    topics = getattr(memory, "topics", [])
                    if topics:
                        st.write(f"**🏷️ Topics:** {', '.join(topics)}")
                    st.write(
                        f"**🕒 Last Updated:** {getattr(memory, 'last_updated', 'N/A')}"
                    )
                    st.write(f"**🆔 Memory ID:** {getattr(memory, 'memory_id', 'N/A')}")

                    # Memory deletion with confirmation (simplified approach like dashboard)
                    delete_key = f"delete_search_{memory.memory_id}"

                    if not st.session_state.get(
                        f"show_delete_confirm_{delete_key}", False
                    ):
                        if st.button(f"🗑️ Delete Memory", key=delete_key):
                            st.session_state[f"show_delete_confirm_{delete_key}"] = True
                            st.rerun()
                    else:
                        st.warning(
                            "⚠️ **Confirm Deletion** - This action cannot be undone!"
                        )
                        st.write(
                            f"Memory: {memory.memory[:100]}{'...' if len(memory.memory) > 100 else ''}"
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("❌ Cancel", key=f"cancel_{delete_key}"):
                                st.session_state[
                                    f"show_delete_confirm_{delete_key}"
                                ] = False
                                st.rerun()
                        with col2:
                            if st.button(
                                "🗑️ Yes, Delete",
                                key=f"confirm_{delete_key}",
                                type="primary",
                            ):
                                with st.spinner("Deleting memory..."):
                                    try:
                                        success, message = memory_helper.delete_memory(
                                            memory.memory_id
                                        )

                                        # Clear confirmation state
                                        st.session_state[
                                            f"show_delete_confirm_{delete_key}"
                                        ] = False

                                        if success:
                                            st.success(
                                                f"✅ Memory deleted successfully: {message}"
                                            )
                                            # Clear any caches and refresh
                                            st.cache_resource.clear()
                                            st.rerun()
                                        else:
                                            st.error(
                                                f"❌ Failed to delete memory: {message}"
                                            )

                                    except Exception as e:
                                        st.error(
                                            f"❌ Exception during delete: {str(e)}"
                                        )
                                        st.session_state[
                                            f"show_delete_confirm_{delete_key}"
                                        ] = False
        else:
            st.info("No matching memories found.")

    # Browse All Memories Section
    st.markdown("---")
    st.subheader("📚 Browse All Memories")
    st.markdown("*View, edit, and manage all stored memories*")

    # Date range filter like dashboard
    col1, col2, col3 = st.columns(3)

    with col1:
        memory_type = st.selectbox(
            "Memory Type",
            ["All", "Conversation", "Document", "Tool", "System"],
            help="Filter memories by type",
        )

    with col2:
        # Get all memories to determine the full date range
        try:
            all_memories = memory_helper.get_all_memories()
            memory_dates = []

            for memory in all_memories:
                last_updated = getattr(memory, "last_updated", None)
                if last_updated:
                    try:
                        # Convert memory date to date object
                        if isinstance(last_updated, str):
                            # Try to parse the date string (assuming YYYY-MM-DD format)
                            memory_date = datetime.strptime(
                                last_updated.split()[0], "%Y-%m-%d"
                            ).date()
                        elif hasattr(last_updated, "date"):
                            memory_date = last_updated.date()
                        else:
                            memory_date = last_updated
                        memory_dates.append(memory_date)
                    except (ValueError, AttributeError):
                        pass

            # Try to get user's birth date as the start date
            user_birth_date = None
            try:
                from personal_agent.core.user_registry import UserRegistry

                user_registry = UserRegistry()
                current_user = user_registry.get_current_user()
                if current_user and current_user.get("birth_date"):
                    birth_date_str = current_user["birth_date"]
                    user_birth_date = datetime.strptime(
                        birth_date_str, "%Y-%m-%d"
                    ).date()
            except Exception as e:
                logger.debug(f"Could not retrieve user birth date: {e}")

            if memory_dates:
                # Use user birth date as start date if available, otherwise use earliest memory date
                if user_birth_date:
                    default_start_date = user_birth_date
                else:
                    default_start_date = min(memory_dates)
                default_end_date = max(memory_dates)
            else:
                # Use user birth date if available, otherwise fallback to last 5 days
                if user_birth_date:
                    default_start_date = user_birth_date
                    default_end_date = datetime.now().date()
                else:
                    # Fallback to last 5 days if no memories have dates and no birth date
                    default_start_date = datetime.now().date() - timedelta(days=5)
                    default_end_date = datetime.now().date()

        except Exception:
            # Final fallback to last 5 days if there's an error
            default_start_date = datetime.now().date() - timedelta(days=5)
            default_end_date = datetime.now().date()

        date_range = st.date_input(
            "Date Range",
            value=[default_start_date, default_end_date],
            help="Filter memories by date range (start date defaults to user's birth date if available, otherwise earliest memory date)",
        )

    with col3:
        limit = st.number_input(
            "Limit",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            help="Maximum number of memories to display",
        )

    # Auto-load memories like the dashboard does (no button required)
    try:
        raw_memories = memory_helper.get_all_memories()

        # Apply date range filter if specified
        filtered_memories = raw_memories
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_memories = []
            for memory in raw_memories:
                memory_date = getattr(memory, "last_updated", None)
                if memory_date:
                    try:
                        # Convert memory date to date object for comparison
                        if isinstance(memory_date, str):
                            # Try to parse the date string (assuming YYYY-MM-DD format)
                            memory_date = datetime.strptime(
                                memory_date.split()[0], "%Y-%m-%d"
                            ).date()
                        elif hasattr(memory_date, "date"):
                            memory_date = memory_date.date()

                        # Check if memory date is within range
                        if start_date <= memory_date <= end_date:
                            filtered_memories.append(memory)
                    except (ValueError, AttributeError):
                        # If date parsing fails, include the memory
                        filtered_memories.append(memory)
                else:
                    # If no date, include the memory
                    filtered_memories.append(memory)

        # Apply limit
        filtered_memories = filtered_memories[:limit]

        if filtered_memories:
            st.info(
                f"Displaying {len(filtered_memories)} of {len(raw_memories)} total memories"
            )
            for memory in filtered_memories:
                # Get enhanced fields
                confidence = getattr(memory, "confidence", 1.0)
                is_proxy = getattr(memory, "is_proxy", False)
                proxy_agent = getattr(memory, "proxy_agent", None)

                # Build title with enhanced indicators
                if confidence >= 0.8:
                    conf_emoji = "🟢"
                elif confidence >= 0.6:
                    conf_emoji = "🟡"
                elif confidence >= 0.4:
                    conf_emoji = "🟠"
                else:
                    conf_emoji = "🔴"

                proxy_str = (
                    f" | 🤖 {proxy_agent}"
                    if is_proxy and proxy_agent
                    else " | 🤖 Proxy" if is_proxy else " | 👤 User"
                )

                with st.expander(
                    f"Memory: {memory.memory[:50]}... | {conf_emoji} {int(confidence * 100)}%{proxy_str}"
                ):
                    st.write(f"**Content:** {memory.memory}")
                    st.write(f"**🆔 Memory ID:** {getattr(memory, 'memory_id', 'N/A')}")
                    st.write(
                        f"**🕒 Last Updated:** {getattr(memory, 'last_updated', 'N/A')}"
                    )

                    st.write(f"**{conf_emoji} Confidence:** {int(confidence * 100)}%")

                    if is_proxy:
                        st.write(
                            f"**🤖 Proxy Memory** (Agent: {proxy_agent or 'Unknown'})"
                        )
                    else:
                        st.write(f"**👤 User Memory**")

                    topics = getattr(memory, "topics", [])
                    if topics:
                        st.write(f"**🏷️ Topics:** {', '.join(topics)}")

                    # Memory deletion with confirmation (simplified approach like dashboard)
                    delete_key = f"delete_browse_{memory.memory_id}"

                    if not st.session_state.get(
                        f"show_delete_confirm_{delete_key}", False
                    ):
                        if st.button(f"🗑️ Delete", key=delete_key):
                            st.session_state[f"show_delete_confirm_{delete_key}"] = True
                            st.rerun()
                    else:
                        st.warning(
                            "⚠️ **Confirm Deletion** - This action cannot be undone!"
                        )
                        st.write(
                            f"Memory: {memory.memory[:100]}{'...' if len(memory.memory) > 100 else ''}"
                        )

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("❌ Cancel", key=f"cancel_{delete_key}"):
                                st.session_state[
                                    f"show_delete_confirm_{delete_key}"
                                ] = False
                                st.rerun()
                        with col2:
                            if st.button(
                                "🗑️ Yes, Delete",
                                key=f"confirm_{delete_key}",
                                type="primary",
                            ):
                                with st.spinner("Deleting memory..."):
                                    try:
                                        success, message = memory_helper.delete_memory(
                                            memory.memory_id
                                        )

                                        # Clear confirmation state
                                        st.session_state[
                                            f"show_delete_confirm_{delete_key}"
                                        ] = False

                                        if success:
                                            st.success(
                                                f"✅ Memory deleted successfully: {message}"
                                            )
                                            # Clear any caches and refresh
                                            st.cache_resource.clear()
                                            st.rerun()
                                        else:
                                            st.error(
                                                f"❌ Failed to delete memory: {message}"
                                            )

                                    except Exception as e:
                                        st.error(
                                            f"❌ Exception during delete: {str(e)}"
                                        )
                                        st.session_state[
                                            f"show_delete_confirm_{delete_key}"
                                        ] = False
        else:
            st.info("No memories stored yet.")
    except Exception as e:
        st.error(f"Error loading memories: {str(e)}")

    # Memory Statistics Section
    st.markdown("---")
    st.subheader("📊 Memory Statistics")
    st.markdown("*Analytics and insights about your stored memories*")
    if st.button("📈 Show Statistics", key="show_stats_btn"):
        stats = memory_helper.get_memory_stats()
        if "error" not in stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Memories", stats.get("total_memories", 0))
            with col2:
                st.metric("Recent (24h)", stats.get("recent_memories_24h", 0))
            with col3:
                avg_length = stats.get("average_memory_length", 0)
                st.metric(
                    "Avg Length", f"{avg_length:.1f} chars" if avg_length else "N/A"
                )
            topic_dist = stats.get("topic_distribution", {})
            if topic_dist:
                st.subheader("📈 Topic Distribution")
                for topic, count in sorted(
                    topic_dist.items(), key=lambda x: x[1], reverse=True
                ):
                    st.write(f"**{topic.title()}:** {count} memories")
        else:
            st.error(f"Error getting statistics: {stats['error']}")

    # Memory Sync Status Section
    st.markdown("---")
    st.subheader("🔄 Memory Sync Status")
    st.markdown(
        "*Monitor synchronization between local SQLite and LightRAG graph memories*"
    )
    if st.button("🔍 Check Sync Status", key="check_sync_btn"):
        sync_status = memory_helper.get_memory_sync_status()
        if "error" not in sync_status:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Local Memories", sync_status.get("local_memory_count", 0))
            with col2:
                st.metric("Graph Entities", sync_status.get("graph_entity_count", 0))
            with col3:
                sync_ratio = sync_status.get("sync_ratio", 0)
                st.metric("Sync Ratio", f"{sync_ratio:.2f}")

            status = sync_status.get("status", "unknown")
            if status == "synced":
                st.success(
                    "✅ Memories are synchronized between local and graph systems"
                )
            elif status == "out_of_sync":
                st.warning("⚠️ Memories may be out of sync between systems")
                if st.button("🔄 Sync Missing Memories", key="sync_missing_btn"):
                    # Sync any missing memories to graph
                    local_memories = memory_helper.get_all_memories()
                    synced_count = 0
                    for memory in local_memories:
                        try:
                            success, result = memory_helper.sync_memory_to_graph(
                                memory.memory, getattr(memory, "topics", None)
                            )
                            if success:
                                synced_count += 1
                        except Exception as e:
                            st.error(f"Error syncing memory: {e}")

                    if synced_count > 0:
                        st.success(f"✅ Synced {synced_count} memories to graph system")
                    else:
                        st.info("No memories needed syncing")
            else:
                st.error(f"❌ Sync status unknown: {status}")
        else:
            st.error(
                f"Error checking sync status: {sync_status.get('error', 'Unknown error')}"
            )


def render_knowledge_status(knowledge_helper):
    """Renders the status of the knowledge bases in an expander."""
    with st.expander("ℹ️ Knowledge Base Status"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**SQLite/LanceDB**")

            # Show the knowledge directory path
            st.caption(f"**Data Dir:** {USER_DATA_DIR}")
            st.caption(f"**Knowledge Dir:** {AGNO_KNOWLEDGE_DIR}")

            # FORCE AGENT/TEAM INITIALIZATION TO CHECK REAL STATUS
            try:
                current_mode = st.session_state.get(SESSION_KEY_AGENT_MODE, "single")

                if current_mode == "team":
                    # Handle team mode
                    team = st.session_state.get(SESSION_KEY_TEAM)
                    if team:
                        # For team mode, we don't need to trigger initialization
                        # as the team should already be initialized
                        km = (
                            knowledge_helper.knowledge_manager
                        )  # This will trigger fresh check
                        if km:
                            st.success("✅ Ready")
                            # Show additional info if available
                            if hasattr(km, "vector_db") and km.vector_db:
                                st.caption("Vector DB: Connected")
                            elif hasattr(km, "search"):
                                st.caption("Knowledge base loaded")
                        else:
                            st.warning("⚠️ Offline")
                            st.caption("Knowledge manager not available")
                    else:
                        st.error("❌ Error: Team not initialized")
                        st.caption("Failed to initialize team")
                else:
                    # Handle single agent mode
                    agent = st.session_state.get(SESSION_KEY_AGENT)
                    if agent:
                        # Show initialization status
                        if not getattr(agent, "_initialized", False):
                            with st.spinner("Initializing knowledge system..."):
                                if hasattr(agent, "_ensure_initialized"):
                                    # This will trigger initialization if not already done
                                    asyncio.run(agent._ensure_initialized())
                        else:
                            # Agent already initialized, just ensure knowledge helper is updated
                            if hasattr(agent, "_ensure_initialized"):
                                asyncio.run(agent._ensure_initialized())

                        # Now check the real status after ensuring initialization
                        km = (
                            knowledge_helper.knowledge_manager
                        )  # This will trigger fresh check
                        if km:
                            st.success("✅ Ready")
                            # Show additional info if available
                            if hasattr(km, "vector_db") and km.vector_db:
                                st.caption("Vector DB: Connected")
                            elif hasattr(km, "search"):
                                st.caption("Knowledge base loaded")
                        else:
                            st.warning("⚠️ Offline")
                            st.caption("Knowledge manager not available")
                    else:
                        st.error("❌ Error: Agent not initialized")
                        st.caption("Failed to initialize agent")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.caption("Failed to initialize knowledge system")

        with col2:
            st.markdown("**RAG**")

            # RAG Server Location Dropdown
            rag_location = st.selectbox(
                "RAG Server:",
                ["localhost", "100.100.248.61"],
                index=(
                    0
                    if st.session_state[SESSION_KEY_RAG_SERVER_LOCATION] == "localhost"
                    else 1
                ),
                key="rag_server_dropdown",
            )

            # Check if location changed and show apply button
            location_changed = (
                rag_location != st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]
            )

            if location_changed:
                if st.button(
                    "🔄 Apply & Rescan", key="apply_rag_server", type="primary"
                ):
                    # Update session state
                    st.session_state[SESSION_KEY_RAG_SERVER_LOCATION] = rag_location

                    # Determine the new RAG URL
                    if rag_location == "localhost":
                        new_rag_url = "http://localhost:9621"
                    else:  # 100.100.248.61
                        new_rag_url = "http://100.100.248.61:9621"

                    # Trigger rescan on the new server
                    with st.spinner(
                        f"Switching to {rag_location} and triggering rescan..."
                    ):
                        try:
                            import requests

                            rescan_response = requests.post(
                                f"{new_rag_url}/documents/scan", timeout=10
                            )
                            if rescan_response.status_code == 200:
                                st.success(
                                    f"✅ Switched to {rag_location} and rescan initiated!"
                                )
                            else:
                                st.warning(
                                    f"⚠️ Switched to {rag_location} but rescan failed (status: {rescan_response.status_code})"
                                )
                        except requests.exceptions.RequestException as e:
                            st.error(
                                f"❌ Failed to connect to {rag_location}: {str(e)}"
                            )

                    # Force a rerun to update the status display
                    st.rerun()

            # Determine the RAG URL based on current session state
            if st.session_state[SESSION_KEY_RAG_SERVER_LOCATION] == "localhost":
                rag_url = "http://localhost:9621"
            else:  # 100.100.248.61
                rag_url = "http://100.100.248.61:9621"

            # Check RAG server status with improved reliability and error handling
            try:
                # Increase timeout and add better error handling
                import requests

                health_response = requests.get(
                    f"{rag_url}/health", timeout=10
                )  # Increased from 3 to 10
                if health_response.status_code == 200:
                    # Get pipeline status for more detailed information
                    try:
                        pipeline_response = requests.get(
                            f"{rag_url}/documents/pipeline_status", timeout=10
                        )
                        if pipeline_response.status_code == 200:
                            pipeline_data = pipeline_response.json()

                            # Check if pipeline is processing
                            if pipeline_data.get("is_processing", False):
                                st.warning("🔄 Processing")
                                if pipeline_data.get("current_task"):
                                    st.caption(f"Task: {pipeline_data['current_task']}")
                            elif pipeline_data.get("queue_size", 0) > 0:
                                st.info(
                                    f"📋 Queued ({pipeline_data['queue_size']} items)"
                                )
                            else:
                                st.success("✅ Ready")

                            # Show additional pipeline info if available
                            if pipeline_data.get("last_processed"):
                                st.caption(f"Last: {pipeline_data['last_processed']}")
                        else:
                            # Fallback to basic ready status if pipeline endpoint fails
                            st.success("✅ Ready")
                            st.caption("(Pipeline status unavailable)")
                    except requests.exceptions.RequestException:
                        # Pipeline status failed, but health passed
                        st.success("✅ Ready")
                        st.caption("(Basic health check passed)")
                else:
                    st.error(f"❌ Error ({health_response.status_code})")
                    st.caption(
                        f"Server responded with error: {health_response.status_code}"
                    )
            except requests.exceptions.ConnectTimeout:
                st.warning("⚠️ Timeout")
                st.caption(
                    f"Connection timeout to {st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]}"
                )
            except requests.exceptions.ConnectionError:
                st.warning("⚠️ Offline")
                st.caption(
                    f"Cannot connect to {st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]}"
                )
            except requests.exceptions.RequestException as e:
                st.warning("⚠️ Error")
                st.caption(f"Request failed: {str(e)}")

            # Show current server info
            if not location_changed:
                st.caption(
                    f"Current: {st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]}"
                )

        # Add debug information in an expander if debug mode is enabled
        if st.session_state.get(SESSION_KEY_SHOW_DEBUG, False):
            with st.expander("🔍 Debug Status Info"):
                current_mode = st.session_state.get(SESSION_KEY_AGENT_MODE, "single")
                st.write(f"**Current Mode:** {current_mode}")

                if current_mode == "team":
                    # Debug info for team mode
                    team = st.session_state.get(SESSION_KEY_TEAM)
                    if team:
                        st.write(f"**Team Type:** {type(team).__name__}")
                        st.write(
                            f"**Team Members:** {len(getattr(team, 'members', []))}"
                        )
                        if hasattr(team, "agno_memory"):
                            st.write(f"**Team Memory:** {team.agno_memory is not None}")
                    else:
                        st.write("**Team:** Not initialized")
                else:
                    # Debug info for single agent mode
                    agent = st.session_state.get(SESSION_KEY_AGENT)
                    if agent:
                        st.write(
                            f"**Agent Initialized:** {getattr(agent, '_initialized', False)}"
                        )
                        st.write(f"**Agent Type:** {type(agent).__name__}")
                        if hasattr(agent, "agno_knowledge"):
                            st.write(
                                f"**Agent Knowledge:** {agent.agno_knowledge is not None}"
                            )
                        if hasattr(agent, "agno_memory"):
                            st.write(
                                f"**Agent Memory:** {agent.agno_memory is not None}"
                            )
                    else:
                        st.write("**Agent:** Not initialized")

                st.write(
                    f"**Knowledge Manager:** {knowledge_helper.knowledge_manager is not None}"
                )
                st.write(f"**RAG URL:** {rag_url}")
                st.write(
                    f"**RAG Location:** {st.session_state[SESSION_KEY_RAG_SERVER_LOCATION]}"
                )


def render_sidebar():
    """Render the sidebar with configuration and control options."""
    with st.sidebar:
        # Theme selector at the very top
        st.header("🎨 Theme")
        dark_mode = st.toggle(
            "Dark Mode", value=st.session_state.get(SESSION_KEY_DARK_THEME, False)
        )

        if dark_mode != st.session_state.get(SESSION_KEY_DARK_THEME, False):
            st.session_state[SESSION_KEY_DARK_THEME] = dark_mode
            st.rerun()

        st.header("Provider Selection")

        # Provider selector
        available_providers = ["ollama", "lm-studio", "openai"]
        current_provider = os.getenv("PROVIDER", "ollama")

        selected_provider = st.selectbox(
            "Select AI Provider:",
            available_providers,
            index=(
                available_providers.index(current_provider)
                if current_provider in available_providers
                else 0
            ),
            help="Choose your AI model provider. Each provider has different default models.",
        )

        # Show provider-specific information based on CURRENT provider (not selected)
        from personal_agent.config import get_provider_default_model

        current_default_model = get_provider_default_model(current_provider)

        if current_provider == "ollama":
            st.caption(
                "🐳 **Current**: Ollama - Local models, full control, no API costs"
            )
        elif current_provider == "lm-studio":
            st.caption(
                "🎭 **Current**: LM Studio - Local models with user-friendly interface"
            )
        elif current_provider == "openai":
            st.caption("🔗 **Current**: OpenAI - Cloud models, requires API key")

        st.caption(f"📋 **Current Default Model:** {current_default_model}")

        # Show preview of selected provider if different from current
        if selected_provider != current_provider:
            selected_default_model = get_provider_default_model(selected_provider)
            if selected_provider == "ollama":
                st.caption(
                    "� **Preview**: Ollama - Local models, full control, no API costs"
                )
            elif selected_provider == "lm-studio":
                st.caption(
                    "🔮 **Preview**: LM Studio - Local models with user-friendly interface"
                )
            elif selected_provider == "openai":
                st.caption("🔮 **Preview**: OpenAI - Cloud models, requires API key")
            st.caption(f"📋 **New Default Model:** {selected_default_model}")

        # Apply provider change
        if selected_provider != current_provider:
            if st.button(f"🔄 Switch to {selected_provider.title()}", type="primary"):
                with st.spinner(
                    f"Switching to {selected_provider.title()} provider..."
                ):
                    # Use PersonalAgentConfig for provider switching
                    from personal_agent.config.runtime_config import get_config

                    config = get_config()

                    # Switch provider (automatically sets default model)
                    config.set_provider(selected_provider, auto_set_model=True)
                    new_default_model = config.model
                    new_url = config.get_effective_base_url()

                    logger.info(
                        f"🔄 Switched provider to {selected_provider}, default model: {new_default_model}, URL: {new_url}"
                    )

                    # Clear available models cache to force refresh
                    if SESSION_KEY_AVAILABLE_MODELS in st.session_state:
                        del st.session_state[SESSION_KEY_AVAILABLE_MODELS]

                    # Update session state to match config
                    st.session_state[SESSION_KEY_CURRENT_MODEL] = new_default_model
                    st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = new_url
                    logger.info(
                        f"🔄 Updated session state: model={new_default_model}, url={new_url}"
                    )

                    st.success(
                        f"✅ Switched to {selected_provider.title()} provider with default model: {new_default_model}"
                    )
                    st.info(
                        "💡 **Tip**: Click 'Fetch Available Models' to see models available in the new provider, then select and apply a model to reinitialize the agent/team."
                    )
                    st.rerun()

        st.header("Model Selection")

        # Show current provider and model prominently from config
        from personal_agent.config.runtime_config import get_config

        config = get_config()
        provider = config.provider
        provider_display = (
            provider.upper()
            if provider == "ollama"
            else "LM Studio" if provider == "lm-studio" else provider.title()
        )
        current_model = st.session_state.get(SESSION_KEY_CURRENT_MODEL, "Unknown")
        st.write(f"**Current Provider:** {provider_display}")
        st.write(f"**Current Model:** {current_model}")

        new_ollama_url = st.text_input(
            "**Provider URL:**", value=st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]
        )
        if st.button("🔄 Fetch Available Models"):
            with st.spinner("Fetching models..."):
                from personal_agent.tools.streamlit_config import get_available_models

                current_provider = os.getenv("PROVIDER", "ollama")
                available_models = get_available_models(
                    new_ollama_url, provider=current_provider
                )
                if available_models:
                    st.session_state[SESSION_KEY_AVAILABLE_MODELS] = available_models
                    st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = new_ollama_url
                    st.success(f"Found {len(available_models)} models!")
                else:
                    st.error("No models found or connection failed")

        if (
            SESSION_KEY_AVAILABLE_MODELS in st.session_state
            and st.session_state[SESSION_KEY_AVAILABLE_MODELS]
        ):
            current_model_index = 0
            if (
                st.session_state[SESSION_KEY_CURRENT_MODEL]
                in st.session_state[SESSION_KEY_AVAILABLE_MODELS]
            ):
                current_model_index = st.session_state[
                    SESSION_KEY_AVAILABLE_MODELS
                ].index(st.session_state[SESSION_KEY_CURRENT_MODEL])
            selected_model = st.selectbox(
                "Select Model:",
                st.session_state[SESSION_KEY_AVAILABLE_MODELS],
                index=current_model_index,
            )
            if st.button("🚀 Apply Model Selection"):
                # Detect provider change based on model name
                from personal_agent.tools.streamlit_config import (
                    args,
                    detect_provider_from_model_name,
                    get_appropriate_base_url,
                )

                detected_provider = detect_provider_from_model_name(selected_model)
                current_provider = os.getenv("PROVIDER", "ollama")

                provider_changed = detected_provider != current_provider
                model_changed = (
                    selected_model != st.session_state[SESSION_KEY_CURRENT_MODEL]
                )
                url_changed = (
                    new_ollama_url != st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]
                )

                if model_changed or url_changed or provider_changed:
                    # CRITICAL: If provider is changing, update URL FIRST before any initialization
                    if provider_changed:
                        st.warning(
                            f"🔄 Auto-detected provider change from {current_provider} to {detected_provider}"
                        )
                        st.info(
                            "💡 **Note**: You selected a model that requires a different provider. The system will switch providers and use the selected model name."
                        )

                        # CRITICAL: Get the correct URL for the new provider BEFORE initialization
                        target_url = get_appropriate_base_url(
                            detected_provider, use_remote=args.remote
                        )
                        new_ollama_url = target_url  # Update URL to match provider
                        logger.info(
                            f"🔄 Provider change: Updated URL from {st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]} to {new_ollama_url}"
                        )

                    # CRITICAL: Even if provider didn't change, ensure URL matches current provider
                    # This handles the case where user manually changed the URL input
                    if not provider_changed and url_changed:
                        # Verify the URL is appropriate for the current provider
                        expected_url = get_appropriate_base_url(
                            detected_provider, use_remote=args.remote
                        )
                        if new_ollama_url != expected_url:
                            logger.warning(
                                f"⚠️ URL mismatch: User entered {new_ollama_url}, but provider {detected_provider} expects {expected_url}"
                            )
                            # Use the user-provided URL but log the discrepancy

                    current_mode = st.session_state.get(
                        SESSION_KEY_AGENT_MODE, "single"
                    )
                    spinner_text = (
                        "Reinitializing team..."
                        if current_mode == "team"
                        else "Reinitializing agent..."
                    )

                    with st.spinner(spinner_text):
                        old_model = st.session_state[SESSION_KEY_CURRENT_MODEL]
                        old_url = st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]

                        logger.info(
                            "🔄 MODEL UPDATE: Changing from %s to %s",
                            old_model,
                            selected_model,
                        )
                        logger.info(
                            "🔄 URL UPDATE: Changing from %s to %s",
                            old_url,
                            new_ollama_url,
                        )

                        # Handle provider switching if needed
                        if provider_changed:
                            logger.info(
                                "🔄 PROVIDER CHANGE DETECTED: Switching from %s to %s for model %s",
                                current_provider,
                                detected_provider,
                                selected_model,
                            )

                            # Update provider and get appropriate URL
                            from personal_agent.tools.streamlit_config import (
                                args,
                                update_provider_and_reinitialize,
                            )

                            success, message, suggested_url = (
                                update_provider_and_reinitialize(
                                    detected_provider,
                                    selected_model,
                                    use_remote=args.remote,
                                )
                            )

                            if success:
                                st.info(f"🔄 {message}")
                                # Use the suggested URL if different from user input
                                if suggested_url and suggested_url != new_ollama_url:
                                    logger.info(
                                        "📡 Using provider-appropriate URL: %s",
                                        suggested_url,
                                    )
                                    new_ollama_url = suggested_url

                                # Clear available models cache to force re-fetch from new provider
                                if SESSION_KEY_AVAILABLE_MODELS in st.session_state:
                                    del st.session_state[SESSION_KEY_AVAILABLE_MODELS]
                                    logger.info(
                                        "🔄 Cleared model cache - user should re-fetch models for new provider"
                                    )
                            else:
                                st.error(f"❌ Provider switch failed: {message}")
                                return  # Exit early on provider switch failure

                        st.session_state[SESSION_KEY_CURRENT_MODEL] = selected_model
                        st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL] = (
                            new_ollama_url
                        )

                        if current_mode == "team":
                            logger.info(
                                "🤖 TEAM REINIT: Reinitializing team with new model %s",
                                selected_model,
                            )
                            # Reinitialize team with detected provider
                            # Note: initialize_team() now uses get_config() for all settings
                            from personal_agent.tools.streamlit_agent_manager import (
                                initialize_team,
                            )

                            st.session_state[SESSION_KEY_TEAM] = initialize_team(
                                recreate=False
                            )

                            # Update helper classes with new team - use knowledge agent directly
                            team = st.session_state[SESSION_KEY_TEAM]
                            if hasattr(team, "members") and team.members:
                                knowledge_agent = team.members[
                                    0
                                ]  # First member is the knowledge agent
                                from personal_agent.tools.streamlit_helpers import (
                                    StreamlitKnowledgeHelper,
                                    StreamlitMemoryHelper,
                                )

                                st.session_state[SESSION_KEY_MEMORY_HELPER] = (
                                    StreamlitMemoryHelper(knowledge_agent)
                                )
                                st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                                    StreamlitKnowledgeHelper(knowledge_agent)
                                )
                            else:
                                # Fallback: create with team object
                                from personal_agent.tools.streamlit_helpers import (
                                    StreamlitKnowledgeHelper,
                                    StreamlitMemoryHelper,
                                )

                                st.session_state[SESSION_KEY_MEMORY_HELPER] = (
                                    StreamlitMemoryHelper(team)
                                )
                                st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                                    StreamlitKnowledgeHelper(team)
                                )

                            success_msg = f"Team updated to use model: {selected_model}"
                            logger.info("✅ TEAM UPDATE COMPLETE: %s", success_msg)
                        else:
                            logger.info(
                                "🧠 AGENT REINIT: Reinitializing agent with new model %s",
                                selected_model,
                            )
                            # Reinitialize single agent with detected provider
                            # Note: initialize_agent() now uses get_config() for all settings
                            from personal_agent.tools.streamlit_agent_manager import (
                                initialize_agent,
                            )

                            st.session_state[SESSION_KEY_AGENT] = initialize_agent(
                                recreate=False
                            )

                            # Update helper classes with new agent
                            from personal_agent.tools.streamlit_helpers import (
                                StreamlitKnowledgeHelper,
                                StreamlitMemoryHelper,
                            )

                            st.session_state[SESSION_KEY_MEMORY_HELPER] = (
                                StreamlitMemoryHelper(
                                    st.session_state[SESSION_KEY_AGENT]
                                )
                            )
                            st.session_state[SESSION_KEY_KNOWLEDGE_HELPER] = (
                                StreamlitKnowledgeHelper(
                                    st.session_state[SESSION_KEY_AGENT]
                                )
                            )

                            success_msg = (
                                f"Agent updated to use model: {selected_model}"
                            )
                            logger.info("✅ AGENT UPDATE COMPLETE: %s", success_msg)

                        st.session_state[SESSION_KEY_MESSAGES] = []

                        # Enhanced success message with provider info
                        final_provider = os.getenv("PROVIDER", "ollama")
                        provider_display = (
                            final_provider.upper()
                            if final_provider == "ollama"
                            else (
                                "LM Studio"
                                if final_provider == "lm-studio"
                                else final_provider.title()
                            )
                        )
                        enhanced_msg = (
                            f"✅ {success_msg} using {provider_display} provider"
                        )
                        if provider_changed:
                            enhanced_msg += f" (auto-switched from {current_provider})"
                            st.success(enhanced_msg)
                            st.info(
                                "💡 **Tip**: After switching providers, click 'Fetch Available Models' to see models available in the new provider"
                            )
                        else:
                            st.success(enhanced_msg)

                        st.rerun()
                else:
                    st.info("Model and URL are already current")
        else:
            st.info("Click 'Fetch Available Models' to see available models")

        # Dynamic header based on mode
        current_mode = st.session_state.get(SESSION_KEY_AGENT_MODE, "single")
        if current_mode == "team":
            st.header("Team Information")
        else:
            st.header("Agent Information")

        st.write(f"**Current Model:** {st.session_state[SESSION_KEY_CURRENT_MODEL]}")
        # st.write(
        #    f"**Current Ollama URL:** {st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]}"
        # )

        # Show mode-specific information
        if current_mode == "team":
            # Team-specific information
            team = st.session_state.get(SESSION_KEY_TEAM)
            if team:
                st.write(f"**Mode:** 🤖 Team of Agents")

                # Make team information collapsible
                with st.expander("🤖 Team Details", expanded=False):
                    # Show team composition
                    members = getattr(team, "members", [])
                    st.write(f"**Team Members:** {len(members)}")

                    if members:
                        st.write("**Specialized Agents:**")
                        for member in members:
                            member_name = getattr(member, "name", "Unknown")
                            member_role = getattr(member, "role", "Unknown")
                            member_tools = len(getattr(member, "tools", []))
                            st.write(
                                f"• **{member_name}**: {member_role} ({member_tools} tools)"
                            )

                    # Show team capabilities
                    st.write("**Team Capabilities:**")
                    st.write("• 🧠 Memory Management")
                    st.write("• 📚 Knowledge Base Access")
                    st.write("• 🌐 Web Research")
                    st.write("• ✍️ Writing & Content Creation")
                    st.write("• 🎨 Image Creation")
                    st.write("• 🔬 PubMed Research")
                    st.write("• 💰 Finance & Calculations")
                    st.write("• 📁 File Operations")
            else:
                st.write(f"**Mode:** 🤖 Team of Agents")
                st.warning("⚠️ Team not initialized")
        else:
            # Single agent information
            agent = st.session_state.get(SESSION_KEY_AGENT)
            if agent:
                st.write(f"**Mode:** 🧠 Single Agent")
                st.write(f"**Agent Type:** {type(agent).__name__}")

                # Show agent capabilities
                st.write("**Agent Capabilities:**")
                st.write("• 🧠 Memory Management")
                st.write("• 📚 Knowledge Base Access")
                st.write("• 🔧 Tool Integration")
                if hasattr(agent, "enable_mcp") and agent.enable_mcp:
                    st.write("• 🔌 MCP Server Integration")
            else:
                st.write(f"**Mode:** 🧠 Single Agent")
                st.warning("⚠️ Agent not initialized")

        # Show comprehensive model configuration for current model
        current_model = st.session_state[SESSION_KEY_CURRENT_MODEL]
        current_ollama_url = st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]

        with st.expander("⚙️ Model Configuration", expanded=False):
            try:
                # Get comprehensive model configuration
                from personal_agent.config.model_contexts import get_model_config_dict

                model_config = get_model_config_dict(current_model, current_ollama_url)

                st.write("**Model Parameters:**")
                params = model_config.get("parameters", {})
                st.write(f"• Temperature: {params.get('temperature', 'N/A')}")
                st.write(f"• Top P: {params.get('top_p', 'N/A')}")
                st.write(f"• Top K: {params.get('top_k', 'N/A')}")
                st.write(
                    f"• Repetition Penalty: {params.get('repetition_penalty', 'N/A')}"
                )

                st.write("**Context Configuration:**")
                context_size = model_config.get("context_size", "N/A")
                if isinstance(context_size, int):
                    st.write(f"• Context Size: {context_size:,} tokens")
                else:
                    st.write(f"• Context Size: {context_size}")

                st.caption(
                    "Configuration sourced from model_contexts.py and environment variables"
                )

            except Exception as e:
                st.error(f"Error loading model configuration: {e}")
                # Fallback to basic model info
                st.write(f"**Model:** {current_model}")
                st.write(f"**Ollama URL:** {current_ollama_url}")

        # Show debug info about URL configuration
        if st.session_state.get(SESSION_KEY_SHOW_DEBUG, False):
            with st.expander("🔍 URL Debug Info", expanded=False):
                st.write(
                    f"**--remote flag:** {st.session_state.get('args', {}).get('remote', 'N/A')}"
                )
                from personal_agent.config import OLLAMA_URL, REMOTE_OLLAMA_URL

                st.write(f"**OLLAMA_URL (local):** {OLLAMA_URL}")
                st.write(f"**REMOTE_OLLAMA_URL:** {REMOTE_OLLAMA_URL}")

                # Show current provider and calculate effective URL dynamically
                provider = os.getenv("PROVIDER", "ollama")
                st.write(f"**Current Provider:** {provider}")

                # Calculate the effective URL based on current provider and remote flag
                from personal_agent.tools.streamlit_config import (
                    get_appropriate_base_url,
                )

                use_remote = st.session_state.get("args", {}).get("remote", False)
                effective_url = get_appropriate_base_url(provider, use_remote)
                st.write(f"**EFFECTIVE_URL (current provider):** {effective_url}")

                st.write(
                    f"**Session Ollama URL:** {st.session_state[SESSION_KEY_CURRENT_OLLAMA_URL]}"
                )

                # Show agent/team specific debug info

                if current_mode == "team":
                    team = st.session_state.get(SESSION_KEY_TEAM)
                    if team and hasattr(team, "ollama_base_url"):
                        st.write(f"**Team's Ollama URL:** {team.ollama_base_url}")
                    else:
                        st.write("**Team URL:** Not accessible")
                else:
                    agent = st.session_state.get(SESSION_KEY_AGENT)
                    if agent:
                        # Show provider-specific URLs
                        if provider == "lm-studio":
                            if hasattr(agent, "model_manager") and hasattr(
                                agent.model_manager, "lmstudio_base_url"
                            ):
                                st.write(
                                    f"**Agent's LM Studio URL:** {agent.model_manager.lmstudio_base_url}"
                                )
                            else:
                                lmstudio_url = os.getenv("LMSTUDIO_BASE_URL", "Not set")
                                st.write(f"**LM Studio URL (env):** {lmstudio_url}")
                        else:
                            if hasattr(agent, "ollama_base_url"):
                                st.write(
                                    f"**Agent's Ollama URL:** {agent.ollama_base_url}"
                                )
                            elif hasattr(agent, "model_manager") and hasattr(
                                agent.model_manager, "ollama_base_url"
                            ):
                                st.write(
                                    f"**Agent's Model Manager URL:** {agent.model_manager.ollama_base_url}"
                                )
                            else:
                                st.write("**Agent URL:** Not accessible")

                        # Show model manager provider info
                        if hasattr(agent, "model_manager"):
                            st.write(
                                f"**Model Manager Provider:** {getattr(agent.model_manager, 'model_provider', 'Unknown')}"
                            )
                    else:
                        st.write("**Agent:** Not accessible")

        st.header("Controls")
        if st.button("Clear Chat History"):
            st.session_state[SESSION_KEY_MESSAGES] = []
            st.rerun()

        st.header("Debug Info")
        debug_label = "Enable Debug Mode"
        if st.session_state.get("DEBUG_FLAG", False):
            debug_label += " (CLI enabled)"
        st.session_state[SESSION_KEY_SHOW_DEBUG] = st.checkbox(
            debug_label,
            value=st.session_state.get(
                SESSION_KEY_SHOW_DEBUG, st.session_state.get("DEBUG_FLAG", False)
            ),
            help="Debug mode can be enabled via --debug flag or this checkbox",
        )
        if st.session_state.get(SESSION_KEY_SHOW_DEBUG):
            st.subheader("📊 Performance Statistics")
            stats = st.session_state[SESSION_KEY_PERFORMANCE_STATS]
            if stats["total_requests"] > 0:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Requests", stats["total_requests"])
                    st.metric(
                        "Avg Response Time", f"{stats['average_response_time']:.3f}s"
                    )
                    st.metric(
                        "Fastest Response",
                        (
                            f"{stats['fastest_response']:.3f}s"
                            if stats["fastest_response"] != float("inf")
                            else "N/A"
                        ),
                    )
                with col2:
                    st.metric("Total Tool Calls", stats["tool_calls_count"])
                    st.metric("Avg Tokens/Request", f"{stats['average_tokens']:.0f}")
                    st.metric("Slowest Response", f"{stats['slowest_response']:.3f}s")
            else:
                st.info("No requests made yet.")

            if len(st.session_state[SESSION_KEY_DEBUG_METRICS]) > 1:
                st.subheader("📈 Response Time Trend")
                df = pd.DataFrame(st.session_state[SESSION_KEY_DEBUG_METRICS])
                df = df[df["success"]]
                if not df.empty and len(df) > 1:
                    chart_data = (
                        df[["timestamp", "response_time"]].copy().set_index("timestamp")
                    )

                    # Apply theme-aware styling for the chart
                    is_dark_theme = st.session_state.get(SESSION_KEY_DARK_THEME, False)

                    # Create base chart
                    chart = (
                        alt.Chart(chart_data.reset_index())
                        .mark_line(
                            point=True,
                            color="#1f77b4" if not is_dark_theme else "#ff7f0e",
                        )
                        .encode(
                            x=alt.X("timestamp:O", title="Time"),
                            y=alt.Y("response_time:Q", title="Response Time (s)"),
                            tooltip=["timestamp:O", "response_time:Q"],
                        )
                        .properties(title="Response Time Trend")
                    )

                    # Apply theme-specific configuration
                    if is_dark_theme:
                        # Configure for dark theme
                        chart = (
                            chart.configure_view(
                                strokeWidth=0,
                                fill="#0e1117",  # Dark background color matching Streamlit dark theme
                            )
                            .configure_axis(
                                labelColor="white",
                                titleColor="white",
                                gridColor="#444444",
                                domainColor="white",
                            )
                            .configure_title(color="white")
                            .configure_legend(labelColor="white", titleColor="white")
                            .configure(
                                background="#0e1117"  # Set overall chart background
                            )
                        )
                    else:
                        # Configure for light theme (default)
                        chart = (
                            chart.configure_view(
                                strokeWidth=0, fill="white"  # Light background color
                            )
                            .configure_axis(
                                labelColor="black",
                                titleColor="black",
                                gridColor="#e0e0e0",
                                domainColor="black",
                            )
                            .configure_title(color="black")
                            .configure_legend(labelColor="black", titleColor="black")
                            .configure(
                                background="white"  # Set overall chart background
                            )
                        )

                    st.altair_chart(chart, use_container_width=True)

            st.subheader("🔧 Recent Tool Calls")
            if st.session_state[SESSION_KEY_DEBUG_METRICS]:
                # Filter entries that have tool calls
                tool_call_entries = [
                    entry
                    for entry in st.session_state[SESSION_KEY_DEBUG_METRICS]
                    if entry.get("tool_calls", 0) > 0
                ]

                if tool_call_entries:
                    for entry in reversed(
                        tool_call_entries[-5:]
                    ):  # Show last 5 tool call entries
                        tool_call_details = entry.get("tool_call_details", [])
                        with st.expander(
                            f"🔧 {entry['timestamp']} - {entry['tool_calls']} tool(s) - {entry['response_time']}s"
                        ):
                            st.write(f"**Prompt:** {entry['prompt']}")
                            st.write(f"**Response Time:** {entry['response_time']}s")
                            st.write(f"**Tool Calls Made:** {entry['tool_calls']}")

                            if tool_call_details:
                                st.write("**Tool Call Details:**")
                                for i, tool_call in enumerate(tool_call_details, 1):
                                    # Use standardized format - check for 'name' field first
                                    tool_name = tool_call.get(
                                        "name",
                                        tool_call.get("function_name", "Unknown"),
                                    )
                                    tool_status = tool_call.get("status", "unknown")

                                    # Status indicator
                                    status_icon = (
                                        "✅"
                                        if tool_status == "success"
                                        else "❓" if tool_status == "unknown" else "❌"
                                    )

                                    st.write(f"**Tool {i}:** {status_icon} {tool_name}")

                                    # Show arguments
                                    tool_args = tool_call.get(
                                        "arguments", tool_call.get("function_args", {})
                                    )
                                    if tool_args:
                                        st.write("**Arguments:**")
                                        st.json(tool_args)

                                    # Show result if available
                                    tool_result = tool_call.get(
                                        "result", tool_call.get("content")
                                    )
                                    if tool_result:
                                        st.write("**Result:**")
                                        if (
                                            isinstance(tool_result, str)
                                            and len(tool_result) > 200
                                        ):
                                            st.write(f"{tool_result[:200]}...")
                                        else:
                                            st.write(str(tool_result))

                                    # Show reasoning if available (legacy field)
                                    if tool_call.get("reasoning"):
                                        st.write(
                                            f"**Reasoning:** {tool_call['reasoning']}"
                                        )

                                    if i < len(
                                        tool_call_details
                                    ):  # Add separator between tools
                                        st.markdown("---")
                else:
                    st.info("No tool calls made yet.")
            else:
                st.info("No debug metrics available yet.")

            # REST API (debug-only) moved to sidebar to avoid cluttering pages
            if False and st.session_state.get(SESSION_KEY_SHOW_DEBUG):
                st.subheader("📡 REST API")
                if st.session_state.get("rest_api_server"):
                    st.success("🌐 REST API server running on http://localhost:8001")
                    with st.expander("📡 REST API Endpoints", expanded=False):
                        st.markdown(
                            """
            **Memory Endpoints:**
            - `POST /api/v1/memory/store` - Store text as memory
            - `POST /api/v1/memory/store-url` - Store content from URL as memory
            - `GET /api/v1/memory/search?q=query` - Search memories
            - `GET /api/v1/memory/list` - List all memories
            - `GET /api/v1/memory/stats` - Get memory statistics

            **Knowledge Endpoints:**
            - `POST /api/v1/knowledge/store-text` - Store text in knowledge base
            - `POST /api/v1/knowledge/store-url` - Store content from URL in knowledge base
            - `GET /api/v1/knowledge/search?q=query` - Search knowledge base
            - `GET /api/v1/knowledge/status` - Get knowledge base status

            **System Endpoints:**
            - `GET /api/v1/health` - Health check
            - `GET /api/v1/status` - System status

            **Example Usage:**
            ```bash
            # Store memory
            curl -X POST http://localhost:8001/api/v1/memory/store \\
              -H "Content-Type: application/json" \\
              -d '{"content": "I work at Google", "topics": ["work"]}'

            # Store knowledge from URL
            curl -X POST http://localhost:8001/api/v1/knowledge/store-url \\
              -H "Content-Type: application/json" \\
              -d '{"url": "https://example.com/article", "title": "Important Article"}'
            ```
                        """
                        )
                else:
                    st.warning("⚠️ REST API server failed to start")

        # Show recent request details above system controls to keep power button last
        if st.session_state.get(SESSION_KEY_SHOW_DEBUG):
            st.subheader("🔍 Recent Request Details")
            if st.session_state[SESSION_KEY_DEBUG_METRICS]:
                for entry in reversed(st.session_state[SESSION_KEY_DEBUG_METRICS][-5:]):
                    with st.expander(
                        f"{'✅' if entry['success'] else '❌'} {entry['timestamp']} - {entry['response_time']}s"
                    ):
                        st.write(f"**Prompt:** {entry['prompt']}")
                        st.write(f"**Response Time:** {entry['response_time']}s")
                        st.write(f"**Input Tokens:** {entry['input_tokens']}")
                        st.write(f"**Output Tokens:** {entry['output_tokens']}")
                        st.write(f"**Total Tokens:** {entry['total_tokens']}")
                        st.write(f"**Tool Calls:** {entry['tool_calls']}")
                        st.write(f"**Response Type:** {entry['response_type']}")
                        if not entry["success"]:
                            st.write(
                                f"**Error:** {entry.get('error', 'Unknown error')}"
                            )
            else:
                st.info("No debug metrics available yet.")

        # REST API (debug-only) placed below Recent Request Details
        if st.session_state.get(SESSION_KEY_SHOW_DEBUG):
            st.subheader("📡 REST API")
            if st.session_state.get("rest_api_server"):
                st.success("🌐 REST API server running on http://localhost:8001")
                with st.expander("📡 REST API Endpoints", expanded=False):
                    st.markdown(
                        """
            **Memory Endpoints:**
            - `POST /api/v1/memory/store` - Store text as memory
            - `POST /api/v1/memory/store-url` - Store content from URL as memory
            - `GET /api/v1/memory/search?q=query` - Search memories
            - `GET /api/v1/memory/list` - List all memories
            - `GET /api/v1/memory/stats` - Get memory statistics

            **Knowledge Endpoints:**
            - `POST /api/v1/knowledge/store-text` - Store text in knowledge base
            - `POST /api/v1/knowledge/store-url` - Store content from URL in knowledge base
            - `GET /api/v1/knowledge/search?q=query` - Search knowledge base
            - `GET /api/v1/knowledge/status` - Get knowledge base status

            **System Endpoints:**
            - `GET /api/v1/health` - Health check
            - `GET /api/v1/status` - System status

            **Example Usage:**
            ```bash
            # Store memory
            curl -X POST http://localhost:8001/api/v1/memory/store \\
              -H "Content-Type: application/json" \\
              -d '{"content": "I work at Google", "topics": ["work"]}'

            # Store knowledge from URL
            curl -X POST http://localhost:8001/api/v1/knowledge/store-url \\
              -H "Content-Type: application/json" \\
              -d '{"url": "https://example.com/article", "title": "Important Article"}'
            ```
                    """
                    )
            else:
                st.warning("⚠️ REST API server failed to start")

        # Power off button at the bottom of the sidebar
        st.markdown("---")
        st.header("🚨 System Control")
        if st.button(
            "🔴 Power Off System",
            key="sidebar_power_off_btn",
            type="primary",
            use_container_width=True,
        ):
            # Show confirmation dialog
            st.session_state["show_power_off_confirmation"] = True
            st.rerun()


def render_knowledge_tab():
    """Render the knowledge base management tab interface."""
    st.markdown("### Knowledge Base Search & Management")
    knowledge_helper = st.session_state[SESSION_KEY_KNOWLEDGE_HELPER]
    render_knowledge_status(knowledge_helper)

    # File Upload Section
    st.markdown("---")
    st.subheader("📁 Add Knowledge Files")
    st.markdown("*Upload files directly to your knowledge base*")

    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files to add to your knowledge base",
        accept_multiple_files=True,
        type=["txt", "md", "pdf", "docx", "doc", "html", "csv", "json"],
        key="knowledge_file_uploader",
    )

    if uploaded_files:
        st.write(f"Selected {len(uploaded_files)} file(s):")
        for file in uploaded_files:
            st.write(f"- {file.name} ({file.size} bytes)")

        if st.button(
            "🚀 Upload and Process Files", key="upload_files_btn", type="primary"
        ):
            progress_bar = st.progress(0)
            status_text = st.empty()
            results = []

            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name}...")

                try:
                    # Save uploaded file temporarily
                    import os
                    import tempfile

                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=f"_{uploaded_file.name}"
                    ) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name

                    try:
                        # Get the appropriate agent/team based on current mode
                        current_mode = st.session_state.get(
                            SESSION_KEY_AGENT_MODE, "single"
                        )

                        if current_mode == "team":
                            # Team mode - get the knowledge agent (first team member)
                            team = st.session_state.get(SESSION_KEY_TEAM)
                            if team and hasattr(team, "members") and team.members:
                                agent = team.members[
                                    0
                                ]  # First member is the knowledge agent
                            else:
                                results.append(
                                    f"**{uploaded_file.name}**: ❌ Team not properly initialized"
                                )
                                continue
                        else:
                            # Single agent mode
                            agent = st.session_state.get(SESSION_KEY_AGENT)
                            if not agent:
                                results.append(
                                    f"**{uploaded_file.name}**: ❌ Agent not initialized"
                                )
                                continue

                        # Use the knowledge ingestion tools from the agent
                        if hasattr(agent, "agent") and hasattr(agent.agent, "tools"):
                            # Find the knowledge tools (consolidated)
                            knowledge_tools = None
                            for tool in agent.agent.tools:
                                if hasattr(
                                    tool, "__class__"
                                ) and "KnowledgeTools" in str(tool.__class__):
                                    knowledge_tools = tool
                                    break

                            if knowledge_tools:
                                # Use the ingest_knowledge_file method
                                result = knowledge_tools.ingest_knowledge_file(
                                    file_path=tmp_file_path, title=uploaded_file.name
                                )
                                results.append(f"**{uploaded_file.name}**: {result}")
                            else:
                                results.append(
                                    f"**{uploaded_file.name}**: ❌ Knowledge tools not available"
                                )
                        else:
                            results.append(
                                f"**{uploaded_file.name}**: ❌ Agent tools not accessible"
                            )

                    finally:
                        # Clean up temporary file
                        try:
                            os.unlink(tmp_file_path)
                        except OSError:
                            pass

                except Exception as e:
                    results.append(f"**{uploaded_file.name}**: ❌ Error: {str(e)}")

                # Update progress
                progress_bar.progress((i + 1) / len(uploaded_files))

            # Show results
            status_text.text("Upload complete!")
            st.markdown("### Upload Results:")
            for result in results:
                st.markdown(result)

            # Clear the file uploader
            st.rerun()

    # Text Input Section
    st.markdown("---")
    st.subheader("📝 Add Text Knowledge")
    st.markdown("*Add text content directly to your knowledge base*")

    # Clear-on-success using a flag to avoid Streamlit key mutation errors
    if st.session_state.get("clear_knowledge_input_text", False):
        st.session_state["knowledge_title"] = ""
        st.session_state["knowledge_content"] = ""
        st.session_state["clear_knowledge_input_text"] = False

    col1, col2 = st.columns([3, 1])
    with col1:
        knowledge_title = st.text_input(
            "Title for your knowledge entry:", key="knowledge_title"
        )
    with col2:
        file_type = st.selectbox(
            "Format:", ["txt", "md", "html", "json"], key="knowledge_format"
        )

    knowledge_content = st.text_area(
        "Enter your knowledge content:",
        height=200,
        key="knowledge_content",
        placeholder="Enter the text content you want to add to your knowledge base...",
    )

    if st.button("💾 Save Text Knowledge", key="save_text_knowledge", type="primary"):
        if knowledge_title and knowledge_content:
            try:
                # Get the appropriate agent/team based on current mode
                current_mode = st.session_state.get(SESSION_KEY_AGENT_MODE, "single")

                if current_mode == "team":
                    # Team mode - get the knowledge agent (first team member)
                    team = st.session_state.get(SESSION_KEY_TEAM)
                    if team and hasattr(team, "members") and team.members:
                        agent = team.members[0]  # First member is the knowledge agent
                    else:
                        st.error("❌ Team not properly initialized")
                        return
                else:
                    # Single agent mode
                    agent = st.session_state.get(SESSION_KEY_AGENT)
                    if not agent:
                        st.error("❌ Agent not initialized")
                        return

                # Use the knowledge ingestion tools from the agent
                if hasattr(agent, "agent") and hasattr(agent.agent, "tools"):
                    # Find the knowledge tools (consolidated)
                    knowledge_tools = None
                    for tool in agent.agent.tools:
                        if hasattr(tool, "__class__") and "KnowledgeTools" in str(
                            tool.__class__
                        ):
                            knowledge_tools = tool
                            break

                    if knowledge_tools:
                        # Use the ingest_knowledge_text method
                        result = knowledge_tools.ingest_knowledge_text(
                            content=knowledge_content,
                            title=knowledge_title,
                            file_type=file_type,
                        )
                        # Show success notification
                        st.toast("🎉 Knowledge saved successfully!", icon="✅")
                        time.sleep(2.0)  # 2 second delay

                        # Clear the form using flag-based approach
                        st.session_state["clear_knowledge_input_text"] = True
                        st.rerun()
                    else:
                        st.error("❌ Knowledge tools not available")
                else:
                    st.error("❌ Agent tools not accessible")
            except Exception as e:
                st.error(f"❌ Error saving knowledge: {str(e)}")
        else:
            st.warning("⚠️ Please provide both title and content")

    # URL Input Section
    st.markdown("---")
    st.subheader("🌐 Add Knowledge from URL")
    st.markdown("*Extract and add content from web pages*")

    # Clear-on-success using a flag to avoid Streamlit key mutation errors
    if st.session_state.get("clear_url_input_text", False):
        st.session_state["knowledge_url"] = ""
        st.session_state["url_title"] = ""
        st.session_state["clear_url_input_text"] = False

    col1, col2 = st.columns([3, 1])
    with col1:
        knowledge_url = st.text_input(
            "URL to extract content from:", key="knowledge_url"
        )
    with col2:
        url_title = st.text_input("Title (optional):", key="url_title")

    if st.button(
        "🌐 Extract and Save from URL", key="save_url_knowledge", type="primary"
    ):
        if knowledge_url:
            try:
                with st.spinner("Extracting content from URL..."):
                    # Get the appropriate agent/team based on current mode
                    current_mode = st.session_state.get(
                        SESSION_KEY_AGENT_MODE, "single"
                    )

                    if current_mode == "team":
                        # Team mode - get the knowledge agent (first team member)
                        team = st.session_state.get(SESSION_KEY_TEAM)
                        if team and hasattr(team, "members") and team.members:
                            agent = team.members[
                                0
                            ]  # First member is the knowledge agent
                        else:
                            st.error("❌ Team not properly initialized")
                            return
                    else:
                        # Single agent mode
                        agent = st.session_state.get(SESSION_KEY_AGENT)
                        if not agent:
                            st.error("❌ Agent not initialized")
                            return

                    # Use the knowledge ingestion tools from the agent
                    if hasattr(agent, "agent") and hasattr(agent.agent, "tools"):
                        # Find the knowledge tools (consolidated)
                        knowledge_tools = None
                        for tool in agent.agent.tools:
                            if hasattr(tool, "__class__") and "KnowledgeTools" in str(
                                tool.__class__
                            ):
                                knowledge_tools = tool
                                break

                        if knowledge_tools:
                            # Use the ingest_knowledge_from_url method
                            result = knowledge_tools.ingest_knowledge_from_url(
                                url=knowledge_url,
                                title=url_title if url_title else None,
                            )
                            # Show success notification
                            st.toast(
                                "🎉 Knowledge from URL saved successfully!", icon="✅"
                            )
                            time.sleep(2.0)  # 2 second delay

                            # Clear the form using flag-based approach
                            st.session_state["clear_url_input_text"] = True
                            st.rerun()
                        else:
                            st.error("❌ Knowledge tools not available")
                    else:
                        st.error("❌ Agent tools not accessible")
            except Exception as e:
                st.error(f"❌ Error extracting from URL: {str(e)}")
        else:
            st.warning("⚠️ Please provide a URL")

    # SQLite/LanceDB Knowledge Search Section
    st.markdown("---")
    st.subheader("🔍 SQLite/LanceDB Knowledge Search")
    st.markdown(
        "*Search through stored knowledge using the original sqlite and lancedb knowledge sources*"
    )
    knowledge_search_limit = st.number_input(
        "Max Results", 1, 50, 10, key="knowledge_search_limit"
    )
    with st.form("knowledge_sqlite_search_form"):
        knowledge_search_query = st.text_input(
            "Enter keywords to search the SQLite/LanceDB knowledge base",
            key="knowledge_search_query_text",
        )
        submitted_knowledge_sqlite = st.form_submit_button("🔎 Search")
    if (
        submitted_knowledge_sqlite
        and knowledge_search_query
        and knowledge_search_query.strip()
    ):
        search_results = knowledge_helper.search_knowledge(
            query=knowledge_search_query.strip(), limit=knowledge_search_limit
        )
        if search_results:
            st.subheader(
                f"🔍 SQLite/LanceDB Knowledge Search Results for: '{knowledge_search_query.strip()}'"
            )
            for i, knowledge_entry in enumerate(search_results, 1):
                if hasattr(knowledge_entry, "content"):
                    content = knowledge_entry.content
                    title = getattr(knowledge_entry, "title", "Untitled")
                    source = getattr(knowledge_entry, "source", "Unknown")
                    knowledge_id = getattr(knowledge_entry, "id", "N/A")
                elif isinstance(knowledge_entry, dict):
                    content = knowledge_entry.get("content", "No content")
                    title = knowledge_entry.get("title", "Untitled")
                    source = knowledge_entry.get("source", "Unknown")
                    knowledge_id = knowledge_entry.get("id", "N/A")
                else:
                    content = str(knowledge_entry)
                    title = "Untitled"
                    source = "Unknown"
                    knowledge_id = "N/A"

                with st.expander(
                    f"📚 Result {i}: {title if title != 'Untitled' else content[:50]}..."
                ):
                    st.write(f"**Title:** {title}")
                    st.write(f"**Content:** {content}")
                    st.write(f"**Source:** {source}")
                    st.write(f"**Knowledge ID:** {knowledge_id}")
        else:
            st.info("No matching knowledge found.")

    # RAG Knowledge Search Section
    st.markdown("---")
    st.subheader("🤖 RAG Knowledge Search")
    st.markdown(
        "*Search through knowledge using direct RAG query with advanced options*"
    )

    # Create a dictionary to hold the query parameters
    query_params = {}

    # Query mode
    query_params["mode"] = st.selectbox(
        "Select RAG Search Type:",
        ("naive", "hybrid", "local", "global"),
        key="rag_search_type",
    )

    # Response type
    query_params["response_type"] = st.text_input(
        "Response Format:",
        "Multiple Paragraphs",
        key="rag_response_type",
        help="Examples: 'Single Paragraph', 'Bullet Points', 'JSON'",
    )

    # Top K
    query_params["top_k"] = st.slider(
        "Top K:",
        min_value=1,
        max_value=100,
        value=10,
        key="rag_top_k",
        help="Number of items to retrieve",
    )

    # Other boolean flags
    col1, col2, col3 = st.columns(3)
    with col1:
        query_params["only_need_context"] = st.checkbox(
            "Context Only", key="rag_context_only"
        )
    with col2:
        query_params["only_need_prompt"] = st.checkbox(
            "Prompt Only", key="rag_prompt_only"
        )
    with col3:
        query_params["stream"] = st.checkbox("Stream", key="rag_stream")

    with st.form("rag_search_form"):
        rag_search_query = st.text_input(
            "Enter keywords to search the RAG knowledge base",
            key="rag_search_query_text",
        )
        submitted_rag_search = st.form_submit_button("🔎 Search RAG")
    if submitted_rag_search and rag_search_query and rag_search_query.strip():
        # Pass the entire dictionary of parameters to the helper
        search_results = knowledge_helper.search_rag(
            query=rag_search_query.strip(), params=query_params
        )
        # Check if we have actual content (not just empty string or None)
        if search_results is not None and str(search_results).strip():
            st.subheader(
                f"🤖 RAG Knowledge Search Results for: '{rag_search_query.strip()}'"
            )
            st.markdown(search_results)
        elif search_results is not None:
            st.warning(f"Query returned empty response. Raw result: '{search_results}'")
        else:
            st.info("No matching knowledge found.")
