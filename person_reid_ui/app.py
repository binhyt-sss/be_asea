"""
Person ReID System - Main Streamlit Application
Standalone UI Module - No backend code dependencies
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import streamlit as st
from src.config import get_config
from src.api_client import get_api_client
from src.utils import load_custom_css, show_error, show_info

# Load configuration
config = get_config()

# Page configuration
st.set_page_config(
    page_title=config.ui.title,
    page_icon=config.ui.page_icon,
    layout=config.ui.layout,
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_custom_css()

# Initialize API client
api = get_api_client(
    base_url=config.api.base_url,
    timeout=config.api.timeout,
    retry_attempts=config.api.retry_attempts,
    retry_delay=config.api.retry_delay
)

# Store in session state for pages to access
if 'api_client' not in st.session_state:
    st.session_state.api_client = api
if 'config' not in st.session_state:
    st.session_state.config = config


def main():
    """Main dashboard page"""
    
    # Header
    st.markdown(f'<div class="main-header">{config.ui.page_icon} {config.ui.title}</div>', 
                unsafe_allow_html=True)
    st.markdown("---")
    
    # Welcome section
    st.markdown("### 🎯 Welcome to Person ReID Management System")
    st.info("""
    **Person Re-Identification (ReID)** system giúp theo dõi và quản lý người dùng qua các khu vực khác nhau 
    với khả năng nhận diện và cảnh báo thời gian thực.
    """)
    
    # Check API connection
    st.markdown("### 🔌 API Connection Status")
    
    with st.spinner("Checking API connection..."):
        is_available = api.is_available()
    
    if is_available:
        st.success(f"✅ Connected to API: `{config.api.base_url}`")
        
        # Get health info
        try:
            health = api.health_check()
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("API Status", "🟢 Healthy")
            with col2:
                version = health.get('version', 'Unknown')
                st.metric("Version", version)
            with col3:
                kafka_status = "🟢 Active" if health.get('kafka_running') else "🔴 Inactive"
                st.metric("Kafka", kafka_status)
        except Exception as e:
            show_error("Failed to get health details", e if config.features.debug_mode else None)
    else:
        st.error(f"""
        ❌ **Cannot connect to API server**
        
        - API URL: `{config.api.base_url}`
        - Please ensure the backend is running
        - Check configuration in `config.yaml` or environment variables
        """)
        
        with st.expander("🔧 Configuration Help"):
            st.markdown("""
            **Option 1: Edit config.yaml**
            ```yaml
            api:
              base_url: "http://your-api-server:8000"
            ```
            
            **Option 2: Set environment variable**
            ```bash
            export PERSON_REID_API_URL="http://your-api-server:8000"
            ```
            
            **Option 3: Update in UI**
            """)
            
            new_url = st.text_input("API Base URL", value=config.api.base_url)
            if st.button("Update & Reconnect"):
                config.api.base_url = new_url
                st.rerun()
        
        return
    
    st.markdown("---")
    
    # Quick stats
    st.markdown("### 📊 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">👥</div>
            <div class="metric-label">User Management</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">🗺️</div>
            <div class="metric-label">Zone Management</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">🚨</div>
            <div class="metric-label">Real-time Alerts</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">📈</div>
            <div class="metric-label">Statistics</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Features section
    st.markdown("### ✨ Key Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 👥 User Management
        - Create, update, delete users
        - Assign users to working zones
        - View user details and zone assignments
        - Search and filter capabilities
        """)
        
        st.markdown("""
        #### 🗺️ Zone Management
        - Define working zones with polygon coordinates
        - Manage zone boundaries
        - Assign multiple users to zones
        - Visual zone representation
        """)
        
    with col2:
        st.markdown("""
        #### 🚨 Real-time Alerts
        - Live Kafka message streaming
        - Alert notifications for zone violations
        - Message history and filtering
        - Analytics and trends
        """)
        
        st.markdown("""
        #### 📈 Statistics & Analytics
        - User and zone statistics
        - Visual charts and graphs
        - Activity tracking
        - Performance metrics
        """)
    
    st.markdown("---")
    
    # Navigation guide
    st.markdown("### 🧭 Navigation")
    st.markdown("""
    Sử dụng **sidebar** bên trái để điều hướng giữa các trang:
    
    - **🏠 Home** - Trang chính (trang này)
    - **👥 Users** - Quản lý người dùng
    - **🗺️ Zones** - Quản lý khu vực
    - **🚨 Alerts** - Cảnh báo thời gian thực
    - **📈 Statistics** - Thống kê và phân tích
    """)
    
    # Configuration info
    with st.expander("⚙️ Configuration"):
        st.json(config.to_dict())
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; padding: 2rem 0;">
        <p>{config.ui.title} | Standalone UI Module v1.0.0</p>
        <p>📚 <a href="{config.api.base_url}/docs" target="_blank">API Documentation</a> | 
        🔧 <a href="{config.api.base_url}/health" target="_blank">Health Check</a></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
