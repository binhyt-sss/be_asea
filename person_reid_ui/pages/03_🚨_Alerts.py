"""
Real-time Alerts & Violation Tracking Page
Display Kafka messages, violation logs, and tracking statistics
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
from datetime import datetime, timedelta
import time

# Page configuration
st.set_page_config(
    page_title="Alerts & Violations - Person ReID",
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
    .violation-card {
        background-color: #ffebee;
        padding: 1.25rem;
        border-radius: 0.75rem;
        margin-bottom: 1rem;
        border-left: 5px solid #f44336;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .violation-card-warning {
        border-left-color: #ff9800;
        background-color: #fff3e0;
    }
    .violation-card-entered {
        border-left-color: #2196f3;
        background-color: #e3f2fd;
    }
    .violation-card-ongoing {
        border-left-color: #9c27b0;
        background-color: #f3e5f5;
    }
    .status-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 1.5rem;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .status-violation { background-color: #f44336; color: white; }
    .status-warning { background-color: #ff9800; color: white; }
    .status-entered { background-color: #2196f3; color: white; }
    .status-ongoing { background-color: #9c27b0; color: white; }
    .status-authorized { background-color: #4caf50; color: white; }

    .metric-card-alert {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value-alert {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .metric-label-alert {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)


def format_violation_card(violation: dict, show_status: str = 'VIOLATION') -> str:
    """Format violation as HTML card"""
    be_status = violation.get('be_status', show_status)

    # Determine card style based on status
    card_classes = {
        'ENTERED': 'violation-card violation-card-entered',
        'WARNING': 'violation-card violation-card-warning',
        'VIOLATION': 'violation-card',
        'VIOLATION_ONGOING': 'violation-card violation-card-ongoing'
    }

    badge_classes = {
        'ENTERED': 'status-badge status-entered',
        'WARNING': 'status-badge status-warning',
        'VIOLATION': 'status-badge status-violation',
        'VIOLATION_ONGOING': 'status-badge status-ongoing'
    }

    card_class = card_classes.get(be_status, 'violation-card')
    badge_class = badge_classes.get(be_status, 'status-badge status-violation')

    # Format timestamp
    timestamp_str = 'N/A'
    if 'created_at' in violation:
        timestamp_str = violation['created_at'][:19].replace('T', ' ')
    elif 'start_time' in violation:
        timestamp_str = violation['start_time'][:19].replace('T', ' ')

    user_name = violation.get('user_name', 'Unknown')
    zone_name = violation.get('zone_name', 'Unknown')
    duration = violation.get('duration', violation.get('_violation_duration', violation.get('_tracking_duration', 0)))
    threshold = violation.get('threshold', violation.get('_threshold', 0))

    # Additional info based on status
    extra_info = ""
    if be_status == 'WARNING':
        time_remaining = violation.get('_time_remaining', 0)
        extra_info = f"<div style='margin-top: 0.5rem; color: #ff9800;'>⏱️ Time remaining: {time_remaining:.1f}s</div>"
    elif be_status in ['VIOLATION', 'VIOLATION_ONGOING']:
        extra_info = f"<div style='margin-top: 0.5rem; color: #f44336;'>⚠️ Exceeded threshold by {duration - threshold:.1f}s</div>"

    return f"""
    <div class="{card_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span class="{badge_class}">{be_status}</span>
                <strong style="margin-left: 1rem; font-size: 1.1rem;">👤 {user_name}</strong>
                <span style="margin-left: 1rem;">📍 {zone_name}</span>
            </div>
            <div style="color: #666; font-size: 0.95rem;">
                🕐 {timestamp_str}
            </div>
        </div>
        <div style="margin-top: 0.75rem; font-size: 0.95rem; color: #555;">
            ⏱️ Duration: <strong>{duration:.1f}s</strong> |
            🎯 Threshold: <strong>{threshold}s</strong>
        </div>
        {extra_info}
    </div>
    """


def main():
    st.title("🚨 Real-time Alerts & Violation Tracking")
    st.markdown("---")

    # Check API connection
    try:
        health = api.health_check()
        tracking_info = health.get('tracking', {})
        redis_connected = tracking_info.get('redis_connected', False)

        if not redis_connected:
            st.warning("⚠️ Redis not connected. Violation tracking may not work properly.")
    except APIError as e:
        show_error(f"Cannot connect to API server: {e}")
        st.info(f"Please ensure the backend is running at {config.api.base_url}")
        return

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "🔴 Live Tracking",
        "📜 Violation History",
        "⚙️ Settings"
    ])

    with tab1:
        dashboard_tab()

    with tab2:
        live_tracking_tab()

    with tab3:
        violation_history_tab()

    with tab4:
        settings_tab()


def dashboard_tab():
    """Dashboard with overview statistics"""
    st.subheader("📊 Violation Tracking Dashboard")

    try:
        # Get violation summary
        summary = api.get_violation_summary()
        health = api.health_check()
        tracking_stats = health.get('tracking', {}).get('stats', {})

        # Top metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card-alert" style="background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);">
                <div class="metric-value-alert">{summary.get('total_violations', 0)}</div>
                <div class="metric-label-alert">Total Violations</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            avg_duration = summary.get('average_duration', 0)
            st.markdown(f"""
            <div class="metric-card-alert" style="background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);">
                <div class="metric-value-alert">{avg_duration:.1f}s</div>
                <div class="metric-label-alert">Avg Duration</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card-alert" style="background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);">
                <div class="metric-value-alert">{tracking_stats.get('messages_processed', 0)}</div>
                <div class="metric-label-alert">Messages Processed</div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card-alert" style="background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);">
                <div class="metric-value-alert">{tracking_stats.get('zone_cache_size', 0)}</div>
                <div class="metric-label-alert">Cached Zones</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 👥 Top Violating Users")
            top_users = summary.get('top_users', [])
            if top_users:
                df_users = pd.DataFrame(top_users)
                fig = px.bar(
                    df_users,
                    x='violation_count',
                    y='user_name',
                    orientation='h',
                    title='Top 10 Users by Violations',
                    color='violation_count',
                    color_continuous_scale='Reds'
                )
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No violation data available yet")

        with col2:
            st.markdown("### 🗺️ Top Zones")
            top_zones = summary.get('top_zones', [])
            if top_zones:
                df_zones = pd.DataFrame(top_zones)
                fig = px.pie(
                    df_zones,
                    values='violation_count',
                    names='zone_name',
                    title='Violations by Zone',
                    color_discrete_sequence=px.colors.sequential.RdBu
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No violation data available yet")

        st.markdown("---")

        # Real-time stats
        st.markdown("### 📈 Real-time Tracking Statistics")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Violations Detected", tracking_stats.get('violations_detected', 0))
        with col2:
            st.metric("Warnings Issued", tracking_stats.get('warnings_issued', 0))
        with col3:
            st.metric("Errors", tracking_stats.get('errors', 0))

    except Exception as e:
        show_error(f"Failed to load dashboard: {e}")


def live_tracking_tab():
    """Live message tracking with status indicators"""
    st.subheader("🔴 Live Message Tracking")

    # Controls
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    with col2:
        limit = st.selectbox("Show", [10, 25, 50, 100], index=1, key="live_limit")

    try:
        response = api.get_recent_messages(limit=limit)
        messages = response.get('messages', [])

        if not messages:
            st.info("No messages received yet. Waiting for tracking data...")
        else:
            st.success(f"Showing {len(messages)} most recent messages")

            # Status filter
            status_filter = st.multiselect(
                "Filter by Status",
                ["ENTERED", "WARNING", "VIOLATION", "VIOLATION_ONGOING"],
                default=["VIOLATION", "WARNING"],
                key="live_status_filter"
            )

            # Filter messages
            filtered = [
                m for m in messages
                if m.get('be_status') in status_filter
            ]

            if not filtered:
                st.warning("No messages match the selected filters")
            else:
                # Display messages
                for msg in reversed(filtered):  # Show newest first
                    be_status = msg.get('be_status', 'UNKNOWN')
                    st.markdown(format_violation_card(msg, be_status), unsafe_allow_html=True)

        # Auto refresh
        if config.features.auto_refresh if config else False:
            refresh_interval = config.features.auto_refresh_interval if config else 5
            st.info(f"Auto-refreshing in {refresh_interval} seconds...")
            time.sleep(refresh_interval)
            st.rerun()

    except Exception as e:
        show_error(f"Failed to load messages: {e}")


def violation_history_tab():
    """Violation history from database"""
    st.subheader("📜 Violation History (Database)")

    # Filters
    with st.expander("🔍 Filters", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            user_filter = st.text_input("User ID")
        with col2:
            zone_filter = st.text_input("Zone ID")
        with col3:
            limit = st.number_input("Limit", min_value=10, max_value=500, value=50)

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=7))
        with col2:
            end_date = st.date_input("End Date", value=datetime.now())

    try:
        # Get violation logs
        logs_response = api.get_violation_logs(
            limit=limit,
            user_id=user_filter if user_filter else None,
            zone_id=zone_filter if zone_filter else None,
            start_date=start_date.isoformat() if start_date else None,
            end_date=end_date.isoformat() if end_date else None
        )

        violations = logs_response.get('violations', [])
        total = logs_response.get('total', 0)

        if not violations:
            st.info("No violation history found")
            return

        st.success(f"Found {len(violations)} violations (Total: {total})")

        # Statistics
        col1, col2, col3, col4 = st.columns(4)

        df = pd.DataFrame(violations)

        with col1:
            st.metric("Total Violations", len(df))
        with col2:
            avg_duration = df['duration'].mean() if 'duration' in df.columns else 0
            st.metric("Avg Duration", f"{avg_duration:.1f}s")
        with col3:
            unique_users = df['user_id'].nunique() if 'user_id' in df.columns else 0
            st.metric("Unique Users", unique_users)
        with col4:
            unique_zones = df['zone_id'].nunique() if 'zone_id' in df.columns else 0
            st.metric("Unique Zones", unique_zones)

        st.markdown("---")

        # Display violations
        for violation in violations:
            st.markdown(format_violation_card(violation), unsafe_allow_html=True)

        st.markdown("---")

        # Download option
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"violations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

    except Exception as e:
        show_error(f"Failed to load violation history: {e}")


def settings_tab():
    """Settings and configuration"""
    st.subheader("⚙️ Settings")

    st.markdown("### 🔔 Alert Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.checkbox("Auto Refresh", value=config.features.auto_refresh if config else True)
        st.number_input("Refresh Interval (seconds)", min_value=1, max_value=60, value=5)
        st.checkbox("Desktop Notifications", value=False, disabled=True)

    with col2:
        st.checkbox("Sound Alerts", value=False, disabled=True)
        st.selectbox("Alert Priority", ["All", "High Only", "Critical Only"])
        st.checkbox("Email Notifications", value=False, disabled=True)

    st.markdown("---")

    st.markdown("### 🎨 Display Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.selectbox("Theme", ["Light", "Dark", "Auto"])
        st.number_input("Messages Per Page", min_value=10, max_value=200, value=50)

    with col2:
        st.multiselect(
            "Default Status Filter",
            ["ENTERED", "WARNING", "VIOLATION", "VIOLATION_ONGOING"],
            default=["VIOLATION", "WARNING"]
        )

    st.markdown("---")

    if st.button("💾 Save Settings", disabled=True):
        st.info("Settings saved! (Coming soon)")


if __name__ == "__main__":
    main()
