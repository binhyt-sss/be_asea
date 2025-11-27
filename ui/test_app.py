"""
Streamlit Testing UI for Async Database API
Comprehensive interface for testing all CRUD operations with async SQLAlchemy backend
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
import json

# API Configuration
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Person ReID Database Testing",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stAlert > div {
        padding: 1rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health() -> Dict:
    """Check API health status"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_all_users() -> List[Dict]:
    """Get all users"""
    try:
        response = requests.get(f"{API_BASE_URL}/users")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching users: {e}")
        return []


def get_all_zones() -> List[Dict]:
    """Get all zones"""
    try:
        response = requests.get(f"{API_BASE_URL}/zones")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching zones: {e}")
        return []


def create_user(global_id: int, name: str, zone_id: Optional[str]) -> Dict:
    """Create a new user"""
    try:
        payload = {
            "global_id": global_id,
            "name": name,
            "zone_id": zone_id if zone_id else None
        }
        response = requests.post(f"{API_BASE_URL}/users", json=payload)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"success": False, "error": str(e)}


def update_user(user_id: int, name: Optional[str], zone_id: Optional[str]) -> Dict:
    """Update an existing user"""
    try:
        payload = {}
        if name:
            payload["name"] = name
        if zone_id:
            payload["zone_id"] = zone_id
        
        response = requests.put(f"{API_BASE_URL}/users/{user_id}", json=payload)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_user(user_id: int) -> Dict:
    """Delete a user"""
    try:
        response = requests.delete(f"{API_BASE_URL}/users/{user_id}")
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_zone(zone_id: str, zone_name: str, x1: float, y1: float, x2: float, y2: float,
                x3: float, y3: float, x4: float, y4: float) -> Dict:
    """Create a new working zone"""
    try:
        payload = {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "x1": x1, "y1": y1,
            "x2": x2, "y2": y2,
            "x3": x3, "y3": y3,
            "x4": x4, "y4": y4
        }
        response = requests.post(f"{API_BASE_URL}/zones", json=payload)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": e.response.json().get("detail", str(e))}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_stats() -> Dict:
    """Get statistics"""
    try:
        user_stats = requests.get(f"{API_BASE_URL}/stats/users").json()
        zone_stats = requests.get(f"{API_BASE_URL}/stats/zones").json()
        cache_stats = requests.get(f"{API_BASE_URL}/cache/stats").json()
        
        return {
            "users": user_stats,
            "zones": zone_stats,
            "cache": cache_stats
        }
    except Exception as e:
        st.error(f"Error fetching stats: {e}")
        return {}


# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title("🚀 Person ReID API Testing")
st.sidebar.markdown("---")

# Health Check
health = check_api_health()
if health.get("status") == "healthy":
    st.sidebar.success("✅ API Connected")
    st.sidebar.json(health, expanded=False)
else:
    st.sidebar.error("❌ API Disconnected")
    st.sidebar.error(health.get("message", "Unknown error"))

st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "👥 Users", "🏢 Zones", "📈 Statistics", "⚙️ Settings"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Async Backend**\n"
    "- SQLAlchemy 2.0\n"
    "- asyncpg driver\n"
    "- Dependency Injection\n"
    "- Connection Pooling"
)


# ============================================================================
# DASHBOARD PAGE
# ============================================================================

if page == "📊 Dashboard":
    st.title("📊 Dashboard Overview")
    
    # Fetch data
    users = get_all_users()
    zones = get_all_zones()
    stats = get_stats()
    
    # Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", len(users))
    
    with col2:
        st.metric("Total Zones", len(zones))
    
    with col3:
        redis_keys = stats.get("cache", {}).get("total_keys", 0)
        st.metric("Redis Keys", redis_keys)
    
    with col4:
        redis_memory = stats.get("cache", {}).get("memory_used", "N/A")
        st.metric("Redis Memory", redis_memory)
    
    st.markdown("---")
    
    # Users Table
    st.subheader("👥 Recent Users")
    if users:
        df_users = pd.DataFrame(users)
        st.dataframe(df_users, use_container_width=True, height=300)
    else:
        st.info("No users in database. Create some in the Users page!")
    
    # Zones Table
    st.subheader("🏢 Working Zones")
    if zones:
        df_zones = pd.DataFrame(zones)
        st.dataframe(df_zones, use_container_width=True, height=300)
    else:
        st.info("No zones in database. Create some in the Zones page!")


# ============================================================================
# USERS PAGE
# ============================================================================

elif page == "👥 Users":
    st.title("👥 User Management")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 View All", "➕ Create", "✏️ Update", "🗑️ Delete"])
    
    # TAB 1: View All Users
    with tab1:
        st.subheader("All Users")
        
        if st.button("🔄 Refresh Users", key="refresh_users"):
            st.rerun()
        
        users = get_all_users()
        
        if users:
            df = pd.DataFrame(users)
            st.dataframe(df, use_container_width=True, height=500)
            
            # Download CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name="users.csv",
                mime="text/csv"
            )
        else:
            st.info("No users found. Create your first user!")
    
    # TAB 2: Create User
    with tab2:
        st.subheader("Create New User")
        
        zones = get_all_zones()
        zone_options = ["None"] + [z["zone_id"] for z in zones]
        
        with st.form("create_user_form"):
            global_id = st.number_input("Global ID", min_value=1, step=1)
            name = st.text_input("Name", placeholder="Enter user name")
            zone_id = st.selectbox("Assign to Zone", zone_options)
            
            submitted = st.form_submit_button("✅ Create User")
            
            if submitted:
                if not name:
                    st.error("Name is required!")
                else:
                    result = create_user(
                        global_id=global_id,
                        name=name,
                        zone_id=None if zone_id == "None" else zone_id
                    )
                    
                    if result["success"]:
                        st.success(f"✅ User created successfully!")
                        st.json(result["data"])
                    else:
                        st.error(f"❌ Error: {result['error']}")
    
    # TAB 3: Update User
    with tab3:
        st.subheader("Update Existing User")
        
        users = get_all_users()
        
        if users:
            user_options = {f"{u['id']} - {u['name']} (Global ID: {u['global_id']})": u['id'] for u in users}
            
            with st.form("update_user_form"):
                selected_user = st.selectbox("Select User", list(user_options.keys()))
                user_id = user_options[selected_user]
                
                new_name = st.text_input("New Name (leave empty to keep current)")
                
                zones = get_all_zones()
                zone_options = ["Keep Current"] + [z["zone_id"] for z in zones]
                new_zone = st.selectbox("New Zone", zone_options)
                
                submitted = st.form_submit_button("💾 Update User")
                
                if submitted:
                    result = update_user(
                        user_id=user_id,
                        name=new_name if new_name else None,
                        zone_id=None if new_zone == "Keep Current" else new_zone
                    )
                    
                    if result["success"]:
                        st.success("✅ User updated successfully!")
                        st.json(result["data"])
                    else:
                        st.error(f"❌ Error: {result['error']}")
        else:
            st.info("No users available to update.")
    
    # TAB 4: Delete User
    with tab4:
        st.subheader("Delete User")
        st.warning("⚠️ This action cannot be undone!")
        
        users = get_all_users()
        
        if users:
            user_options = {f"{u['id']} - {u['name']} (Global ID: {u['global_id']})": u['id'] for u in users}
            
            with st.form("delete_user_form"):
                selected_user = st.selectbox("Select User to Delete", list(user_options.keys()))
                user_id = user_options[selected_user]
                
                confirm = st.checkbox("I confirm I want to delete this user")
                submitted = st.form_submit_button("🗑️ Delete User", type="primary")
                
                if submitted:
                    if not confirm:
                        st.error("Please confirm deletion!")
                    else:
                        result = delete_user(user_id)
                        
                        if result["success"]:
                            st.success("✅ User deleted successfully!")
                        else:
                            st.error(f"❌ Error: {result['error']}")
        else:
            st.info("No users available to delete.")


# ============================================================================
# ZONES PAGE
# ============================================================================

elif page == "🏢 Zones":
    st.title("🏢 Working Zone Management")
    
    tab1, tab2 = st.tabs(["📋 View All", "➕ Create"])
    
    with tab1:
        st.subheader("All Working Zones")
        
        if st.button("🔄 Refresh Zones", key="refresh_zones"):
            st.rerun()
        
        zones = get_all_zones()
        
        if zones:
            df = pd.DataFrame(zones)
            st.dataframe(df, use_container_width=True, height=500)
            
            # Visualize zone polygons
            st.subheader("📍 Zone Visualization")
            
            for zone in zones:
                with st.expander(f"Zone: {zone['zone_name']} ({zone['zone_id']})"):
                    # Create polygon plot
                    x_coords = [zone['x1'], zone['x2'], zone['x3'], zone['x4'], zone['x1']]
                    y_coords = [zone['y1'], zone['y2'], zone['y3'], zone['y4'], zone['y1']]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=x_coords,
                        y=y_coords,
                        fill="toself",
                        name=zone['zone_name'],
                        mode='lines+markers'
                    ))
                    
                    fig.update_layout(
                        title=f"Zone: {zone['zone_name']}",
                        xaxis_title="X Coordinate",
                        yaxis_title="Y Coordinate",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No zones found. Create your first zone!")
    
    with tab2:
        st.subheader("Create New Working Zone")
        
        with st.form("create_zone_form"):
            zone_id = st.text_input("Zone ID", placeholder="e.g., ZONE_001")
            zone_name = st.text_input("Zone Name", placeholder="e.g., Assembly Area")
            
            st.markdown("**Polygon Coordinates (4 points)**")
            
            col1, col2 = st.columns(2)
            with col1:
                x1 = st.number_input("X1", value=0.0, format="%.2f")
                y1 = st.number_input("Y1", value=0.0, format="%.2f")
                x2 = st.number_input("X2", value=100.0, format="%.2f")
                y2 = st.number_input("Y2", value=0.0, format="%.2f")
            
            with col2:
                x3 = st.number_input("X3", value=100.0, format="%.2f")
                y3 = st.number_input("Y3", value=100.0, format="%.2f")
                x4 = st.number_input("X4", value=0.0, format="%.2f")
                y4 = st.number_input("Y4", value=100.0, format="%.2f")
            
            submitted = st.form_submit_button("✅ Create Zone")
            
            if submitted:
                if not zone_id or not zone_name:
                    st.error("Zone ID and Name are required!")
                else:
                    result = create_zone(
                        zone_id=zone_id,
                        zone_name=zone_name,
                        x1=x1, y1=y1, x2=x2, y2=y2,
                        x3=x3, y3=y3, x4=x4, y4=y4
                    )
                    
                    if result["success"]:
                        st.success("✅ Zone created successfully!")
                        st.json(result["data"])
                    else:
                        st.error(f"❌ Error: {result['error']}")


# ============================================================================
# STATISTICS PAGE
# ============================================================================

elif page == "📈 Statistics":
    st.title("📈 Statistics & Analytics")
    
    stats = get_stats()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👥 User Statistics")
        if stats.get("users"):
            st.metric("Total Users", stats["users"].get("total_users", 0))
    
    with col2:
        st.subheader("🏢 Zone Statistics")
        if stats.get("zones"):
            st.metric("Total Zones", stats["zones"].get("total_zones", 0))
    
    # Zone User Distribution
    if stats.get("zones") and stats["zones"].get("zones"):
        st.subheader("👥 Users per Zone")
        
        zone_data = stats["zones"]["zones"]
        df_zone_stats = pd.DataFrame(zone_data)
        
        fig = px.bar(
            df_zone_stats,
            x="zone_name",
            y="user_count",
            title="User Distribution by Zone",
            labels={"zone_name": "Zone Name", "user_count": "Number of Users"}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Redis Cache Stats
    st.subheader("💾 Redis Cache Statistics")
    if stats.get("cache"):
        cache_info = stats["cache"]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Keys", cache_info.get("total_keys", 0))
        
        with col2:
            st.metric("Memory Used", cache_info.get("memory_used", "N/A"))
        
        with col3:
            st.metric("Connected Clients", cache_info.get("connected_clients", 0))
        
        with col4:
            uptime = cache_info.get("uptime_seconds", 0)
            st.metric("Uptime (hours)", f"{uptime / 3600:.1f}")


# ============================================================================
# SETTINGS PAGE
# ============================================================================

elif page == "⚙️ Settings":
    st.title("⚙️ Settings & Configuration")
    
    st.subheader("🔧 API Configuration")
    st.code(f"API Base URL: {API_BASE_URL}", language="text")
    
    st.markdown("---")
    
    st.subheader("🧹 Cache Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clear Users Dict Cache", type="primary"):
            try:
                response = requests.post(f"{API_BASE_URL}/cache/invalidate/users-dict")
                if response.status_code == 200:
                    st.success("✅ Users dict cache cleared!")
                else:
                    st.error("❌ Failed to clear cache")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        if st.button("🗑️ Clear All Cache", type="secondary"):
            confirm = st.checkbox("Confirm clear all cache")
            if confirm:
                try:
                    response = requests.post(f"{API_BASE_URL}/cache/clear")
                    if response.status_code == 200:
                        st.success("✅ All cache cleared!")
                    else:
                        st.error("❌ Failed to clear cache")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.markdown("---")
    
    st.subheader("📚 API Documentation")
    st.markdown(f"[Open Swagger UI]({API_BASE_URL}/docs)")
    st.markdown(f"[Open ReDoc]({API_BASE_URL}/redoc)")
