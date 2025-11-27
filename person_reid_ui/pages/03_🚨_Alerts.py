"""
Real-time Alerts Page
Display Kafka messages and alerts with filtering
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from api_client import get_api_client, APIError
from utils import show_error, show_success, load_custom_css, format_datetime
from config import get_config
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# Page configuration
st.set_page_config(
    page_title="Alerts - Person ReID",
    page_icon="🚨",
    layout="wide"
)

# Load custom CSS
load_custom_css()

# Get configuration and API client from session state
config = st.session_state.get('config')
api = st.session_state.get('api_client')

if not config or not api:
    st.error("⚠️ Configuration not loaded. Please return to Home page.")
    st.stop()

# Custom CSS
st.markdown("""
<style>
    .alert-card {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        border-left: 4px solid #ff9800;
    }
    .alert-violation {
        border-left-color: #f44336 !important;
        background-color: #ffebee;
    }
    .alert-authorized {
        border-left-color: #4caf50 !important;
        background-color: #e8f5e9;
    }
    .alert-incomplete {
        border-left-color: #ff9800 !important;
        background-color: #fff3e0;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        font-weight: 600;
    }
    .status-violation {
        background-color: #f44336;
        color: white;
    }
    .status-authorized {
        background-color: #4caf50;
        color: white;
    }
    .status-incomplete {
        background-color: #ff9800;
        color: white;
    }
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: #4caf50;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }
</style>
""", unsafe_allow_html=True)


def format_alert_card(msg: dict) -> str:
    """Format alert message as HTML card"""
    status = msg.get('status', 'unknown')
    card_class = f"alert-card alert-{status}"
    badge_class = f"status-badge status-{status}"
    
    timestamp = msg.get('timestamp', '')
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            timestamp_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            timestamp_str = timestamp[:19]
    else:
        timestamp_str = 'N/A'
    
    user_name = msg.get('user_name', 'Unknown')
    zone_name = msg.get('zone_name', 'Unknown')
    camera_id = msg.get('camera_id', 'N/A')
    iop = msg.get('iop', 0)
    threshold = msg.get('threshold', 0)
    
    return f"""
    <div class="{card_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="{badge_class}">{status.upper()}</span>
                <strong style="margin-left: 1rem;">👤 {user_name}</strong>
                <span style="margin-left: 1rem;">📍 {zone_name}</span>
                <span style="margin-left: 1rem;">📷 Camera {camera_id}</span>
            </div>
            <div style="color: #666; font-size: 0.875rem;">
                🕐 {timestamp_str}
            </div>
        </div>
        <div style="margin-top: 0.5rem; font-size: 0.875rem; color: #666;">
            IOP: {iop:.3f} | Threshold: {threshold:.3f}
        </div>
    </div>
    """


def main():
    st.title("🚨 Real-time Alerts")
    st.markdown("---")
    
    # Check API connection
    try:
        api.health_check()
    except APIError as e:
        show_error(f"Cannot connect to API server: {e}")
        st.info(f"Please ensure the backend is running at {config.api.base_url}")
        return
    
    # Live indicator
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        st.markdown('<span class="live-indicator"></span> <strong>LIVE</strong>', unsafe_allow_html=True)
    with col3:
        auto_refresh = st.checkbox("Auto Refresh", value=config.features.auto_refresh if config else True)
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🔴 Live Feed", "📊 Message History", "⚙️ Filters"])
    
    with tab1:
        live_feed_tab(auto_refresh)
    
    with tab2:
        message_history_tab()
    
    with tab3:
        filters_tab()


def live_feed_tab(auto_refresh: bool):
    """Display live Kafka messages"""
    st.subheader("Live Alert Feed")
    
    # Controls
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    with col2:
        limit = st.selectbox("Show", [10, 25, 50, 100], index=1, key="live_limit")
    
    # Fetch recent messages
    try:
        response = api.get_recent_messages(limit=limit)
        messages = response.get('messages', [])
        count = response.get('count', 0)
        
        if not messages:
            st.info("No messages received yet. Waiting for Kafka alerts...")
            st.markdown("""
            **How to test:**
            1. Ensure Kafka is running
            2. Backend service is consuming messages
            3. Send test messages using the publisher script
            """)
        else:
            st.success(f"Displaying {count} most recent messages")
            
            # Status filter
            status_filter = st.multiselect(
                "Filter by Status",
                ["violation", "authorized", "incomplete"],
                default=["violation", "authorized", "incomplete"],
                key="live_status_filter"
            )
            
            # Filter messages
            filtered = [m for m in messages if m.get('status') in status_filter]
            
            if not filtered:
                st.warning("No messages match the selected filters")
            else:
                # Display messages
                for msg in reversed(filtered):  # Show newest first
                    st.markdown(format_alert_card(msg), unsafe_allow_html=True)
        
        # Auto refresh
        if auto_refresh and messages:
            refresh_interval = config.features.auto_refresh_interval if config else 5
            st.info(f"Auto-refreshing in {refresh_interval} seconds...")
            time.sleep(refresh_interval)
            st.rerun()
            
    except Exception as e:
        st.error(f"Failed to load messages: {e}")


def message_history_tab():
    """Display message history with analytics"""
    st.subheader("Message History & Analytics")
    
    # Controls
    col1, col2 = st.columns([1, 5])
    with col1:
        limit = st.number_input("Messages", min_value=10, max_value=1000, value=100, step=10)
    
    try:
        response = api.get_recent_messages(limit=limit)
        messages = response.get('messages', [])
        
        if not messages:
            st.info("No message history available")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(messages)
        
        # Statistics
        st.markdown("### 📊 Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Messages", len(df))
        
        with col2:
            violations = len(df[df['status'] == 'violation']) if 'status' in df.columns else 0
            st.metric("Violations", violations, delta=f"{violations/len(df)*100:.1f}%")
        
        with col3:
            authorized = len(df[df['status'] == 'authorized']) if 'status' in df.columns else 0
            st.metric("Authorized", authorized, delta=f"{authorized/len(df)*100:.1f}%")
        
        with col4:
            if 'iop' in df.columns:
                avg_iop = df['iop'].mean()
                st.metric("Avg IOP", f"{avg_iop:.3f}")
            else:
                st.metric("Avg IOP", "N/A")
        
        st.markdown("---")
        
        # Status distribution
        if 'status' in df.columns:
            st.markdown("### Status Distribution")
            status_counts = df['status'].value_counts()
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.dataframe(status_counts.to_frame('Count'), use_container_width=True)
            
            with col2:
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Alert Status Distribution",
                    color=status_counts.index,
                    color_discrete_map={
                        'violation': '#f44336',
                        'authorized': '#4caf50',
                        'incomplete': '#ff9800'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Top users and zones
        col1, col2 = st.columns(2)
        
        with col1:
            if 'user_name' in df.columns:
                st.markdown("### 👥 Top Users")
                top_users = df['user_name'].value_counts().head(10)
                st.dataframe(top_users.to_frame('Alerts'), use_container_width=True)
        
        with col2:
            if 'zone_name' in df.columns:
                st.markdown("### 🗺️ Top Zones")
                top_zones = df['zone_name'].value_counts().head(10)
                st.dataframe(top_zones.to_frame('Alerts'), use_container_width=True)
        
        st.markdown("---")
        
        # Raw data table
        st.markdown("### 📋 Raw Data")
        
        # Select columns to display
        display_cols = ['timestamp', 'user_name', 'zone_name', 'camera_id', 'status', 'iop', 'threshold']
        available_cols = [col for col in display_cols if col in df.columns]
        
        if available_cols:
            display_df = df[available_cols].copy()
            
            # Format timestamp
            if 'timestamp' in display_df.columns:
                display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            st.dataframe(display_df, use_container_width=True, height=400)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.dataframe(df, use_container_width=True, height=400)
            
    except Exception as e:
        st.error(f"Failed to load history: {e}")


def filters_tab():
    """Configure filters and settings"""
    st.subheader("Filter Settings")
    
    st.markdown("### 🔍 Message Filters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Status Filter")
        st.checkbox("Show Violations", value=True, key="filter_violation")
        st.checkbox("Show Authorized", value=True, key="filter_authorized")
        st.checkbox("Show Incomplete", value=True, key="filter_incomplete")
    
    with col2:
        st.markdown("#### IOP Threshold")
        iop_min = st.slider("Minimum IOP", 0.0, 1.0, 0.0, 0.01)
        iop_max = st.slider("Maximum IOP", 0.0, 1.0, 1.0, 0.01)
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Display Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.number_input("Auto-refresh Interval (seconds)", min_value=1, max_value=60, value=5)
        st.checkbox("Play Sound on Alert", value=False)
    
    with col2:
        st.selectbox("Alert Priority", ["All", "High", "Medium", "Low"])
        st.checkbox("Desktop Notifications", value=False)
    
    st.markdown("---")
    
    st.markdown("### 📧 Alert Rules")
    st.info("Configure custom alert rules (Coming soon)")
    
    with st.expander("Example: Email on Violation"):
        st.text_input("Email Address")
        st.selectbox("When", ["Any Violation", "Critical Only", "Repeated Violations"])
        st.button("Save Rule", disabled=True)


if __name__ == "__main__":
    main()
