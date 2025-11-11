"""
Memory Management Component

Provides interface for:
- Viewing memories
- Searching memories
- Managing memory storage
- Syncing memories between systems
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import project modules
from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.streamlit.utils.agent_utils import get_agent_instance
from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper


def memory_management_tab():
    """Render the memory management tab."""
    st.title("Memory Management")

    # Show agent status
    _render_agent_status()

    # Create tabs for different memory management functions
    tabs = st.tabs(["Memory Explorer", "Search", "Sync & Backup", "Settings"])

    with tabs[0]:
        _render_memory_explorer()

    with tabs[1]:
        _render_memory_search()

    with tabs[2]:
        _render_memory_sync()

    with tabs[3]:
        _render_memory_settings()


def _render_agent_status():
    """Display agent initialization status."""
    try:
        from personal_agent.streamlit.utils.agent_utils import (
            check_agent_status,
            get_agent_instance,
        )

        agent = get_agent_instance()
        status = check_agent_status(agent)

        col1, col2, col3 = st.columns(3)

        with col1:
            if status["initialized"]:
                st.success("🤖 Agent: Initialized")
            else:
                st.error("🤖 Agent: Not Initialized")
                if "error" in status:
                    st.caption(f"Error: {status['error']}")

        with col2:
            if status["memory_available"]:
                st.success("💾 Memory: Available")
            else:
                st.warning("💾 Memory: Not Available")

        with col3:
            if status.get("user_id"):
                st.info(f"👤 User: {status['user_id']}")
            else:
                st.warning("👤 User: Unknown")

        # Show additional details in an expander
        with st.expander("Agent Details"):
            st.json(status)

    except Exception as e:
        st.error(f"Error checking agent status: {str(e)}")


def _render_memory_explorer():
    """Display and manage memories using StreamlitMemoryHelper directly."""
    st.subheader("Memory Explorer")

    # Get memory helper
    agent = get_agent_instance()
    if not agent:
        st.error("Agent not available")
        return

    memory_helper = StreamlitMemoryHelper(agent)

    # Filters
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

            if memory_dates:
                default_start_date = min(memory_dates)
                default_end_date = max(memory_dates)
            else:
                # Fallback to last 5 days if no memories have dates
                default_start_date = datetime.now().date() - timedelta(days=5)
                default_end_date = datetime.now().date()

        except Exception:
            # Fallback to last 5 days if there's an error
            default_start_date = datetime.now().date() - timedelta(days=5)
            default_end_date = datetime.now().date()

        date_range = st.date_input(
            "Date Range",
            value=[default_start_date, default_end_date],
            help="Filter memories by date range (automatically set to encompass all memory dates)",
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

    # Get all memories using the helper
    try:
        raw_memories = memory_helper.get_all_memories()

        # Apply filters
        filtered_memories = raw_memories

        # Filter by date range if specified
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
            # Display memory count
            st.caption(
                f"Displaying {len(filtered_memories)} of {len(raw_memories)} total memories"
            )

            # Display memories in single line format with trashcan icon
            for i, memory in enumerate(filtered_memories):
                memory_id = getattr(memory, "memory_id", f"mem_{i}")
                memory_content = getattr(memory, "memory", str(memory))
                last_updated = getattr(memory, "last_updated", "N/A")
                topics = getattr(memory, "topics", [])

                # Enhanced fields
                confidence = getattr(memory, "confidence", 1.0)
                is_proxy = getattr(memory, "is_proxy", False)
                proxy_agent = getattr(memory, "proxy_agent", None)

                # Create a container for each memory row
                with st.container():
                    col1, col2, col3 = st.columns([8, 1, 1])

                    with col1:
                        # Build display string with enhanced fields
                        topics_str = f" | Topics: {', '.join(topics)}" if topics else ""

                        # Add confidence indicator (only if not 1.0)
                        if confidence < 1.0:
                            conf_emoji = (
                                "🟡"
                                if confidence >= 0.7
                                else "🟠" if confidence >= 0.4 else "🔴"
                            )
                            confidence_str = f" | {conf_emoji} {int(confidence * 100)}%"
                        else:
                            confidence_str = ""

                        # Add proxy indicator
                        proxy_str = (
                            f" | 🤖 {proxy_agent}"
                            if is_proxy and proxy_agent
                            else " | 🤖 Proxy" if is_proxy else ""
                        )

                        st.write(
                            f"**{memory_id}:** {memory_content[:100]}{'...' if len(memory_content) > 100 else ''} | Updated: {last_updated}{topics_str}{confidence_str}{proxy_str}"
                        )

                    with col2:
                        # Trashcan icon button
                        if st.button(
                            "🗑️", key=f"trash_{memory_id}", help="Delete Memory"
                        ):
                            st.session_state[f"show_delete_confirm_{memory_id}"] = True

                    with col3:
                        # Export button with enhanced fields
                        export_data = json.dumps(
                            {
                                "id": memory_id,
                                "content": memory_content,
                                "last_updated": str(last_updated),
                                "topics": topics,
                                "confidence": confidence,
                                "is_proxy": is_proxy,
                                "proxy_agent": proxy_agent,
                            },
                            indent=2,
                        )
                        st.download_button(
                            label="📥",
                            data=export_data,
                            file_name=f"memory_{memory_id}.json",
                            mime="application/json",
                            key=f"export_{memory_id}",
                            help="Export Memory",
                        )

                    # Show confirmation dropdown if trashcan was clicked
                    if st.session_state.get(f"show_delete_confirm_{memory_id}", False):
                        with st.expander("⚠️ Confirm Deletion", expanded=True):
                            st.warning(
                                f"Are you sure you want to delete memory: **{memory_id}**?"
                            )
                            st.write(
                                f"Content: {memory_content[:200]}{'...' if len(memory_content) > 200 else ''}"
                            )

                            col_confirm1, col_confirm2 = st.columns([3, 1])

                            with col_confirm1:
                                confirmation_text = st.text_input(
                                    "Type 'yes' to confirm deletion:",
                                    key=f"confirm_text_{memory_id}",
                                    placeholder="yes",
                                )

                            with col_confirm2:
                                if st.button(
                                    "Delete",
                                    key=f"confirm_delete_{memory_id}",
                                    type="primary",
                                ):
                                    if confirmation_text.lower() == "yes":
                                        # Show toast notification with 2-second delay
                                        st.toast(
                                            f"Deleting memory {memory_id}...", icon="🗑️"
                                        )
                                        time.sleep(2)

                                        with st.spinner("Deleting memory..."):
                                            success, message = (
                                                memory_helper.delete_memory(memory_id)
                                            )

                                            # Store deletion status in session state for 5-second display
                                            st.session_state[
                                                f"deletion_status_{memory_id}"
                                            ] = {
                                                "success": success,
                                                "message": message,
                                                "timestamp": time.time(),
                                            }

                                            # Clear confirmation state
                                            st.session_state[
                                                f"show_delete_confirm_{memory_id}"
                                            ] = False

                                            if success:
                                                st.toast(
                                                    "Memory deleted successfully!",
                                                    icon="✅",
                                                )
                                                # Clear the agent cache to ensure fresh data on next load
                                                st.cache_resource.clear()
                                                st.rerun()
                                            else:
                                                st.toast(
                                                    f"Failed to delete memory: {message}",
                                                    icon="❌",
                                                )
                                    else:
                                        st.error(
                                            "Please type 'yes' to confirm deletion"
                                        )

                                # Cancel button
                                if st.button(
                                    "Cancel", key=f"cancel_delete_{memory_id}"
                                ):
                                    st.session_state[
                                        f"show_delete_confirm_{memory_id}"
                                    ] = False
                                    st.rerun()

                    # Show deletion status for 5 seconds
                    deletion_status = st.session_state.get(
                        f"deletion_status_{memory_id}"
                    )
                    if deletion_status:
                        current_time = time.time()
                        if current_time - deletion_status["timestamp"] < 5:
                            if deletion_status["success"]:
                                st.success(f"✅ {deletion_status['message']}")
                            else:
                                st.error(f"❌ {deletion_status['message']}")
                        else:
                            # Clear status after 5 seconds
                            del st.session_state[f"deletion_status_{memory_id}"]

                    st.divider()
        else:
            st.info("No memories found.")

    except Exception as e:
        st.error(f"Error loading memories: {str(e)}")


def _render_memory_search():
    """Search through memories using StreamlitMemoryHelper directly."""
    st.subheader("Memory Search")

    # Get memory helper
    agent = get_agent_instance()
    if not agent:
        st.error("Agent not available")
        return

    memory_helper = StreamlitMemoryHelper(agent)

    # Search form
    with st.form("memory_search_form"):
        query = st.text_input(
            "Search Query", help="Enter keywords or phrases to search for in memories"
        )

        col1, col2 = st.columns(2)

        with col1:
            similarity_threshold = st.slider(
                "Similarity Threshold",
                0.1,
                1.0,
                0.3,
                0.1,
                help="Minimum similarity score for results",
            )

        with col2:
            max_results = st.number_input(
                "Max Results",
                min_value=5,
                max_value=100,
                value=20,
                step=5,
                help="Maximum number of results to return",
            )

        submitted = st.form_submit_button("Search")

        if submitted and query:
            try:
                # Search memories using the helper
                search_results = memory_helper.search_memories(
                    query=query,
                    limit=max_results,
                    similarity_threshold=similarity_threshold,
                )

                if search_results:
                    st.caption(f"Found {len(search_results)} matching memories")

                    # Display search results
                    for i, (memory, score) in enumerate(search_results, 1):
                        # Get enhanced fields
                        confidence = getattr(memory, "confidence", 1.0)
                        is_proxy = getattr(memory, "is_proxy", False)
                        proxy_agent = getattr(memory, "proxy_agent", None)

                        # Build title with confidence and proxy indicators
                        conf_indicator = (
                            f" | {int(confidence * 100)}% conf"
                            if confidence < 1.0
                            else ""
                        )
                        proxy_indicator = (
                            f" | 🤖 {proxy_agent}"
                            if is_proxy and proxy_agent
                            else " | 🤖 Proxy" if is_proxy else ""
                        )

                        with st.expander(
                            f"Result {i} (Score: {score:.3f}): {memory.memory[:50]}...{conf_indicator}{proxy_indicator}"
                        ):
                            st.write(f"**Memory:** {memory.memory}")
                            st.write(f"**Similarity Score:** {score:.3f}")
                            st.write(f"**Confidence:** {int(confidence * 100)}%")
                            if is_proxy:
                                st.write(
                                    f"**🤖 Proxy Memory** (Agent: {proxy_agent or 'Unknown'})"
                                )
                            topics = getattr(memory, "topics", [])
                            if topics:
                                st.write(f"**Topics:** {', '.join(topics)}")
                            st.write(
                                f"**Last Updated:** {getattr(memory, 'last_updated', 'N/A')}"
                            )
                            st.write(
                                f"**Memory ID:** {getattr(memory, 'memory_id', 'N/A')}"
                            )

                            # Delete button for search results
                            if st.button(
                                f"🗑️ Delete Memory",
                                key=f"delete_search_{memory.memory_id}",
                            ):
                                # Show toast notification with 2-second delay
                                st.toast(
                                    f"Deleting memory {memory.memory_id}...", icon="🗑️"
                                )
                                time.sleep(2)

                                success, message = memory_helper.delete_memory(
                                    memory.memory_id
                                )
                                if success:
                                    st.toast("Memory deleted successfully!", icon="✅")
                                    st.success(f"Memory deleted: {message}")
                                    st.rerun()
                                else:
                                    st.toast(
                                        f"Failed to delete memory: {message}", icon="❌"
                                    )
                                    st.error(f"Failed to delete memory: {message}")
                else:
                    st.info("No memories found matching your search.")

            except Exception as e:
                st.error(f"Error searching memories: {str(e)}")


def _render_memory_sync():
    """Sync and backup memories using StreamlitMemoryHelper directly."""
    st.subheader("Sync & Backup")

    # Get memory helper
    agent = get_agent_instance()
    if not agent:
        st.error("Agent not available")
        return

    memory_helper = StreamlitMemoryHelper(agent)

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Memory Sync")
        st.write("Synchronize memories between SQLite and LightRAG graph systems.")

        if st.button("🔍 Check Sync Status"):
            try:
                sync_status = memory_helper.get_memory_sync_status()
                if "error" not in sync_status:
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric(
                            "Local Memories", sync_status.get("local_memory_count", 0)
                        )
                    with col_b:
                        st.metric(
                            "Graph Entities", sync_status.get("graph_entity_count", 0)
                        )
                    with col_c:
                        sync_ratio = sync_status.get("sync_ratio", 0)
                        st.metric("Sync Ratio", f"{sync_ratio:.2f}")

                    status = sync_status.get("status", "unknown")
                    if status == "synced":
                        st.success(
                            "✅ Memories are synchronized between local and graph systems"
                        )
                    elif status == "out_of_sync":
                        st.warning("⚠️ Memories may be out of sync between systems")
                    else:
                        st.error(f"❌ Sync status unknown: {status}")
                else:
                    st.error(
                        f"Error checking sync status: {sync_status.get('error', 'Unknown error')}"
                    )
            except Exception as e:
                st.error(f"Error checking sync status: {str(e)}")

        if st.button("🔄 Sync Missing Memories"):
            try:
                with st.spinner("Syncing memories..."):
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
                            st.warning(f"Error syncing memory: {e}")

                    if synced_count > 0:
                        # Show success notification
                        st.toast(
                            f"🎉 Synced {synced_count} memories to graph system!",
                            icon="✅",
                        )
                        time.sleep(2.0)  # 2 second delay
                        st.rerun()
                    else:
                        st.info("No memories needed syncing")
            except Exception as e:
                st.error(f"Error during memory sync: {str(e)}")

    with col2:
        st.write("### Export/Import")

        # Export section
        st.write("#### Export Memories")
        export_type = st.selectbox(
            "Export Format", ["JSON", "CSV"], help="Format to export memories in"
        )

        if st.button("Export All Memories"):
            try:
                # Get all memories and export them
                all_memories = memory_helper.get_all_memories()
                export_content = ""
                mime_type = "text/plain"

                if export_type == "JSON":
                    # Export as JSON
                    export_data = []
                    for memory in all_memories:
                        export_data.append(
                            {
                                "id": getattr(memory, "memory_id", "unknown"),
                                "content": getattr(memory, "memory", str(memory)),
                                "last_updated": str(
                                    getattr(memory, "last_updated", "N/A")
                                ),
                                "topics": getattr(memory, "topics", []),
                            }
                        )

                    export_content = json.dumps(export_data, indent=2)
                    mime_type = "application/json"

                elif export_type == "CSV":
                    # Export as CSV
                    import csv
                    import io

                    output = io.StringIO()
                    writer = csv.writer(output)

                    # Write header
                    writer.writerow(["id", "content", "last_updated", "topics"])

                    # Write rows
                    for memory in all_memories:
                        writer.writerow(
                            [
                                getattr(memory, "memory_id", "unknown"),
                                getattr(memory, "memory", str(memory)),
                                str(getattr(memory, "last_updated", "N/A")),
                                ", ".join(getattr(memory, "topics", [])),
                            ]
                        )

                    export_content = output.getvalue()
                    mime_type = "text/csv"

                if export_content:
                    st.download_button(
                        label=f"Download {export_type} File",
                        data=export_content,
                        file_name=f"memories_export_{datetime.now().strftime('%Y%m%d')}.{export_type.lower()}",
                        mime=mime_type,
                    )
                else:
                    st.warning("No data to export")

            except Exception as e:
                st.error(f"Error exporting memories: {str(e)}")

        # Import section
        st.write("#### Import Memories")
        uploaded_file = st.file_uploader(
            "Choose a file to import", type=["json", "csv"]
        )

        if uploaded_file is not None:
            if st.button("Import Memories"):
                try:
                    file_content = uploaded_file.getvalue().decode("utf-8")
                    imported_count = 0

                    if uploaded_file.name.endswith(".json"):
                        # Import from JSON
                        memories = json.loads(file_content)
                        for memory_data in memories:
                            try:
                                content_text = memory_data.get("content", "")
                                topics = memory_data.get("topics", [])
                                if isinstance(topics, str):
                                    topics = [
                                        t.strip()
                                        for t in topics.split(",")
                                        if t.strip()
                                    ]

                                success, message, memory_id, _ = (
                                    memory_helper.add_memory(
                                        memory_text=content_text,
                                        topics=topics,
                                        input_text="Imported memory",
                                    )
                                )

                                if success:
                                    imported_count += 1

                            except Exception as e:
                                st.warning(f"Error importing memory: {e}")

                    elif uploaded_file.name.endswith(".csv"):
                        # Import from CSV
                        import csv
                        import io

                        reader = csv.DictReader(io.StringIO(file_content))
                        for row in reader:
                            try:
                                content_text = row.get("content", "")
                                topics_str = row.get("topics", "")
                                topics = [
                                    t.strip()
                                    for t in topics_str.split(",")
                                    if t.strip()
                                ]

                                success, message, memory_id, _ = (
                                    memory_helper.add_memory(
                                        memory_text=content_text,
                                        topics=topics,
                                        input_text="Imported memory",
                                    )
                                )

                                if success:
                                    imported_count += 1

                            except Exception as e:
                                st.warning(f"Error importing memory: {e}")

                    if imported_count > 0:
                        # Show success notification
                        st.toast(
                            f"🎉 Successfully imported {imported_count} memories!",
                            icon="✅",
                        )
                        time.sleep(2.0)  # 2 second delay
                        st.rerun()
                    else:
                        st.warning("No memories were imported.")

                except Exception as e:
                    st.error(f"Error importing memories: {str(e)}")


def _render_memory_settings():
    """Memory system settings."""
    st.subheader("Memory Settings")

    # Clear all memories section
    st.write("### Dangerous Actions")
    st.warning("⚠️ **Warning:** The following actions are irreversible!")

    # Get memory helper
    agent = get_agent_instance()
    if not agent:
        st.error("Agent not available")
        return

    memory_helper = StreamlitMemoryHelper(agent)

    # Clear all memories button
    if st.button(
        "🗑️ Clear All Memories",
        type="primary",
        help="Delete all memories from local SQLite and LightRAG graph",
    ):
        st.session_state["show_clear_all_confirmation"] = True

    # Show confirmation dialog if button was clicked
    if st.session_state.get("show_clear_all_confirmation", False):
        with st.expander("⚠️ Confirm Clear All Memories", expanded=True):
            st.error(
                "**This will permanently delete ALL memories from both local and graph storage!**"
            )
            st.write(
                "This action cannot be undone. All user memories will be permanently removed."
            )

            col_confirm1, col_confirm2 = st.columns([3, 1])

            with col_confirm1:
                confirmation_text = st.text_input(
                    "Type 'DELETE ALL' to confirm:",
                    key="confirm_clear_all_text",
                    placeholder="DELETE ALL",
                )

            with col_confirm2:
                if st.button("Clear All", key="confirm_clear_all", type="primary"):
                    if confirmation_text == "DELETE ALL":
                        st.toast("Clearing all memories...", icon="🗑️")
                        time.sleep(2)

                        with st.spinner(
                            "Deleting all memories from local and graph storage..."
                        ):
                            success, message = memory_helper.clear_memories()

                            # Clear confirmation state
                            st.session_state["show_clear_all_confirmation"] = False

                            if success:
                                st.toast(
                                    "All memories cleared successfully!", icon="✅"
                                )
                                # Clear the agent cache to ensure fresh data on next load
                                st.cache_resource.clear()
                                st.success(message)
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.toast(
                                    f"Failed to clear memories: {message}", icon="❌"
                                )
                                st.error(message)
                    else:
                        st.error("Please type 'DELETE ALL' to confirm")

                # Cancel button
                if st.button("Cancel", key="cancel_clear_all"):
                    st.session_state["show_clear_all_confirmation"] = False
                    st.rerun()
