"""
User Management Component

Provides interface for:
- Creating new users
- Switching between users
- Managing user settings and permissions
- Viewing user activity
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime

# Import project modules
from personal_agent.core.docker.user_sync import DockerUserSync
from personal_agent.streamlit.utils.user_utils import (
    get_all_users,
    create_new_user,
    switch_user,
    get_user_details,
    delete_user
)


def user_management_tab():
    """Render the user management tab."""
    st.title("User Management")
    
    # Create tabs for different user management functions
    tabs = st.tabs([" User Overview ", " Create User ", " Switch User ", " Delete User ", " User Settings "])
    
    with tabs[0]:
        _render_user_overview()
    
    with tabs[1]:
        _render_create_user()
    
    with tabs[2]:
        _render_switch_user()
    
    with tabs[3]:
        _render_delete_user()
    
    with tabs[4]:
        _render_user_settings()


def _render_user_overview():
    """Display overview of all users."""
    st.subheader("User Overview")
    
    # Add refresh button to manually refresh user list
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", help="Refresh user list"):
            from personal_agent.streamlit.utils.user_utils import get_user_manager
            get_user_manager.clear()
            st.rerun()
    
    try:
        # Get all users
        users = get_all_users()
        
        if users:
            # Create a DataFrame for display
            df = pd.DataFrame(users)
            st.dataframe(df)
            
            # Display user count
            st.caption(f"Total Users: {len(users)}")
        else:
            st.info("No users found.")
            
    except Exception as e:
        st.error(f"Error loading user information: {str(e)}")


def _render_create_user():
    """Interface for creating a new user."""
    st.subheader("Create New User")
    
    # Form for creating a new user
    with st.form("create_user_form"):
        user_id = st.text_input("User ID", 
                               help="Unique identifier for the user")
        
        user_name = st.text_input("User Name", 
                                 help="Display name for the user")
        
        user_type = st.selectbox("User Type", 
                                ["Standard", "Admin", "Guest"],
                                help="Determines user permissions")
        
        create_docker = st.checkbox("Create Docker Containers", 
                                   value=True,
                                   help="Create Docker containers for this user")
        
        submitted = st.form_submit_button("Create User")
        
        if submitted:
            try:
                # Create the new user
                result = create_new_user(
                    user_id=user_id,
                    user_name=user_name,
                    user_type=user_type,
                    create_docker=create_docker
                )
                
                if result['success']:
                    st.success(f"User '{user_id}' created successfully!")
                    st.info("You may need to restart Docker containers for changes to take effect.")
                else:
                    st.error(f"Failed to create user: {result['error']}")
                    
            except Exception as e:
                st.error(f"Error creating user: {str(e)}")


def _render_switch_user():
    """Interface for switching between users."""
    st.subheader("Switch User")
    
    try:
        # Get current user
        from personal_agent.config.user_id_mgr import get_userid
        current_user = get_userid()
        
        st.info(f"Current User: {current_user}")
        
        # Get all users
        users = get_all_users()
        user_ids = [user['user_id'] for user in users if user['user_id'] != current_user]
        
        if user_ids:
            # Form for switching user
            with st.form("switch_user_form"):
                selected_user = st.selectbox("Select User", user_ids)
                
                col1, col2 = st.columns(2)
                with col1:
                    restart_containers = st.checkbox("Restart LightRAG Containers", 
                                                   value=True,
                                                   help="Restart LightRAG Docker containers after switching user")
                with col2:
                    update_global_config = st.checkbox("Update Global USER_ID", 
                                                      value=True,
                                                      help="Update the global USER_ID configuration")
                
                submitted = st.form_submit_button("Switch User")
                
                if submitted:
                    try:
                        # Switch to the selected user
                        result = switch_user(
                            user_id=selected_user,
                            restart_containers=restart_containers
                        )
                        
                        if result['success']:
                            st.success(f"Switched to user '{selected_user}' successfully!")
                            
                            if update_global_config:
                                st.info("Global USER_ID configuration updated.")
                            
                            if restart_containers:
                                st.info("LightRAG containers will be restarted.")
                            
                            st.warning("Please refresh the page to see the changes.")
                        else:
                            st.error(f"Failed to switch user: {result['error']}")
                            
                    except Exception as e:
                        st.error(f"Error switching user: {str(e)}")
        else:
            st.warning("No other users available to switch to.")
        
        # Add manual LightRAG restart section
        st.subheader("Manual LightRAG Restart")
        st.write("Restart LightRAG containers for the current user:")
        
        if st.button("Restart LightRAG Containers"):
            try:
                from personal_agent.streamlit.utils.user_utils import get_user_manager
                user_manager = get_user_manager()
                result = user_manager.restart_lightrag_for_current_user()
                
                if result["success"]:
                    st.success("LightRAG containers restarted successfully!")
                    if result.get("services_restarted"):
                        st.info(f"Services restarted: {', '.join(result['services_restarted'])}")
                else:
                    st.error(f"Error restarting LightRAG containers: {result.get('error', 'Unknown error')}")
                    if result.get("errors"):
                        for error in result["errors"]:
                            st.warning(error)
            except Exception as e:
                st.error(f"Error restarting LightRAG containers: {str(e)}")
            
    except Exception as e:
        st.error(f"Error loading user information: {str(e)}")


def _render_user_settings():
    """Interface for managing user settings."""
    st.subheader("User Settings")
    
    try:
        # Get current user
        from personal_agent.config.user_id_mgr import get_userid
        current_user = get_userid()
        
        # Get user details
        user_details = get_user_details(current_user)
        
        if user_details:
            # Display current settings
            st.json(user_details)
            
            # Form for updating settings
            with st.form("update_settings_form"):
                st.text_input("User Name", 
                             value=user_details.get('user_name', ''),
                             help="Display name for the user")
                
                st.selectbox("User Type", 
                            ["Standard", "Admin", "Guest"],
                            index=["Standard", "Admin", "Guest"].index(user_details.get('user_type', 'Standard')),
                            help="Determines user permissions")
                
                # Add more settings as needed
                
                submitted = st.form_submit_button("Update Settings")
                
                if submitted:
                    st.success("Settings updated successfully!")
                    st.info("Some settings may require a restart to take effect.")
        else:
            st.warning(f"No settings found for user '{current_user}'.")
            
    except Exception as e:
        st.error(f"Error loading user settings: {str(e)}")


def _render_delete_user():
    """Interface for deleting users with enhanced options."""
    st.subheader("Delete User")
    
    st.warning("⚠️ **Warning**: User deletion is permanent and cannot be undone!")
    
    try:
        # Get current user
        from personal_agent.config.user_id_mgr import get_userid
        current_user = get_userid()
        
        # Get all users except current user
        users = get_all_users()
        user_ids = [user['user_id'] for user in users if user['user_id'] != current_user]
        
        if user_ids:
            # Form for deleting user
            with st.form("delete_user_form"):
                selected_user = st.selectbox("Select User to Delete",
                                           [""] + user_ids,
                                           help="Choose the user you want to delete")
                
                if selected_user:
                    # Show user details
                    user_details = get_user_details(selected_user)
                    if user_details:
                        st.info(f"**User Details:**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**User ID:** {user_details.get('user_id', 'N/A')}")
                            st.write(f"**User Name:** {user_details.get('user_name', 'N/A')}")
                        with col2:
                            st.write(f"**User Type:** {user_details.get('user_type', 'N/A')}")
                            st.write(f"**Created:** {user_details.get('created_at', 'N/A')}")
                
                st.subheader("Deletion Options")
                
                # Deletion options
                col1, col2 = st.columns(2)
                with col1:
                    delete_data = st.checkbox("Delete User Data",
                                            value=True,
                                            help="Delete all persistent data directories for this user")
                    backup_data = st.checkbox("Backup Data Before Deletion",
                                            value=False,
                                            help="Create a backup of user data before deleting")
                
                with col2:
                    dry_run = st.checkbox("Dry Run (Preview Only)",
                                        value=False,
                                        help="Preview what would be deleted without actually deleting")
                
                # Confirmation
                st.subheader("Confirmation")
                confirmation_text = ""
                if selected_user:
                    confirmation_text = st.text_input(
                        f"Type '{selected_user}' to confirm deletion:",
                        help="This is a safety measure to prevent accidental deletions"
                    )
                
                # Submit button - always enabled
                submitted = st.form_submit_button(
                    "🗑️ Delete User" if not dry_run else "👁️ Preview Deletion",
                    type="primary" if dry_run else "secondary"
                )
                
                # Validation and confirmation after submission
                if submitted:
                    if not selected_user:
                        st.error("❌ Please select a user to delete.")
                    elif not dry_run and confirmation_text != selected_user:
                        st.error(f"❌ Please type '{selected_user}' exactly to confirm deletion.")
                    else:
                        try:
                            # Perform deletion
                            with st.spinner(f"{'Previewing' if dry_run else 'Deleting'} user '{selected_user}'..."):
                                result = delete_user(
                                    user_id=selected_user,
                                    delete_data=delete_data,
                                    backup_data=backup_data,
                                    dry_run=dry_run
                                )
                        
                            if result['success']:
                                if dry_run:
                                    st.success("✅ Dry run completed successfully!")
                                    st.info("**Preview Results:**")
                                else:
                                    st.success(f"✅ User '{selected_user}' deleted successfully!")
                                
                                # Display detailed results
                                if result.get('actions_performed'):
                                    st.subheader("Actions Performed:")
                                    for action in result['actions_performed']:
                                        st.write(f"• {action}")
                                
                                # Display data deletion info
                                data_info = result.get('data_deleted', {})
                                if data_info.get('files_removed', 0) > 0:
                                    st.info(f"📊 **Data Summary:** {data_info['files_removed']} files, "
                                           f"{data_info['total_size_mb']:.2f} MB")
                                
                                # Display backup info
                                backup_info = result.get('backup_info', {})
                                if backup_info.get('success'):
                                    st.success(f"💾 **Backup Created:** {backup_info['backup_path']}")
                                    st.info(f"Backup contains {backup_info['files_backed_up']} files "
                                           f"({backup_info['backup_size_mb']:.2f} MB)")
                                
                                # Display warnings
                                if result.get('warnings'):
                                    st.subheader("Warnings:")
                                    for warning in result['warnings']:
                                        st.warning(f"⚠️ {warning}")
                                
                                if not dry_run:
                                    # Clear the cached user manager to refresh user list
                                    from personal_agent.streamlit.utils.user_utils import get_user_manager
                                    get_user_manager.clear()
                                    st.success("🔄 User list updated automatically!")
                                    st.rerun()
                            else:
                                st.error(f"❌ Failed to delete user: {result.get('error', 'Unknown error')}")
                                
                                # Display any errors
                                if result.get('errors'):
                                    st.subheader("Errors:")
                                    for error in result['errors']:
                                        st.error(f"❌ {error}")
                                        
                        except Exception as e:
                            st.error(f"❌ Error during user deletion: {str(e)}")
        else:
            st.info("ℹ️ No users available for deletion (cannot delete current user).")
            st.write(f"Current user: **{current_user}**")
            
    except Exception as e:
        st.error(f"❌ Error loading user information: {str(e)}")
