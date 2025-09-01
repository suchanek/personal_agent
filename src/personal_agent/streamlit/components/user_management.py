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
    get_all_users_with_profiles,
    create_new_user,
    switch_user,
    get_user_details,
    delete_user,
    update_user_profile,
    update_cognitive_state,
    update_contact_info,
    get_user_profile_summary
)


def user_management_tab():
    """Render the user management tab."""
    st.title("User Management")
    
    # Create tabs for different user management functions
    tabs = st.tabs([" User Overview ", " Create User ", " Profile Management ", " Switch User ", " Delete User ", " User Settings "])
    
    with tabs[0]:
        _render_user_overview()
    
    with tabs[1]:
        _render_create_user()
    
    with tabs[2]:
        _render_profile_management()
    
    with tabs[3]:
        _render_switch_user()
    
    with tabs[4]:
        _render_delete_user()
    
    with tabs[5]:
        _render_user_settings()


def _render_user_overview():
    """Display overview of all users with enhanced profile information."""
    st.subheader("User Overview")
    
    # Add refresh button to manually refresh user list
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", help="Refresh user list"):
            from personal_agent.streamlit.utils.user_utils import get_user_manager
            get_user_manager.clear()
            st.rerun()
    
    try:
        # Get all users with profile information
        users = get_all_users_with_profiles()
        
        if users:
            # Create enhanced display with profile completion
            for user in users:
                with st.expander(f"👤 {user['user_name']} ({user['user_id']})" + (" - Current User" if user.get('is_current') else "")):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**Basic Info:**")
                        st.write(f"User ID: {user['user_id']}")
                        st.write(f"Name: {user['user_name']}")
                        st.write(f"Type: {user['user_type']}")
                        st.write(f"Birth Date: {user.get('birth_date', 'Not set')}")
                        st.write(f"Delta Year: {user.get('delta_year', 'Not set')}")
                        st.write(f"Created: {user.get('created_at', 'N/A')}")
                        st.write(f"Last Seen: {user.get('last_seen', 'N/A')}")
                    
                    with col2:
                        st.write("**Contact Info:**")
                        st.write(f"Email: {user.get('email', 'Not set')}")
                        st.write(f"Phone: {user.get('phone', 'Not set')}")
                        st.write(f"Address: {user.get('address', 'Not set')}")
                    
                    with col3:
                        st.write("**Profile Status:**")
                        cognitive_state = user.get('cognitive_state', 50)
                        st.write(f"Cognitive State: {cognitive_state}/100")
                        st.progress(cognitive_state / 100)
                        
                        profile_summary = user.get('profile_summary', {})
                        if profile_summary and not profile_summary.get('error'):
                            completion = profile_summary.get('completion_percentage', 0)
                            st.write(f"Profile Complete: {completion:.1f}%")
                            st.progress(completion / 100)
                            
                            if profile_summary.get('missing_fields'):
                                st.write(f"Missing: {', '.join(profile_summary['missing_fields'])}")
            
            # Display user count
            st.caption(f"Total Users: {len(users)}")
        else:
            st.info("No users found.")
            
    except Exception as e:
        st.error(f"Error loading user information: {str(e)}")


def _render_profile_management():
    """Interface for managing user profiles."""
    st.subheader("Profile Management")
    
    try:
        # Get all users
        users = get_all_users()
        user_ids = [user['user_id'] for user in users]
        
        if user_ids:
            # User selection
            selected_user = st.selectbox("Select User to Manage", user_ids)
            
            if selected_user:
                # Get current user details
                user_details = get_user_details(selected_user)
                
                if user_details:
                    # Display current profile
                    st.subheader(f"Current Profile: {user_details['user_name']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Current Information:**")
                        st.write(f"Email: {user_details.get('email', 'Not set')}")
                        st.write(f"Phone: {user_details.get('phone', 'Not set')}")
                        st.write(f"Address: {user_details.get('address', 'Not set')}")
                        st.write(f"Birth Date: {user_details.get('birth_date', 'Not set')}")
                        st.write(f"Delta Year: {user_details.get('delta_year', 'Not set')}")
                        st.write(f"Cognitive State: {user_details.get('cognitive_state', 50)}/100")
                    
                    with col2:
                        # Profile completion
                        profile_summary = user_details.get('profile_summary', {})
                        if profile_summary and not profile_summary.get('error'):
                            completion = profile_summary.get('completion_percentage', 0)
                            st.metric("Profile Completion", f"{completion:.1f}%")
                            
                            if profile_summary.get('missing_fields'):
                                st.warning(f"Missing fields: {', '.join(profile_summary['missing_fields'])}")
                    
                    # Profile update forms
                    st.subheader("Update Profile")
                    
                    # Contact Information Form
                    with st.form("update_contact_form"):
                        st.write("**Contact Information**")
                        
                        new_email = st.text_input("Email", 
                                                 value=user_details.get('email', ''),
                                                 help="User's email address")
                        
                        new_phone = st.text_input("Phone", 
                                                 value=user_details.get('phone', ''),
                                                 help="User's phone number")
                        
                        new_address = st.text_area("Address", 
                                                  value=user_details.get('address', ''),
                                                  help="User's address")
                        
                        contact_submitted = st.form_submit_button("Update Contact Info")
                        
                        if contact_submitted:
                            try:
                                result = update_contact_info(
                                    selected_user,
                                    email=new_email if new_email else None,
                                    phone=new_phone if new_phone else None,
                                    address=new_address if new_address else None
                                )
                                
                                if result['success']:
                                    st.success("Contact information updated successfully!")
                                    if result.get('updated_fields'):
                                        st.info(f"Updated fields: {', '.join(result['updated_fields'])}")
                                    st.rerun()
                                else:
                                    st.error("Failed to update contact information")
                                    if result.get('errors'):
                                        for error in result['errors']:
                                            st.error(f"❌ {error}")
                            except Exception as e:
                                st.error(f"Error updating contact info: {str(e)}")
                    
                    # Cognitive State Form
                    with st.form("update_cognitive_form"):
                        st.write("**Cognitive State**")
                        
                        current_cognitive = user_details.get('cognitive_state', 50)
                        new_cognitive = st.slider("Cognitive State", 
                                                 min_value=0, 
                                                 max_value=100, 
                                                 value=current_cognitive,
                                                 help="User's cognitive state on a scale of 0-100")
                        
                        st.write(f"Current: {current_cognitive} → New: {new_cognitive}")
                        
                        cognitive_submitted = st.form_submit_button("Update Cognitive State")
                        
                        if cognitive_submitted:
                            try:
                                result = update_cognitive_state(selected_user, new_cognitive)
                                
                                if result['success']:
                                    st.success(f"Cognitive state updated to {new_cognitive}!")
                                    st.rerun()
                                else:
                                    st.error("Failed to update cognitive state")
                                    if result.get('errors'):
                                        for error in result['errors']:
                                            st.error(f"❌ {error}")
                            except Exception as e:
                                st.error(f"Error updating cognitive state: {str(e)}")
                    
                    # Birth Date and Delta Year Form
                    with st.form("update_birth_delta_form"):
                        st.write("**Birth Date & Memory Context**")
                        
                        current_birth_date = user_details.get('birth_date', '')
                        new_birth_date = st.date_input("Birth Date", 
                                                      value=datetime.fromisoformat(current_birth_date).date() if current_birth_date else None,
                                                      min_value=datetime(1, 1, 1).date(),
                                                      max_value=datetime.now().date(),
                                                      help="User's birth date (YYYY-MM-DD format) - supports dates back to 1 AD")
                        
                        current_delta_year = user_details.get('delta_year')
                        new_delta_year = st.number_input("Delta Year", 
                                                        min_value=0, 
                                                        max_value=150, 
                                                        value=current_delta_year if current_delta_year is not None else 0,
                                                        help="Years from birth when writing memories (e.g., 6 for writing as 6-year-old)")
                        
                        # Show calculated memory year if both fields are set
                        if new_birth_date and new_delta_year > 0:
                            memory_year = new_birth_date.year + new_delta_year
                            st.info(f"Memory context year: {memory_year}")
                        
                        birth_delta_submitted = st.form_submit_button("Update Birth Date & Delta Year")
                        
                        if birth_delta_submitted:
                            try:
                                # Convert date to ISO string format
                                birth_date_str = new_birth_date.isoformat() if new_birth_date else None
                                delta_year_val = new_delta_year if new_delta_year > 0 else None
                                
                                result = update_user_profile(
                                    selected_user,
                                    birth_date=birth_date_str,
                                    delta_year=delta_year_val
                                )
                                
                                if result['success']:
                                    st.success("Birth date and delta year updated successfully!")
                                    if result.get('updated_fields'):
                                        st.info(f"Updated fields: {', '.join(result['updated_fields'])}")
                                    st.rerun()
                                else:
                                    st.error("Failed to update birth date and delta year")
                                    if result.get('errors'):
                                        for error in result['errors']:
                                            st.error(f"❌ {error}")
                            except Exception as e:
                                st.error(f"Error updating birth date and delta year: {str(e)}")
                    
                    # Basic Info Form
                    with st.form("update_basic_form"):
                        st.write("**Basic Information**")
                        
                        new_user_name = st.text_input("User Name", 
                                                     value=user_details.get('user_name', ''),
                                                     help="Display name for the user")
                        
                        new_user_type = st.selectbox("User Type", 
                                                    ["Standard", "Admin", "Guest"],
                                                    index=["Standard", "Admin", "Guest"].index(user_details.get('user_type', 'Standard')),
                                                    help="Determines user permissions")
                        
                        basic_submitted = st.form_submit_button("Update Basic Info")
                        
                        if basic_submitted:
                            try:
                                result = update_user_profile(
                                    selected_user,
                                    user_name=new_user_name,
                                    user_type=new_user_type
                                )
                                
                                if result['success']:
                                    st.success("Basic information updated successfully!")
                                    if result.get('updated_fields'):
                                        st.info(f"Updated fields: {', '.join(result['updated_fields'])}")
                                    st.rerun()
                                else:
                                    st.error("Failed to update basic information")
                                    if result.get('errors'):
                                        for error in result['errors']:
                                            st.error(f"❌ {error}")
                            except Exception as e:
                                st.error(f"Error updating basic info: {str(e)}")
                
                else:
                    st.warning(f"User '{selected_user}' not found.")
        else:
            st.info("No users available for profile management.")
            
    except Exception as e:
        st.error(f"Error loading profile management: {str(e)}")


def _render_create_user():
    """Interface for creating a new user with enhanced profile fields."""
    st.subheader("Create New User")
    
    # Form for creating a new user
    with st.form("create_user_form"):
        st.write("**Basic Information**")
        user_id = st.text_input("User ID", 
                               help="Unique identifier for the user")
        
        user_name = st.text_input("User Name", 
                                 help="Display name for the user")
        
        user_type = st.selectbox("User Type", 
                                ["Standard", "Admin", "Guest"],
                                help="Determines user permissions")
        
        st.write("**Profile Information (Optional)**")
        email = st.text_input("Email", 
                              help="User's email address")
        
        phone = st.text_input("Phone", 
                             help="User's phone number")
        
        address = st.text_area("Address", 
                              help="User's address")
        
        birth_date = st.date_input("Birth Date", 
                                  value=None,
                                  min_value=datetime(1, 1, 1).date(),
                                  max_value=datetime.now().date(),
                                  help="User's birth date (YYYY-MM-DD format) - supports dates back to 1 AD")
        
        delta_year = st.number_input("Delta Year", 
                                    min_value=0, 
                                    max_value=150, 
                                    value=0,
                                    help="Years from birth when writing memories (e.g., 6 for writing as 6-year-old)")
        
        # Show calculated memory year if both fields are set
        if birth_date and delta_year > 0:
            memory_year = birth_date.year + delta_year
            st.info(f"Memory context year: {memory_year}")
        
        cognitive_state = st.slider("Cognitive State", 
                                   min_value=0, 
                                   max_value=100, 
                                   value=100,
                                   help="User's cognitive state on a scale of 0-100")
        
        st.write("**System Options**")
        create_docker = st.checkbox("Create Docker Containers", 
                                   value=True,
                                   help="Create Docker containers for this user")
        
        submitted = st.form_submit_button("Create User")
        
        if submitted:
            try:
                # Validate required fields
                if not user_id:
                    st.error("User ID is required")
                    return
                
                # Create the new user with enhanced profile
                result = create_new_user(
                    user_id=user_id,
                    user_name=user_name or user_id,
                    user_type=user_type,
                    email=email if email else None,
                    phone=phone if phone else None,
                    address=address if address else None,
                    birth_date=birth_date.isoformat() if birth_date else None,
                    delta_year=delta_year if delta_year > 0 else None,
                    cognitive_state=cognitive_state,
                    create_docker=create_docker
                )
                
                if result['success']:
                    st.success(f"User '{user_id}' created successfully!")
                    st.info("You may need to restart Docker containers for changes to take effect.")
                    
                    # Show profile completion
                    if email or phone or address:
                        st.info("✅ User created with extended profile information")
                    else:
                        st.info("ℹ️ User created with basic information. You can add profile details later in the Profile Management tab.")
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
