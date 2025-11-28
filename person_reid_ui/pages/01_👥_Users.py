"""
User Management Page - Standalone Module
No dependencies on backend code
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
import pandas as pd
from src.api_client import APIError
from src.utils import show_error, show_success, show_info, confirm_action, load_custom_css

# Page configuration
st.set_page_config(
    page_title="Users - Person ReID",
    page_icon="👥",
    layout="wide"
)

# Load CSS
load_custom_css()

# Get API client and config from session state
api = st.session_state.get('api_client')
config = st.session_state.get('config')

if not api or not config:
    st.error("❌ API client not initialized. Please return to Home page.")
    st.stop()


def main():
    st.title("👥 User Management")
    st.markdown("---")
    
    # Check API connection
    if not api.is_available():
        show_error(f"Cannot connect to API server at {config.api.base_url}")
        return
    
    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📋 View Users", "➕ Create User", "🔍 Search"])
    
    with tab1:
        view_users_tab()
    
    with tab2:
        create_user_tab()
    
    with tab3:
        search_users_tab()


def view_users_tab():
    """Display all users with their zones"""
    st.subheader("All Users")
    
    # Refresh button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh", key="refresh_users"):
            st.rerun()
    
    try:
        users = api.get_users(limit=config.display.max_users_per_page)
        
        if not users:
            show_info("No users found. Create your first user in the 'Create User' tab.")
            return
        
        show_success(f"Found {len(users)} users")
        
        # Display users in expandable cards
        for user in users:
            with st.expander(f"🧑 {user['name']} (ID: {user['id']}, Global ID: {user['global_id']})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Name:** {user['name']}")
                    st.markdown(f"**User ID:** {user['id']}")
                    st.markdown(f"**Global ID:** {user['global_id']}")
                    st.markdown(f"**Created:** {user['created_at'][:19]}")
                    
                    # Display zones
                    zones = user.get('zones', [])
                    if zones:
                        st.markdown("**Assigned Zones:**")
                        for zone in zones:
                            threshold = zone.get('violation_threshold', 10)
                            st.markdown(
                                f'<span class="zone-badge">🗺️ {zone["zone_name"]} ({zone["zone_id"]}) - ⏱️ {threshold}s threshold</span>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown("*No zones assigned*")
                
                with col2:
                    st.markdown("**Actions:**")
                    
                    # Edit button
                    if st.button("✏️ Edit", key=f"edit_{user['id']}"):
                        st.session_state[f"editing_{user['id']}"] = True
                        st.rerun()
                    
                    # Delete button
                    if st.button("🗑️ Delete", key=f"delete_{user['id']}", type="secondary"):
                        if confirm_action(f"delete_{user['id']}", "Click delete again to confirm"):
                            try:
                                api.delete_user(user['id'])
                                show_success(f"Deleted user {user['name']}")
                                st.rerun()
                            except APIError as e:
                                show_error(f"Failed to delete: {e}")
                
                # Edit form
                if st.session_state.get(f"editing_{user['id']}", False):
                    st.markdown("---")
                    st.markdown("### Edit User")
                    edit_user_form(user)
                    
    except APIError as e:
        show_error(f"Failed to load users: {e}")


def edit_user_form(user: dict):
    """Form to edit user details"""
    with st.form(key=f"edit_form_{user['id']}"):
        new_name = st.text_input("Name", value=user['name'])
        
        # Zone selection
        try:
            all_zones = api.get_zones(limit=config.display.max_zones_per_page)
            zone_options = {z['zone_id']: f"{z['zone_name']} ({z['zone_id']})" 
                          for z in all_zones}
            
            current_zone_ids = [z['zone_id'] for z in user.get('zones', [])]
            selected_zones = st.multiselect(
                "Assigned Zones",
                options=list(zone_options.keys()),
                default=current_zone_ids,
                format_func=lambda x: zone_options[x]
            )
        except APIError as e:
            show_error(f"Failed to load zones: {e}")
            selected_zones = []
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Save Changes", type="primary")
        with col2:
            cancel = st.form_submit_button("❌ Cancel")
        
        if submit:
            try:
                api.update_user(user['id'], name=new_name, zone_ids=selected_zones)
                show_success(f"Updated user {new_name}")
                del st.session_state[f"editing_{user['id']}"]
                st.rerun()
            except APIError as e:
                show_error(f"Failed to update: {e}")
        
        if cancel:
            del st.session_state[f"editing_{user['id']}"]
            st.rerun()


def create_user_tab():
    """Form to create new user"""
    st.subheader("Create New User")
    
    with st.form(key="create_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            global_id = st.number_input("Global ID", min_value=1, step=1, 
                                       help="Unique identifier for the user")
            name = st.text_input("User Name", help="Full name of the user")
        
        with col2:
            # Zone selection
            try:
                all_zones = api.get_zones(limit=config.display.max_zones_per_page)
                if all_zones:
                    zone_options = {z['zone_id']: f"{z['zone_name']} ({z['zone_id']})" 
                                  for z in all_zones}
                    selected_zones = st.multiselect(
                        "Assign Zones (optional)",
                        options=list(zone_options.keys()),
                        format_func=lambda x: zone_options[x]
                    )
                else:
                    show_info("No zones available. Create zones first.")
                    selected_zones = []
            except APIError as e:
                show_error(f"Failed to load zones: {e}")
                selected_zones = []
        
        submit = st.form_submit_button("➕ Create User", type="primary")
        
        if submit:
            if not name:
                show_error("Please provide a user name")
            else:
                try:
                    new_user = api.create_user(
                        global_id=global_id,
                        name=name,
                        zone_ids=selected_zones
                    )
                    show_success(f"Created user: {new_user['name']} (ID: {new_user['id']})")
                    st.balloons()
                except APIError as e:
                    show_error(f"Failed to create user: {e}")


def search_users_tab():
    """Search and filter users"""
    st.subheader("Search Users")
    
    search_query = st.text_input("🔍 Search by name or ID", placeholder="Enter user name or ID...")
    
    if search_query:
        try:
            users = api.get_users(limit=config.display.max_users_per_page)
            
            # Filter users
            filtered_users = [
                u for u in users
                if search_query.lower() in u['name'].lower()
                or search_query in str(u['id'])
                or search_query in str(u['global_id'])
            ]
            
            if filtered_users:
                show_success(f"Found {len(filtered_users)} matching users")
                
                # Display as table
                df = pd.DataFrame([
                    {
                        'ID': u['id'],
                        'Global ID': u['global_id'],
                        'Name': u['name'],
                        'Zones': len(u.get('zones', [])),
                        'Created': u['created_at'][:10]
                    }
                    for u in filtered_users
                ])
                
                st.dataframe(df, use_container_width=True)
                
                # Detailed view
                st.markdown("---")
                for user in filtered_users:
                    with st.expander(f"Details: {user['name']}"):
                        st.json(user)
            else:
                show_info("No users found matching your search")
                
        except APIError as e:
            show_error(f"Search failed: {e}")


if __name__ == "__main__":
    main()
