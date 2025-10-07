"""
User Management Component

Provides interface for:
- Creating new users
- Switching between users
- Managing user settings and permissions
- Viewing user activity
"""

import os
from datetime import date, datetime

import pandas as pd
import streamlit as st

# Import project modules
from personal_agent.streamlit.utils.user_utils import (
    create_new_user,
    delete_user,
    get_all_users,
    get_all_users_with_profiles,
    get_user_details,
    get_user_profile_summary,
    update_cognitive_state,
    update_contact_info,
    update_user_profile,
)


def user_management_tab():
    """Render the user management tab."""
    st.title("User Management")

    # Create tabs for different user management functions
    tabs = st.tabs(
        [
            " User Overview ",
            " Create User ",
            " Profile Management ",
            " Switch User ",
            " Delete User ",
            " Backup & Restore ",
            " User Settings ",
        ]
    )

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
        _render_backup_restore()

    with tabs[6]:
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
                with st.expander(
                    f"👤 {user['user_name']} ({user['user_id']})"
                    + (" - Current User" if user.get("is_current") else "")
                ):
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
                        cognitive_state = user.get("cognitive_state", 50)
                        st.write(f"Cognitive State: {cognitive_state}/100")
                        st.progress(cognitive_state / 100)

                        # Handle profile summary with better error handling
                        try:
                            profile_summary = user.get("profile_summary", {})
                            if profile_summary and not profile_summary.get("error"):
                                completion = profile_summary.get(
                                    "completion_percentage", 0
                                )
                                st.write(f"Profile Complete: {completion:.1f}%")
                                st.progress(completion / 100)

                                if profile_summary.get("missing_fields"):
                                    st.write(
                                        f"Missing: {', '.join(profile_summary['missing_fields'])}"
                                    )
                            elif profile_summary.get("error"):
                                st.write("Profile Status: Error processing profile")
                            else:
                                st.write("Profile Status: Not available")
                        except Exception as e:
                            st.write("Profile Status: Error processing memory")
                            # Optionally log the error for debugging
                            # st.caption(f"Debug: {str(e)}")

            # Display user count
            st.caption(f"Total Users: {len(users)}")
        else:
            st.info("No users found.")

    except Exception as e:
        st.error(f"Error loading user information: {str(e)}")


def _render_create_user():
    """Interface for creating a new user with enhanced profile fields."""
    st.subheader("Create New User")

    # Form for creating a new user
    with st.form("create_user_form"):
        st.write("**Basic Information**")
        user_id = st.text_input("User ID", help="Unique identifier for the user")

        user_name = st.text_input("User Name", help="Display name for the user")

        user_type = st.selectbox(
            "User Type",
            ["Standard", "Admin", "Guest"],
            help="Determines user permissions",
        )

        st.write("**Profile Information (Optional)**")
        email = st.text_input("Email", help="User's email address")

        phone = st.text_input("Phone", help="User's phone number")

        address = st.text_area("Address", help="User's address")

        birth_date = st.date_input(
            "Birth Date",
            value=None,
            min_value=datetime.min.date(),
            max_value=datetime.max.date(),
            help="User's birth date (YYYY-MM-DD format) - supports dates from year 1 to year 9999",
        )

        delta_year = st.number_input(
            "Delta Year",
            min_value=0,
            max_value=150,
            value=0,
            help="Years from birth when writing memories (e.g., 6 for writing as 6-year-old)",
        )

        # Show calculated memory year if both fields are set
        if birth_date and delta_year > 0:
            memory_year = birth_date.year + delta_year
            st.info(f"Memory context year: {memory_year}")

        cognitive_state = st.slider(
            "Cognitive State",
            min_value=0,
            max_value=100,
            value=100,
            help="User's cognitive state on a scale of 0-100",
        )

        st.write("**System Options**")
        create_docker = st.checkbox(
            "Create Docker Containers",
            value=True,
            help="Create Docker containers for this user",
        )

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
                    delta_year=delta_year if delta_year is not None else None,
                    cognitive_state=cognitive_state,
                    create_docker=create_docker,
                )

                if result["success"]:
                    st.success(f"User '{user_id}' created successfully!")
                    st.info(
                        "You may need to restart Docker containers for changes to take effect."
                    )

                    # Show profile completion
                    if email or phone or address:
                        st.info("✅ User created with extended profile information")
                    else:
                        st.info(
                            "ℹ️ User created with basic information. You can add profile details later in the Profile Management tab."
                        )
                else:
                    st.error(f"Failed to create user: {result['error']}")

            except Exception as e:
                st.error(f"Error creating user: {str(e)}")


def _render_profile_management():
    """Interface for managing user profiles."""
    st.subheader("Profile Management")

    try:
        # Get all users
        users = get_all_users()
        user_ids = [user["user_id"] for user in users]

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
                        st.write(
                            f"Birth Date: {user_details.get('birth_date', 'Not set')}"
                        )
                        st.write(
                            f"Delta Year: {user_details.get('delta_year', 'Not set')}"
                        )
                        st.write(
                            f"Cognitive State: {user_details.get('cognitive_state', 50)}/100"
                        )

                    with col2:
                        # Profile completion
                        profile_summary = user_details.get("profile_summary", {})
                        if profile_summary and not profile_summary.get("error"):
                            completion = profile_summary.get("completion_percentage", 0)
                            st.metric("Profile Completion", f"{completion:.1f}%")

                            if profile_summary.get("missing_fields"):
                                st.warning(
                                    f"Missing fields: {', '.join(profile_summary['missing_fields'])}"
                                )

                    # Profile update forms
                    st.subheader("Update Profile")

                    # Create tabs for different profile sections
                    profile_tabs = st.tabs(
                        ["📞 Contact Info", "📅 Personal Info", "🧠 Cognitive State"]
                    )

                    with profile_tabs[0]:
                        # Contact Information Form
                        with st.form("update_contact_form"):
                            st.write("**Contact Information**")

                            new_email = st.text_input(
                                "Email",
                                value=user_details.get("email", ""),
                                help="User's email address",
                            )

                            new_phone = st.text_input(
                                "Phone",
                                value=user_details.get("phone", ""),
                                help="User's phone number",
                            )

                            new_address = st.text_area(
                                "Address",
                                value=user_details.get("address", ""),
                                help="User's address",
                            )

                            contact_submitted = st.form_submit_button(
                                "Update Contact Info"
                            )

                            if contact_submitted:
                                try:
                                    result = update_contact_info(
                                        selected_user,
                                        email=new_email if new_email else None,
                                        phone=new_phone if new_phone else None,
                                        address=new_address if new_address else None,
                                    )

                                    if result["success"]:
                                        st.success(
                                            "Contact information updated successfully!"
                                        )
                                        if result.get("updated_fields"):
                                            st.info(
                                                f"Updated fields: {', '.join(result['updated_fields'])}"
                                            )
                                        st.rerun()
                                    else:
                                        st.error("Failed to update contact information")
                                        if result.get("errors"):
                                            for error in result["errors"]:
                                                st.error(f"❌ {error}")
                                except Exception as e:
                                    st.error(f"Error updating contact info: {str(e)}")

                    with profile_tabs[1]:
                        # Personal Information Form
                        with st.form("update_personal_form"):
                            st.write("**Personal Information**")

                            # Birth Date
                            current_birth_date = user_details.get("birth_date")
                            if current_birth_date:
                                try:
                                    # Parse the current birth date
                                    current_date = datetime.fromisoformat(
                                        current_birth_date
                                    ).date()
                                except:
                                    current_date = None
                            else:
                                current_date = None

                            new_birth_date = st.date_input(
                                "Birth Date",
                                value=current_date,
                                min_value=datetime.min.date(),
                                max_value=datetime.max.date(),
                                help="User's birth date (YYYY-MM-DD format) - supports dates from year 1 to year 9999",
                            )

                            # Delta Year
                            current_delta_year = user_details.get("delta_year", 0)
                            new_delta_year = st.number_input(
                                "Delta Year",
                                min_value=0,
                                max_value=150,
                                value=(
                                    int(current_delta_year) if current_delta_year else 0
                                ),
                                help="Years from birth when writing memories (e.g., 6 for writing as 6-year-old)",
                            )

                            # Show calculated memory year if both fields are set
                            if new_birth_date and new_delta_year > 0:
                                memory_year = new_birth_date.year + new_delta_year
                                st.info(f"Memory context year: {memory_year}")

                            personal_submitted = st.form_submit_button(
                                "Update Personal Info"
                            )

                            if personal_submitted:
                                try:
                                    result = update_contact_info(
                                        selected_user,
                                        birth_date=(
                                            new_birth_date.isoformat()
                                            if new_birth_date
                                            else None
                                        ),
                                        delta_year=(
                                            new_delta_year
                                            if new_delta_year is not None
                                            else None
                                        ),
                                    )

                                    if result["success"]:
                                        st.success(
                                            "Personal information updated successfully!"
                                        )
                                        if result.get("updated_fields"):
                                            st.info(
                                                f"Updated fields: {', '.join(result['updated_fields'])}"
                                            )
                                        # Clear cached user manager to refresh user list
                                        from personal_agent.streamlit.utils.user_utils import (
                                            get_user_manager,
                                        )

                                        get_user_manager.clear()
                                        st.rerun()
                                    else:
                                        st.error(
                                            "Failed to update personal information"
                                        )
                                        if result.get("errors"):
                                            for error in result["errors"]:
                                                st.error(f"❌ {error}")
                                except Exception as e:
                                    st.error(f"Error updating personal info: {str(e)}")

                    with profile_tabs[2]:
                        # Cognitive State Form
                        with st.form("update_cognitive_form"):
                            st.write("**Cognitive State**")

                            current_cognitive_state = user_details.get(
                                "cognitive_state", 50
                            )
                            new_cognitive_state = st.slider(
                                "Cognitive State",
                                min_value=0,
                                max_value=100,
                                value=int(current_cognitive_state),
                                help="User's cognitive state on a scale of 0-100",
                            )

                            # Show current vs new comparison
                            if new_cognitive_state != current_cognitive_state:
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(
                                        f"**Current:** {current_cognitive_state}/100"
                                    )
                                    st.progress(current_cognitive_state / 100)
                                with col2:
                                    st.write(f"**New:** {new_cognitive_state}/100")
                                    st.progress(new_cognitive_state / 100)

                            cognitive_submitted = st.form_submit_button(
                                "Update Cognitive State"
                            )

                            if cognitive_submitted:
                                try:
                                    result = update_cognitive_state(
                                        selected_user, new_cognitive_state
                                    )

                                    if result["success"]:
                                        st.success(
                                            "Cognitive state updated successfully!"
                                        )
                                        st.info(
                                            f"Updated cognitive state from {current_cognitive_state} to {new_cognitive_state}"
                                        )
                                        st.rerun()
                                    else:
                                        st.error("Failed to update cognitive state")
                                        if result.get("error"):
                                            st.error(f"❌ {result['error']}")
                                except Exception as e:
                                    st.error(
                                        f"Error updating cognitive state: {str(e)}"
                                    )

                else:
                    st.warning(f"User '{selected_user}' not found.")
        else:
            st.info("No users available for profile management.")

    except Exception as e:
        st.error(f"Error loading profile management: {str(e)}")


def _render_switch_user():
    """Interface for switching between users."""
    st.subheader("Switch User")

    try:
        # Get all users
        users = get_all_users()
        user_ids = [user["user_id"] for user in users]

        if user_ids:
            # Get current user
            current_user_id = os.getenv("USER_ID", "Unknown")

            # Display current user status
            st.info(f"**Current User:** {current_user_id}")

            # Filter out current user from selection
            available_users = [uid for uid in user_ids if uid != current_user_id]

            if available_users:
                # User selection dropdown
                st.write("**Select User to Switch To:**")
                selected_user = st.selectbox(
                    "Available Users",
                    [""] + available_users,
                    help="Choose the user you want to switch to",
                    key="switch_user_selectbox"
                )

                if selected_user:
                    # Show selected user details
                    user_details = get_user_details(selected_user)
                    if user_details:
                        st.success(f"**Selected:** {user_details.get('user_name', selected_user)} ({selected_user})")

                        # Display user information
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**User Details:**")
                            st.write(f"• User ID: {user_details.get('user_id', 'N/A')}")
                            st.write(f"• Name: {user_details.get('user_name', 'N/A')}")
                            st.write(f"• Type: {user_details.get('user_type', 'N/A')}")

                        with col2:
                            st.write("**Profile Status:**")
                            cognitive_state = user_details.get("cognitive_state", 50)
                            st.write(f"• Cognitive State: {cognitive_state}/100")
                            st.progress(cognitive_state / 100)

                            profile_summary = user_details.get("profile_summary", {})
                            if profile_summary and not profile_summary.get("error"):
                                completion = profile_summary.get("completion_percentage", 0)
                                st.write(f"• Profile Complete: {completion:.1f}%")
                                st.progress(completion / 100)

                        # Warning about switching
                        st.warning("⚠️ **Important:** Switching users will:")
                        st.write("• Change the active user context")
                        st.write("• Restart Docker services with new user data")
                        st.write("• Update all user-dependent configurations")
                        st.write("• May take a few moments to complete")

                        # Switch button
                        if st.button(
                            f"🔄 Switch to {user_details.get('user_name', selected_user)}",
                            type="primary",
                            use_container_width=True
                        ):
                                # Perform the switch via REST API
                                with st.spinner(f"Switching to user '{selected_user}'... This may take a moment."):
                                    try:
                                        import requests

                                        # Call the REST API switch endpoint from paga_streamlit_agno
                                        # Port 8001 is used by paga_streamlit_agno (dashboard uses 8002)
                                        api_url = "http://localhost:8001/api/v1/users/switch"

                                        response = requests.post(
                                            api_url,
                                            json={
                                                "user_id": selected_user,
                                                "restart_containers": True
                                            },
                                            timeout=30
                                        )

                                        if response.status_code == 200:
                                            result = response.json()
                                            if result.get("success") == "True":
                                                st.success("✅ **User switched successfully!**")
                                                st.info(f"**Now active as:** {selected_user}")

                                                # Display success details
                                                if result.get("actions_performed"):
                                                    st.info("**Actions performed:**")
                                                    for action in result["actions_performed"]:
                                                        st.write(f"• {action}")

                                                # Clear cached user manager to refresh user list
                                                from personal_agent.streamlit.utils.user_utils import get_user_manager
                                                get_user_manager.clear()

                                                # Success message with refresh suggestion
                                                st.success("🎉 **Switch Complete!** You may need to refresh the page to see all changes take effect.")
                                            else:
                                                error_msg = result.get("error", "Unknown error")
                                                st.error(f"❌ **Switch failed:** {error_msg}")
                                        else:
                                            st.error(f"❌ Switch request failed with status code: {response.status_code}")
                                            try:
                                                error_detail = response.json().get("error", "No details available")
                                                st.error(f"Error details: {error_detail}")
                                            except:
                                                pass

                                    except requests.exceptions.RequestException as e:
                                        st.error(f"❌ **Error connecting to REST API:** {str(e)}")
                                        st.info("Make sure the Personal Agent service (paga_streamlit_agno) is running on port 8001.")
                                    except Exception as e:
                                        st.error(f"❌ **Error during user switch:** {str(e)}")
                                        st.info("If this error persists, try using the command-line switch-user.py script instead.")

                        # Alternative: Quick switch without confirmation (for power users)
                        with st.expander("⚡ Quick Switch (Advanced)"):
                            st.warning("This bypasses additional confirmation and refreshes automatically. Use with caution!")
                            if st.button(
                                f"⚡ Quick Switch to {user_details.get('user_name', selected_user)}",
                                type="secondary"
                            ):
                                with st.spinner(f"Quick switching to user '{selected_user}'..."):
                                    try:
                                        import requests

                                        # Call the REST API switch endpoint
                                        api_url = "http://localhost:8001/api/v1/users/switch"

                                        response = requests.post(
                                            api_url,
                                            json={
                                                "user_id": selected_user,
                                                "restart_containers": True
                                            },
                                            timeout=30
                                        )

                                        if response.status_code == 200:
                                            result = response.json()
                                            if result.get("success") == "True":
                                                st.success("✅ **Quick switch completed!**")
                                                st.info(f"**Now active as:** {selected_user}")

                                                # Clear cached user manager
                                                from personal_agent.streamlit.utils.user_utils import get_user_manager
                                                get_user_manager.clear()

                                                st.success("🔄 Refreshing user data...")
                                                st.rerun()
                                            else:
                                                st.error(f"❌ **Quick switch failed:** {result.get('error', 'Unknown error')}")
                                        else:
                                            st.error(f"❌ Quick switch request failed with status code: {response.status_code}")

                                    except requests.exceptions.RequestException as e:
                                        st.error(f"❌ **Error connecting to REST API:** {str(e)}")
                                        st.info("Make sure the Personal Agent service (paga_streamlit_agno) is running on port 8001.")
                                    except Exception as e:
                                        st.error(f"❌ **Error during quick switch:** {str(e)}")

                    else:
                        st.error(f"Could not retrieve details for user '{selected_user}'")
                else:
                    st.info("👆 Select a user from the dropdown above to switch to them.")
            else:
                st.info("ℹ️ No other users available to switch to. Create additional users first.")
        else:
            st.info("ℹ️ No users found. Create users first before switching.")

    except Exception as e:
        st.error(f"❌ Error loading switch user interface: {str(e)}")
        st.info("Try refreshing the page or check the system logs for more details.")


def _render_delete_user():
    """Interface for deleting users."""
    st.subheader("Delete User")
    st.warning("⚠️ **Warning**: User deletion is permanent and cannot be undone!")

    try:
        # Get all users
        users = get_all_users()
        user_ids = [user["user_id"] for user in users]

        if user_ids:
            # Get current user to prevent self-deletion
            current_user_id = os.getenv("USER_ID", "Unknown")

            # Form for deleting user
            with st.form("delete_user_form"):
                st.write("**Select User to Delete**")

                selected_user = st.selectbox(
                    "User to Delete",
                    [""] + user_ids,
                    help="Choose the user you want to delete",
                )

                if selected_user:
                    # Show user details
                    user_details = get_user_details(selected_user)
                    if user_details:
                        # Prevent current user deletion
                        if selected_user == current_user_id:
                            st.error("❌ **Cannot delete the currently active user!**")
                            st.info(
                                "💡 Switch to a different user first, then delete this user."
                            )
                        else:
                            st.info("**User Details:**")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(
                                    f"**User ID:** {user_details.get('user_id', 'N/A')}"
                                )
                                st.write(
                                    f"**User Name:** {user_details.get('user_name', 'N/A')}"
                                )
                                st.write(
                                    f"**User Type:** {user_details.get('user_type', 'N/A')}"
                                )
                            with col2:
                                st.write(
                                    f"**Email:** {user_details.get('email', 'Not set')}"
                                )
                                st.write(
                                    f"**Last Seen:** {user_details.get('last_seen', 'N/A')}"
                                )
                                st.write(
                                    f"**Created:** {user_details.get('created_at', 'N/A')}"
                                )

                st.write("**Deletion Options**")

                # Deletion options
                col1, col2 = st.columns(2)
                with col1:
                    delete_data = st.checkbox(
                        "Delete User Data",
                        value=True,
                        help="Delete the user's persistent data directory",
                    )

                    backup_before_delete = st.checkbox(
                        "Create Backup Before Deletion",
                        value=True,
                        help="Create a backup of user data before deletion",
                    )

                with col2:
                    dry_run = st.checkbox(
                        "Preview Mode (Dry Run)",
                        value=False,
                        help="Show what would be deleted without actually deleting",
                    )

                # Confirmation
                st.write("**Confirmation**")
                confirmation_text = ""  # Initialize to prevent undefined variable error
                if selected_user and selected_user != current_user_id:
                    # Use session state key that includes the selected user to reset when user changes
                    confirmation_key = f"delete_confirmation_{selected_user}"
                    confirmation_text = st.text_input(
                        f"Type '{selected_user}' to confirm deletion:",
                        key=confirmation_key,
                        help="This is a safety measure to prevent accidental deletions",
                    )

                    # Show what will happen
                    if dry_run:
                        st.info(
                            "🔍 **Preview Mode**: This will show what would be deleted without actually deleting anything."
                        )
                    else:
                        st.error(
                            "🗑️ **This will permanently delete the user and cannot be undone!**"
                        )
                        if backup_before_delete:
                            st.info("💾 A backup will be created before deletion.")
                        if delete_data:
                            st.warning(
                                "📁 User's data directory will be permanently deleted."
                            )
                        else:
                            st.info("📁 User's data directory will be preserved.")

                # Submit button
                submitted = st.form_submit_button(
                    "🔍 Preview Deletion" if dry_run else "🗑️ Delete User",
                    type="secondary" if dry_run else "primary",
                )

                if submitted:
                    if not selected_user:
                        st.error("❌ Please select a user to delete.")
                    elif selected_user == current_user_id:
                        st.error(
                            "❌ Cannot delete the currently active user. Switch to a different user first."
                        )
                    elif not dry_run and confirmation_text != selected_user:
                        st.error(
                            f"❌ Please type '{selected_user}' exactly to confirm deletion."
                        )
                    else:
                        try:
                            # Perform deletion (or dry run)
                            action_text = (
                                "Previewing deletion" if dry_run else "Deleting user"
                            )
                            with st.spinner(f"{action_text} for '{selected_user}'..."):
                                result = delete_user(
                                    selected_user,
                                    delete_data=delete_data,
                                    backup_data=backup_before_delete,
                                    dry_run=dry_run,
                                )

                            if result["success"]:
                                if dry_run:
                                    st.success(
                                        f"🔍 **Preview completed for user '{selected_user}'**"
                                    )
                                    st.info("**What would be deleted:**")
                                else:
                                    st.success(
                                        f"✅ **User '{selected_user}' deleted successfully!**"
                                    )
                                    st.info("**Deletion completed:**")

                                # Display detailed results
                                if result.get("actions_performed"):
                                    st.subheader(
                                        "Actions Performed:"
                                        if not dry_run
                                        else "Actions That Would Be Performed:"
                                    )
                                    for action in result["actions_performed"]:
                                        st.write(f"• {action}")

                                # Show backup information if created
                                if result.get("backup_created"):
                                    st.success("💾 **Backup created successfully!**")
                                    backup_info = result.get("backup_info", {})
                                    if backup_info:
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.write(
                                                f"**Backup Path:** {backup_info.get('backup_path', 'N/A')}"
                                            )
                                            st.write(
                                                f"**Backup Size:** {backup_info.get('backup_size_mb', 0):.2f} MB"
                                            )
                                        with col2:
                                            st.write(
                                                f"**Files Backed Up:** {backup_info.get('files_backed_up', 0)}"
                                            )
                                            st.write(
                                                f"**Timestamp:** {backup_info.get('timestamp', 'N/A')}"
                                            )

                                # Show data deletion information
                                if result.get("data_deleted") and not dry_run:
                                    data_info = result.get("data_deletion_info", {})
                                    if data_info:
                                        st.info("📁 **Data Directory Information:**")
                                        st.write(
                                            f"• Path: {data_info.get('data_path', 'N/A')}"
                                        )
                                        st.write(
                                            f"• Size: {data_info.get('size_mb', 0):.2f} MB"
                                        )
                                        st.write(
                                            f"• Files: {data_info.get('file_count', 0)}"
                                        )
                                elif result.get("data_preserved"):
                                    st.info(
                                        "📁 **User data directory preserved** (can be manually deleted later)"
                                    )

                                # Clear cached user manager to refresh user list
                                if not dry_run:
                                    from personal_agent.streamlit.utils.user_utils import (
                                        get_user_manager,
                                    )

                                    get_user_manager.clear()

                                    # Clear the confirmation text box after successful deletion
                                    confirmation_key = (
                                        f"delete_confirmation_{selected_user}"
                                    )
                                    if confirmation_key in st.session_state:
                                        del st.session_state[confirmation_key]

                                    st.success("🔄 User list refreshed successfully!")
                                    # Force a rerun to refresh the entire component and user list
                                    st.rerun()

                            else:
                                action_text = "preview" if dry_run else "deletion"
                                st.error(
                                    f"❌ Failed to {action_text} user: {result.get('error', 'Unknown error')}"
                                )

                                # Show any partial results
                                if result.get("partial_results"):
                                    st.warning("⚠️ **Partial results:**")
                                    for partial_result in result["partial_results"]:
                                        st.write(f"• {partial_result}")

                        except Exception as e:
                            action_text = "preview" if dry_run else "deletion"
                            st.error(f"❌ Error during user {action_text}: {str(e)}")
        else:
            st.info("ℹ️ No users available for deletion.")

    except Exception as e:
        st.error(f"❌ Error loading user information: {str(e)}")

    # Additional safety information
    st.markdown("---")
    st.subheader("🛡️ Safety Information")

    col1, col2 = st.columns(2)
    with col1:
        st.info(
            """
        **Before Deleting a User:**
        • Make sure you're not deleting the current user
        • Consider creating a backup first
        • Verify you have the correct user selected
        • Use Preview Mode to see what will be deleted
        """
        )

    with col2:
        st.warning(
            """
        **What Gets Deleted:**
        • User profile and settings
        • User's data directory (if selected)
        • Docker container configurations
        • Memory and knowledge data
        • All user-specific files
        """
        )

    # Recovery information
    st.info(
        """
    **🔄 Recovery Options:**
    • If you created a backup, you can restore the user using the 'Backup & Restore' tab
    • If you preserved the data directory, you can recreate the user with the same ID
    • Docker containers can be recreated automatically when switching users
    """
    )


def _render_backup_restore():
    """Interface for backing up and restoring users."""
    st.subheader("Backup & Restore")

    # Create sub-tabs for backup and restore operations
    backup_tabs = st.tabs(["💾 Backup User", "📥 Restore User", "📋 List Backups"])

    with backup_tabs[0]:
        _render_backup_user()

    with backup_tabs[1]:
        _render_restore_user()

    with backup_tabs[2]:
        _render_list_backups()


def _render_backup_user():
    """Interface for backing up a user."""
    st.subheader("Backup User")
    st.info(
        "💾 Create a backup of a user's data directory for safekeeping or migration."
    )

    try:
        # Get all users
        users = get_all_users()
        user_ids = [user["user_id"] for user in users]

        if user_ids:
            # Form for backing up user
            with st.form("backup_user_form"):
                selected_user = st.selectbox(
                    "Select User to Backup",
                    [""] + user_ids,
                    help="Choose the user whose data you want to backup",
                )

                if selected_user:
                    # Show user details
                    user_details = get_user_details(selected_user)
                    if user_details:
                        st.info("**User Details:**")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(
                                f"**User ID:** {user_details.get('user_id', 'N/A')}"
                            )
                            st.write(
                                f"**User Name:** {user_details.get('user_name', 'N/A')}"
                            )
                        with col2:
                            st.write(
                                f"**User Type:** {user_details.get('user_type', 'N/A')}"
                            )
                            st.write(
                                f"**Last Seen:** {user_details.get('last_seen', 'N/A')}"
                            )

                submitted = st.form_submit_button("💾 Create Backup", type="primary")

                if submitted:
                    if not selected_user:
                        st.error("❌ Please select a user to backup.")
                    else:
                        try:
                            # Perform backup
                            with st.spinner(
                                f"Creating backup for user '{selected_user}'..."
                            ):
                                from personal_agent.streamlit.utils.user_utils import (
                                    get_user_manager,
                                )

                                user_manager = get_user_manager()
                                result = user_manager.backup_user(selected_user)

                            if result["success"]:
                                st.success(
                                    f"✅ User '{selected_user}' backed up successfully!"
                                )

                                # Display backup details
                                st.info("**Backup Details:**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(
                                        f"**Backup Path:** {result['backup_path']}"
                                    )
                                    st.write(f"**Timestamp:** {result['timestamp']}")
                                with col2:
                                    st.write(
                                        f"**Files Backed Up:** {result['files_backed_up']}"
                                    )
                                    st.write(
                                        f"**Size:** {result['backup_size_mb']:.2f} MB"
                                    )

                                # Show backup location
                                st.code(result["backup_path"], language="text")

                            else:
                                st.error(
                                    f"❌ Failed to backup user: {result.get('error', 'Unknown error')}"
                                )

                        except Exception as e:
                            st.error(f"❌ Error during user backup: {str(e)}")
        else:
            st.info("ℹ️ No users available for backup.")

    except Exception as e:
        st.error(f"❌ Error loading user information: {str(e)}")


def _render_restore_user():
    """Interface for restoring a user from backup."""
    st.subheader("Restore User")
    st.info("📥 Restore a user's data from a previously created backup.")

    try:
        # Get available backups
        from personal_agent.streamlit.utils.user_utils import get_user_manager

        user_manager = get_user_manager()
        backups_result = user_manager.list_user_backups()

        if backups_result["success"] and backups_result["backups"]:
            # Form for restoring user
            with st.form("restore_user_form"):
                st.write("**Restore Options**")

                # Target user ID
                target_user_id = st.text_input(
                    "Target User ID",
                    help="User ID to restore the backup to (can be different from original)",
                )

                # Backup selection
                backup_options = []
                backup_map = {}
                for backup in backups_result["backups"]:
                    display_name = f"{backup['user_id']} - {backup['formatted_date']} ({backup['size_mb']:.2f} MB)"
                    backup_options.append(display_name)
                    backup_map[display_name] = backup

                selected_backup_display = st.selectbox(
                    "Select Backup to Restore",
                    [""] + backup_options,
                    help="Choose the backup you want to restore",
                )

                if selected_backup_display:
                    selected_backup = backup_map[selected_backup_display]

                    # Show backup details
                    st.info("**Backup Details:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Original User:** {selected_backup['user_id']}")
                        st.write(
                            f"**Backup Date:** {selected_backup['formatted_date']}"
                        )
                    with col2:
                        st.write(f"**Files:** {selected_backup['file_count']}")
                        st.write(f"**Size:** {selected_backup['size_mb']:.2f} MB")

                    st.code(selected_backup["backup_path"], language="text")

                # Restore options
                st.write("**Advanced Options**")
                overwrite_existing = st.checkbox(
                    "Overwrite Existing Data",
                    value=False,
                    help="Overwrite existing user data if the target user already exists",
                )

                submitted = st.form_submit_button("📥 Restore Backup", type="primary")

                if submitted:
                    if not target_user_id:
                        st.error("❌ Please enter a target user ID.")
                    elif not selected_backup_display:
                        st.error("❌ Please select a backup to restore.")
                    else:
                        try:
                            selected_backup = backup_map[selected_backup_display]

                            # Perform restore
                            with st.spinner(
                                f"Restoring backup to user '{target_user_id}'..."
                            ):
                                result = user_manager.restore_user(
                                    target_user_id,
                                    selected_backup["backup_name"],
                                    overwrite_existing=overwrite_existing,
                                )

                            if result["success"]:
                                st.success(
                                    f"✅ User '{target_user_id}' restored successfully!"
                                )

                                # Display restore details
                                st.info("**Restore Details:**")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(
                                        f"**Restored From:** {result['backup_path']}"
                                    )
                                    st.write(
                                        f"**Restored To:** {result['restore_path']}"
                                    )
                                with col2:
                                    st.write(
                                        f"**Files Restored:** {result['data_restored']['files_restored']}"
                                    )
                                    st.write(
                                        f"**Size:** {result['data_restored']['total_size_mb']:.2f} MB"
                                    )

                                # Show actions performed
                                if result.get("actions_performed"):
                                    st.subheader("Actions Performed:")
                                    for action in result["actions_performed"]:
                                        st.write(f"• {action}")

                                # Clear cached user manager to refresh user list
                                get_user_manager.clear()

                            else:
                                st.error(
                                    f"❌ Failed to restore user: {result.get('error', 'Unknown error')}"
                                )

                        except Exception as e:
                            st.error(f"❌ Error during user restore: {str(e)}")
        else:
            st.info("ℹ️ No backups available for restore.")
            if not backups_result["success"]:
                st.error(
                    f"Error loading backups: {backups_result.get('error', 'Unknown error')}"
                )

    except Exception as e:
        st.error(f"❌ Error loading backup information: {str(e)}")


def _render_list_backups():
    """Interface for listing and managing backups."""
    st.subheader("List Backups")
    st.info("📋 View all available user backups and their details.")

    try:
        # Add refresh button
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Refresh Backups", help="Refresh backup list"):
                st.rerun()

        # Get available backups
        from personal_agent.streamlit.utils.user_utils import get_user_manager

        user_manager = get_user_manager()
        backups_result = user_manager.list_user_backups()

        if backups_result["success"]:
            if backups_result["backups"]:
                # Filter options
                st.subheader("Filter Options")
                col1, col2 = st.columns(2)

                with col1:
                    # Get unique user IDs from backups
                    unique_users = list(
                        set([backup["user_id"] for backup in backups_result["backups"]])
                    )
                    filter_user = st.selectbox(
                        "Filter by User", ["All Users"] + unique_users
                    )

                with col2:
                    # Sort options
                    sort_by = st.selectbox(
                        "Sort by",
                        [
                            "Date (Newest First)",
                            "Date (Oldest First)",
                            "User ID",
                            "Size",
                        ],
                    )

                # Apply filters
                filtered_backups = backups_result["backups"]
                if filter_user != "All Users":
                    filtered_backups = [
                        b for b in filtered_backups if b["user_id"] == filter_user
                    ]

                # Apply sorting
                if sort_by == "Date (Newest First)":
                    filtered_backups.sort(key=lambda x: x["timestamp"], reverse=True)
                elif sort_by == "Date (Oldest First)":
                    filtered_backups.sort(key=lambda x: x["timestamp"])
                elif sort_by == "User ID":
                    filtered_backups.sort(key=lambda x: x["user_id"])
                elif sort_by == "Size":
                    filtered_backups.sort(key=lambda x: x["size_mb"], reverse=True)

                # Display backups
                st.subheader(f"Available Backups ({len(filtered_backups)})")

                for backup in filtered_backups:
                    with st.expander(
                        f"💾 {backup['user_id']} - {backup['formatted_date']} ({backup['size_mb']:.2f} MB)"
                    ):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.write("**Backup Info:**")
                            st.write(f"User ID: {backup['user_id']}")
                            st.write(f"Backup Name: {backup['backup_name']}")
                            st.write(f"Timestamp: {backup['timestamp']}")

                        with col2:
                            st.write("**Details:**")
                            st.write(f"Date: {backup['formatted_date']}")
                            st.write(f"Files: {backup['file_count']}")
                            st.write(f"Size: {backup['size_mb']:.2f} MB")

                        with col3:
                            st.write("**Actions:**")
                            # Quick restore button
                            if st.button(
                                f"🔄 Quick Restore",
                                key=f"restore_{backup['backup_name']}",
                                help=f"Restore to original user ID: {backup['user_id']}",
                            ):
                                try:
                                    with st.spinner(
                                        f"Restoring {backup['user_id']}..."
                                    ):
                                        result = user_manager.restore_user(
                                            backup["user_id"],
                                            backup["backup_name"],
                                            overwrite_existing=True,
                                        )

                                    if result["success"]:
                                        st.success(
                                            f"✅ {backup['user_id']} restored successfully!"
                                        )
                                        get_user_manager.clear()  # Clear cache
                                        st.rerun()
                                    else:
                                        st.error(
                                            f"❌ Restore failed: {result.get('error', 'Unknown error')}"
                                        )
                                except Exception as e:
                                    st.error(f"❌ Error during restore: {str(e)}")

                        # Show backup path
                        st.code(backup["backup_path"], language="text")

                # Summary statistics
                st.subheader("Backup Statistics")
                total_size = sum([b["size_mb"] for b in filtered_backups])
                total_files = sum([b["file_count"] for b in filtered_backups])

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Backups", len(filtered_backups))
                with col2:
                    st.metric("Total Size", f"{total_size:.2f} MB")
                with col3:
                    st.metric("Total Files", total_files)

            else:
                st.info("ℹ️ No backups found.")
                st.write("Create your first backup using the 'Backup User' tab.")
        else:
            st.error(
                f"❌ Error loading backups: {backups_result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        st.error(f"❌ Error loading backup information: {str(e)}")


def _render_user_settings():
    """Interface for managing user settings."""
    st.subheader("User Settings")
    st.info("Manage user-specific settings and preferences.")
