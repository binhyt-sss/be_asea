"""
Utility functions for Person ReID UI
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
import plotly.graph_objects as go


def format_datetime(dt_string: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime string
    
    Args:
        dt_string: ISO datetime string
        format_str: Output format
        
    Returns:
        Formatted datetime string
    """
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime(format_str)
    except:
        return dt_string[:19] if len(dt_string) >= 19 else dt_string


def show_error(message: str, exception: Optional[Exception] = None):
    """
    Display error message
    
    Args:
        message: Error message
        exception: Optional exception object
    """
    st.error(f"❌ {message}")
    if exception and hasattr(st.session_state, 'debug_mode') and st.session_state.debug_mode:
        st.exception(exception)


def show_success(message: str):
    """Display success message"""
    st.success(f"✅ {message}")


def show_info(message: str):
    """Display info message"""
    st.info(f"ℹ️ {message}")


def show_warning(message: str):
    """Display warning message"""
    st.warning(f"⚠️ {message}")


def confirm_action(key: str, message: str) -> bool:
    """
    Require double confirmation for destructive actions
    
    Args:
        key: Unique key for session state
        message: Confirmation message
        
    Returns:
        True if confirmed, False otherwise
    """
    confirm_key = f"confirm_{key}"
    
    if st.session_state.get(confirm_key, False):
        st.session_state[confirm_key] = False
        return True
    else:
        st.session_state[confirm_key] = True
        show_warning(message)
        return False


def create_zone_polygon_figure(zone: Dict[str, Any], title: Optional[str] = None) -> go.Figure:
    """
    Create Plotly figure for zone polygon visualization
    
    Args:
        zone: Zone data with x1-x4, y1-y4 coordinates
        title: Optional chart title
        
    Returns:
        Plotly Figure object
    """
    x_coords = [zone['x1'], zone['x2'], zone['x3'], zone['x4'], zone['x1']]
    y_coords = [zone['y1'], zone['y2'], zone['y3'], zone['y4'], zone['y1']]
    
    fig = go.Figure()
    
    # Add polygon
    fig.add_trace(go.Scatter(
        x=x_coords,
        y=y_coords,
        mode='lines+markers',
        fill='toself',
        fillcolor='rgba(100, 181, 246, 0.3)',
        line=dict(color='rgb(33, 150, 243)', width=2),
        marker=dict(size=10, color='rgb(33, 150, 243)'),
        name=zone.get('zone_name', 'Zone')
    ))
    
    # Add point labels
    for i, (x, y) in enumerate(zip(x_coords[:-1], y_coords[:-1]), 1):
        fig.add_annotation(
            x=x, y=y,
            text=f"P{i}",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="rgb(33, 150, 243)",
            ax=20, ay=-30
        )
    
    # Update layout
    fig.update_layout(
        title=title or f"Zone: {zone.get('zone_name', 'Unknown')} ({zone.get('zone_id', 'N/A')})",
        xaxis_title="X Coordinate",
        yaxis_title="Y Coordinate",
        showlegend=True,
        hovermode='closest',
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        height=500
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    
    return fig


def load_custom_css():
    """Load custom CSS styles"""
    st.markdown("""
    <style>
        /* Cards */
        .user-card {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid #1f77b4;
        }
        
        .zone-card {
            background-color: #f1f8e9;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            border-left: 4px solid #66bb6a;
        }
        
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
        
        /* Badges */
        .zone-badge {
            display: inline-block;
            background-color: #e3f2fd;
            color: #1976d2;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            margin: 0.25rem;
            font-size: 0.875rem;
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
        
        .status-success {
            background-color: #d4edda;
            color: #155724;
        }
        
        .status-error {
            background-color: #f8d7da;
            color: #721c24;
        }
        
        /* Metrics */
        .metric-card {
            background-color: #f0f2f6;
            padding: 1.5rem;
            border-radius: 0.5rem;
            text-align: center;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
        }
        
        .metric-label {
            font-size: 1rem;
            color: #666;
            margin-top: 0.5rem;
        }
        
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
        
        /* Other */
        .coord-box {
            background-color: #fff3e0;
            padding: 0.5rem;
            border-radius: 0.25rem;
            margin: 0.25rem 0;
            font-family: monospace;
        }
        
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            padding: 1rem 0;
            margin-bottom: 2rem;
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


def get_color_scheme(scheme: str = "plotly") -> Dict[str, str]:
    """
    Get color scheme for charts
    
    Args:
        scheme: Color scheme name
        
    Returns:
        Dictionary of color mappings
    """
    schemes = {
        "plotly": {
            "violation": "#f44336",
            "authorized": "#4caf50",
            "incomplete": "#ff9800",
            "primary": "#1f77b4",
            "secondary": "#ff7f0e",
            "success": "#2ca02c",
            "warning": "#ff9800",
            "error": "#d62728"
        },
        "seaborn": {
            "violation": "#d32f2f",
            "authorized": "#388e3c",
            "incomplete": "#f57c00",
            "primary": "#1976d2",
            "secondary": "#f57c00",
            "success": "#388e3c",
            "warning": "#f57c00",
            "error": "#c62828"
        }
    }
    
    return schemes.get(scheme, schemes["plotly"])
