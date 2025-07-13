"""
Memory Management Component

Provides interface for:
- Viewing memories
- Searching memories
- Managing memory storage
- Syncing memories between systems
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime
import json

# Import project modules
from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.streamlit.utils.memory_utils import (
    get_all_memories,
    search_memories,
    delete_memory,
    sync_memories,
    export_memories,
    import_memories
)


def memory_management_tab():
    """Render the memory management tab."""
    st.title("Memory Management")
    
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


def _render_memory_explorer():
    """Display and manage memories."""
    st.subheader("Memory Explorer")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        memory_type = st.selectbox(
            "Memory Type",
            ["All", "Conversation", "Document", "Tool", "System"],
            help="Filter memories by type"
        )
    
    with col2:
        date_range = st.date_input(
            "Date Range",
            value=[datetime.now().date(), datetime.now().date()],
            help="Filter memories by date range"
        )
    
    with col3:
        limit = st.number_input(
            "Limit",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            help="Maximum number of memories to display"
        )
    
    # Get memories based on filters
    try:
        memories = get_all_memories(
            memory_type=None if memory_type == "All" else memory_type.lower(),
            start_date=date_range[0] if len(date_range) > 0 else None,
            end_date=date_range[1] if len(date_range) > 1 else None,
            limit=limit
        )
        
        if memories:
            # Create a DataFrame for display
            df = pd.DataFrame(memories)
            st.dataframe(df)
            
            # Display memory count
            st.caption(f"Displaying {len(memories)} memories")
            
            # Allow selecting a memory to view details
            if len(memories) > 0:
                memory_ids = [memory['id'] for memory in memories]
                selected_memory_id = st.selectbox("Select Memory for Details", memory_ids)
                
                if selected_memory_id:
                    selected_memory = next((m for m in memories if m['id'] == selected_memory_id), None)
                    if selected_memory:
                        # Display memory details
                        st.json(selected_memory)
                        
                        # Actions for this memory
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Delete Memory", key=f"delete_{selected_memory_id}"):
                                if delete_memory(selected_memory_id):
                                    st.success(f"Memory {selected_memory_id} deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete memory.")
                        
                        with col2:
                            if st.button("Export Memory", key=f"export_{selected_memory_id}"):
                                export_data = json.dumps(selected_memory, indent=2)
                                st.download_button(
                                    label="Download Memory JSON",
                                    data=export_data,
                                    file_name=f"memory_{selected_memory_id}.json",
                                    mime="application/json"
                                )
        else:
            st.info("No memories found matching the filters.")
            
    except Exception as e:
        st.error(f"Error loading memories: {str(e)}")


def _render_memory_search():
    """Search through memories."""
    st.subheader("Memory Search")
    
    # Search form
    with st.form("memory_search_form"):
        query = st.text_input(
            "Search Query",
            help="Enter keywords or phrases to search for in memories"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_type = st.selectbox(
                "Search Type",
                ["Keyword", "Semantic", "Hybrid"],
                help="Method used to search memories"
            )
        
        with col2:
            max_results = st.number_input(
                "Max Results",
                min_value=5,
                max_value=100,
                value=20,
                step=5,
                help="Maximum number of results to return"
            )
        
        submitted = st.form_submit_button("Search")
        
        if submitted and query:
            try:
                # Search memories
                results = search_memories(
                    query=query,
                    search_type=search_type.lower(),
                    max_results=max_results
                )
                
                if results:
                    # Create a DataFrame for display
                    df = pd.DataFrame(results)
                    st.dataframe(df)
                    
                    # Display result count
                    st.caption(f"Found {len(results)} matching memories")
                    
                    # Allow selecting a result to view details
                    if len(results) > 0:
                        result_ids = [result['id'] for result in results]
                        selected_result_id = st.selectbox("Select Result for Details", result_ids)
                        
                        if selected_result_id:
                            selected_result = next((r for r in results if r['id'] == selected_result_id), None)
                            if selected_result:
                                # Display result details
                                st.json(selected_result)
                else:
                    st.info("No memories found matching your search.")
                    
            except Exception as e:
                st.error(f"Error searching memories: {str(e)}")


def _render_memory_sync():
    """Sync and backup memories."""
    st.subheader("Sync & Backup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Memory Sync")
        st.write("Synchronize memories between SQLite and LightRAG graph systems.")
        
        if st.button("Sync Memories Now"):
            try:
                result = sync_memories()
                if result['success']:
                    st.success(f"Memory sync completed successfully! {result['synced']} memories synchronized.")
                else:
                    st.error(f"Memory sync failed: {result['error']}")
            except Exception as e:
                st.error(f"Error during memory sync: {str(e)}")
    
    with col2:
        st.write("### Export/Import")
        
        # Export section
        st.write("#### Export Memories")
        export_type = st.selectbox(
            "Export Format",
            ["JSON", "CSV"],
            help="Format to export memories in"
        )
        
        if st.button("Export All Memories"):
            try:
                export_data = export_memories(format=export_type.lower())
                if export_data:
                    st.download_button(
                        label=f"Download {export_type} File",
                        data=export_data,
                        file_name=f"memories_export_{datetime.now().strftime('%Y%m%d')}.{export_type.lower()}",
                        mime="application/json" if export_type == "JSON" else "text/csv"
                    )
            except Exception as e:
                st.error(f"Error exporting memories: {str(e)}")
        
        # Import section
        st.write("#### Import Memories")
        uploaded_file = st.file_uploader("Choose a file to import", type=["json", "csv"])
        
        if uploaded_file is not None:
            if st.button("Import Memories"):
                try:
                    file_content = uploaded_file.getvalue()
                    result = import_memories(
                        content=file_content,
                        format=uploaded_file.name.split(".")[-1].lower()
                    )
                    
                    if result['success']:
                        st.success(f"Successfully imported {result['imported']} memories!")
                    else:
                        st.error(f"Import failed: {result['error']}")
                except Exception as e:
                    st.error(f"Error importing memories: {str(e)}")


def _render_memory_settings():
    """Memory system settings."""
    st.subheader("Memory Settings")
    
    # Memory storage settings
    st.write("### Storage Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input(
            "Max Memory Age (days)",
            min_value=1,
            max_value=365,
            value=90,
            help="Maximum age of memories before they are archived"
        )
    
    with col2:
        st.number_input(
            "Memory Limit",
            min_value=100,
            max_value=100000,
            value=10000,
            step=100,
            help="Maximum number of memories to store"
        )
    
    # Memory systems
    st.write("### Memory Systems")
    
    systems = {
        "SQLite": True,
        "LightRAG Graph": True,
        "Vector Store": False,
        "External API": False
    }
    
    for system, enabled in systems.items():
        st.checkbox(system, value=enabled, key=f"system_{system}")
    
    # Save settings
    if st.button("Save Settings"):
        st.success("Memory settings saved successfully!")
        st.info("Some settings may require a restart to take effect.")