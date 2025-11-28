"""
Statistics & Analytics Page
Visual analytics and reports for the Person ReID system
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from api_client import get_api_client, APIError
from utils import show_error, show_success, load_custom_css, get_color_scheme
from config import get_config
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Statistics - Person ReID",
    page_icon="📈",
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
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stat-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)


def main():
    st.title("📈 Statistics & Analytics")
    st.markdown("---")
    
    # Check API connection
    try:
        api.health_check()
    except APIError as e:
        show_error(f"Cannot connect to API server: {e}")
        st.info(f"Please ensure the backend is running at {config.api.base_url}")
        return
    
    # Tabs for different analytics
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "👥 User Analytics", 
        "🗺️ Zone Analytics",
        "🚨 Alert Analytics",
        "⚠️ Violations"
    ])
    
    with tab1:
        overview_tab()
    
    with tab2:
        user_analytics_tab()
    
    with tab3:
        zone_analytics_tab()
    
    with tab4:
        alert_analytics_tab()
    
    with tab5:
        violation_analytics_tab()


def overview_tab():
    """System overview with key metrics"""
    st.subheader("System Overview")
    
    try:
        # Fetch statistics
        user_stats = api.get_user_stats()
        zone_stats = api.get_zone_stats()
        recent_messages = api.get_recent_messages(limit=100)
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Total Users</div>
                <div class="stat-value">{user_stats.get('total_users', 0)}</div>
                <div class="stat-label">👥 Registered</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Total Zones</div>
                <div class="stat-value">{zone_stats.get('total_zones', 0)}</div>
                <div class="stat-label">🗺️ Active</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            message_count = recent_messages.get('count', 0)
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Recent Alerts</div>
                <div class="stat-value">{message_count}</div>
                <div class="stat-label">🚨 Last 100</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Calculate violation rate
            messages = recent_messages.get('messages', [])
            if messages:
                violations = sum(1 for m in messages if m.get('status') == 'violation')
                violation_rate = (violations / len(messages)) * 100
            else:
                violation_rate = 0
            
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Violation Rate</div>
                <div class="stat-value">{violation_rate:.1f}%</div>
                <div class="stat-label">📉 Rate</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # System health
        st.subheader("🔧 System Health")
        
        health = api.health_check()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            api_status = "✅ Healthy" if health.get('status') == 'healthy' else "❌ Unhealthy"
            st.metric("API Server", api_status)
            st.caption(f"Version: {health.get('version', 'Unknown')}")
        
        with col2:
            db_status = "✅ Connected" if health.get('database') else "❌ Disconnected"
            st.metric("Database", db_status)
            st.caption(f"{health.get('database', 'Unknown')}")
        
        with col3:
            kafka_status = "✅ Running" if health.get('kafka_running') else "⚠️ Stopped"
            st.metric("Kafka", kafka_status)
            st.caption(f"Messages: {health.get('messages_received', 0)}")
        
        st.markdown("---")
        
        # Quick insights
        st.subheader("💡 Quick Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Zone Utilization")
            zones_data = zone_stats.get('zones', [])
            if zones_data:
                df_zones = pd.DataFrame(zones_data)
                fig = px.bar(
                    df_zones,
                    x='zone_name',
                    y='user_count',
                    title="Users per Zone",
                    labels={'zone_name': 'Zone', 'user_count': 'User Count'},
                    color='user_count',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No zone data available")
        
        with col2:
            st.markdown("#### 🚨 Alert Timeline")
            if messages:
                df_messages = pd.DataFrame(messages)
                if 'timestamp' in df_messages.columns and 'status' in df_messages.columns:
                    df_messages['timestamp'] = pd.to_datetime(df_messages['timestamp'])
                    df_messages['hour'] = df_messages['timestamp'].dt.floor('H')
                    
                    hourly_counts = df_messages.groupby(['hour', 'status']).size().reset_index(name='count')
                    
                    fig = px.line(
                        hourly_counts,
                        x='hour',
                        y='count',
                        color='status',
                        title="Alerts Over Time",
                        labels={'hour': 'Time', 'count': 'Alert Count'},
                        color_discrete_map={
                            'violation': '#f44336',
                            'authorized': '#4caf50',
                            'incomplete': '#ff9800'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Insufficient data for timeline")
            else:
                st.info("No alert data available")
        
    except Exception as e:
        st.error(f"Failed to load overview: {e}")


def user_analytics_tab():
    """Detailed user analytics"""
    st.subheader("User Analytics")
    
    try:
        users = api.get_users(limit=1000)
        
        if not users:
            st.info("No users available for analysis")
            return
        
        # User statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Users", len(users))
        
        with col2:
            avg_zones = sum(len(u.get('zones', [])) for u in users) / len(users)
            st.metric("Avg Zones/User", f"{avg_zones:.1f}")
        
        with col3:
            users_with_zones = sum(1 for u in users if u.get('zones'))
            st.metric("Users with Zones", users_with_zones)
        
        st.markdown("---")
        
        # Zone assignment distribution
        st.markdown("### Zone Assignment Distribution")
        
        zone_counts = [len(u.get('zones', [])) for u in users]
        df_distribution = pd.DataFrame({
            'Zones': zone_counts
        })
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### Statistics")
            st.metric("Min Zones", min(zone_counts))
            st.metric("Max Zones", max(zone_counts))
            st.metric("Median Zones", f"{pd.Series(zone_counts).median():.1f}")
        
        with col2:
            fig = px.histogram(
                df_distribution,
                x='Zones',
                title="Distribution of Zone Assignments",
                labels={'Zones': 'Number of Zones', 'count': 'Number of Users'},
                nbins=20,
                color_discrete_sequence=['#1f77b4']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Top users by zone count
        st.markdown("### 👥 Top Users by Zone Assignment")
        
        user_data = [
            {
                'User': u['name'],
                'Global ID': u['global_id'],
                'Zones': len(u.get('zones', [])),
                'Zone Names': ', '.join([z['zone_name'] for z in u.get('zones', [])[:3]]) + 
                            ('...' if len(u.get('zones', [])) > 3 else '')
            }
            for u in users
        ]
        df_users = pd.DataFrame(user_data).sort_values('Zones', ascending=False).head(20)
        
        st.dataframe(df_users, use_container_width=True, height=400)
        
        st.markdown("---")
        
        # User activity over time
        st.markdown("### 📅 User Registration Timeline")
        
        df_users_full = pd.DataFrame(users)
        if 'created_at' in df_users_full.columns:
            df_users_full['created_at'] = pd.to_datetime(df_users_full['created_at'])
            df_users_full['date'] = df_users_full['created_at'].dt.date
            
            daily_registrations = df_users_full.groupby('date').size().reset_index(name='count')
            daily_registrations['cumulative'] = daily_registrations['count'].cumsum()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily_registrations['date'],
                y=daily_registrations['cumulative'],
                mode='lines+markers',
                name='Cumulative Users',
                line=dict(color='#1f77b4', width=3)
            ))
            
            fig.update_layout(
                title="User Growth Over Time",
                xaxis_title="Date",
                yaxis_title="Total Users",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to load user analytics: {e}")


def zone_analytics_tab():
    """Detailed zone analytics"""
    st.subheader("Zone Analytics")
    
    try:
        zone_stats = api.get_zone_stats()
        zones_data = zone_stats.get('zones', [])
        
        if not zones_data:
            st.info("No zones available for analysis")
            return
        
        df_zones = pd.DataFrame(zones_data)
        
        # Zone statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Zones", len(df_zones))
        
        with col2:
            total_assignments = df_zones['user_count'].sum()
            st.metric("Total Assignments", total_assignments)
        
        with col3:
            avg_users = df_zones['user_count'].mean()
            st.metric("Avg Users/Zone", f"{avg_users:.1f}")
        
        st.markdown("---")
        
        # Zone utilization
        st.markdown("### 🗺️ Zone Utilization")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                df_zones.sort_values('user_count', ascending=True),
                y='zone_name',
                x='user_count',
                orientation='h',
                title="Users per Zone",
                labels={'zone_name': 'Zone', 'user_count': 'Number of Users'},
                color='user_count',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=max(400, len(df_zones) * 30))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Top Zones")
            top_zones = df_zones.nlargest(10, 'user_count')[['zone_name', 'user_count']]
            top_zones.columns = ['Zone', 'Users']
            st.dataframe(top_zones, use_container_width=True)
        
        st.markdown("---")
        
        # Zone distribution
        st.markdown("### 📊 Zone Distribution")
        
        # Pie chart
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                df_zones,
                values='user_count',
                names='zone_name',
                title="User Distribution Across Zones",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Zone capacity analysis
            st.markdown("#### Zone Capacity Analysis")
            
            # Categorize zones
            df_zones['category'] = pd.cut(
                df_zones['user_count'],
                bins=[-1, 0, 5, 10, float('inf')],
                labels=['Empty', 'Low (1-5)', 'Medium (6-10)', 'High (>10)']
            )
            
            category_counts = df_zones['category'].value_counts()
            
            fig = px.bar(
                x=category_counts.index,
                y=category_counts.values,
                title="Zones by Capacity",
                labels={'x': 'Capacity', 'y': 'Number of Zones'},
                color=category_counts.values,
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Detailed zone table
        st.markdown("### 📋 Detailed Zone Information")
        
        display_df = df_zones[['zone_id', 'zone_name', 'user_count']].copy()
        display_df.columns = ['Zone ID', 'Zone Name', 'User Count']
        display_df = display_df.sort_values('User Count', ascending=False)
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
    except Exception as e:
        st.error(f"Failed to load zone analytics: {e}")


def alert_analytics_tab():
    """Alert analytics and trends"""
    st.subheader("Alert Analytics")
    
    try:
        # Fetch recent messages
        response = api.get_recent_messages(limit=500)
        messages = response.get('messages', [])
        
        if not messages:
            st.info("No alert data available")
            return
        
        df = pd.DataFrame(messages)
        
        # Alert statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Alerts", len(df))
        
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
        st.markdown("### 📊 Alert Status Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'status' in df.columns:
                status_counts = df['status'].value_counts()
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Status Distribution",
                    color=status_counts.index,
                    color_discrete_map={
                        'violation': '#f44336',
                        'authorized': '#4caf50',
                        'incomplete': '#ff9800'
                    },
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'status' in df.columns:
                st.markdown("#### Status Breakdown")
                for status, count in status_counts.items():
                    percentage = (count / len(df)) * 100
                    st.metric(f"{status.title()}", count, delta=f"{percentage:.1f}%")
        
        st.markdown("---")
        
        # Alert trends
        st.markdown("### 📈 Alert Trends")
        
        if 'timestamp' in df.columns and 'status' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.floor('H')
            
            hourly_status = df.groupby(['hour', 'status']).size().reset_index(name='count')
            
            fig = px.area(
                hourly_status,
                x='hour',
                y='count',
                color='status',
                title="Alert Volume Over Time",
                labels={'hour': 'Time', 'count': 'Alert Count'},
                color_discrete_map={
                    'violation': '#f44336',
                    'authorized': '#4caf50',
                    'incomplete': '#ff9800'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Top alerts
        col1, col2 = st.columns(2)
        
        with col1:
            if 'user_name' in df.columns:
                st.markdown("### 👥 Top Users by Alerts")
                top_users = df['user_name'].value_counts().head(10)
                fig = px.bar(
                    x=top_users.values,
                    y=top_users.index,
                    orientation='h',
                    title="Top 10 Users",
                    labels={'x': 'Alert Count', 'y': 'User'},
                    color=top_users.values,
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'zone_name' in df.columns:
                st.markdown("### 🗺️ Top Zones by Alerts")
                top_zones = df['zone_name'].value_counts().head(10)
                fig = px.bar(
                    x=top_zones.values,
                    y=top_zones.index,
                    orientation='h',
                    title="Top 10 Zones",
                    labels={'x': 'Alert Count', 'y': 'Zone'},
                    color=top_zones.values,
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # IOP analysis
        if 'iop' in df.columns:
            st.markdown("### 📊 IOP Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.histogram(
                    df,
                    x='iop',
                    title="IOP Distribution",
                    labels={'iop': 'IOP Value', 'count': 'Frequency'},
                    nbins=50,
                    color_discrete_sequence=['#1f77b4']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.box(
                    df,
                    y='iop',
                    x='status',
                    title="IOP by Status",
                    labels={'iop': 'IOP Value', 'status': 'Alert Status'},
                    color='status',
                    color_discrete_map={
                        'violation': '#f44336',
                        'authorized': '#4caf50',
                        'incomplete': '#ff9800'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Failed to load alert analytics: {e}")


def violation_analytics_tab():
    """Violation analytics from database"""
    st.subheader("⚠️ Violation Analytics")
    
    try:
        # Get violation summary
        summary = api.get_violation_summary()
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Violations", summary.get('total_violations', 0))
        
        with col2:
            avg_duration = summary.get('average_duration', 0)
            st.metric("Avg Duration", f"{avg_duration:.1f}s")
        
        with col3:
            top_users = summary.get('top_users', [])
            st.metric("Most Active User", 
                     top_users[0]['user_name'] if top_users else "N/A")
        
        with col4:
            top_zones = summary.get('top_zones', [])
            st.metric("Most Violated Zone", 
                     top_zones[0]['zone_name'] if top_zones else "N/A")
        
        # Charts
        st.markdown("---")
        
        if top_users:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top violating users chart
                df_users = pd.DataFrame(top_users)
                fig = px.bar(
                    df_users, 
                    x='violation_count', 
                    y='user_name',
                    orientation='h',
                    title="Top Violating Users",
                    labels={'violation_count': 'Violation Count', 'user_name': 'User'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Top zones chart
                if top_zones:
                    df_zones = pd.DataFrame(top_zones)
                    fig = px.bar(
                        df_zones, 
                        x='violation_count', 
                        y='zone_name',
                        orientation='h',
                        title="Most Violated Zones",
                        labels={'violation_count': 'Violation Count', 'zone_name': 'Zone'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
        
        # Recent violations
        st.markdown("---")
        st.subheader("Recent Violations")
        
        logs_response = api.get_violation_logs(limit=20)
        recent_violations = logs_response.get('violations', [])
        
        if recent_violations:
            df = pd.DataFrame(recent_violations)
            
            # Format for display
            display_df = df[['user_name', 'zone_name', 'duration', 'threshold', 'start_time']].copy()
            display_df['start_time'] = pd.to_datetime(display_df['start_time']).dt.strftime('%Y-%m-%d %H:%M')
            display_df.columns = ['User', 'Zone', 'Duration (s)', 'Threshold (s)', 'Time']
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No recent violations found")
            
    except Exception as e:
        st.error(f"Failed to load violation analytics: {e}")


if __name__ == "__main__":
    main()
