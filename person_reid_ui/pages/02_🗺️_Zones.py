"""
Zone Management Page - Standalone Module
CRUD operations for working zones with polygon coordinates
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from api_client import get_api_client, APIError
from utils import show_error, show_success, load_custom_css, create_zone_polygon_figure
from config import get_config
import pandas as pd
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Zones - Person ReID",
    page_icon="🗺️",
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

# Additional custom CSS for zones
st.markdown("""
<style>
    .zone-card {
        background-color: #f1f8e9;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #66bb6a;
    }
    .coord-box {
        background-color: #fff3e0;
        padding: 0.5rem;
        border-radius: 0.25rem;
        margin: 0.25rem 0;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)


def plot_zone_polygon(zone: dict):
    """Create a plotly visualization of zone polygon"""
    return create_zone_polygon_figure(
        zone=zone,
        title=f"Zone: {zone['zone_name']} ({zone['zone_id']})"
    )


def main():
    st.title("🗺️ Zone Management")
    st.markdown("---")
    
    # Check API connection
    try:
        api.health_check()
    except APIError as e:
        show_error(f"Cannot connect to API server: {e}")
        st.info(f"Please ensure the backend is running at {config.api.base_url}")
        return
    
    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📋 View Zones", "➕ Create Zone", "📊 Visualize"])
    
    with tab1:
        view_zones_tab()
    
    with tab2:
        create_zone_tab()
    
    with tab3:
        visualize_zones_tab()


def view_zones_tab():
    """Display all zones with their details"""
    st.subheader("All Working Zones")
    
    # Refresh button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔄 Refresh", key="refresh_zones"):
            st.rerun()
    
    try:
        # Fetch zones
        zones = api.get_zones(limit=config.display.max_zones_per_page)
        
        if not zones:
            st.info("No zones found. Create your first zone in the 'Create Zone' tab.")
            return
        
        show_success(f"Found {len(zones)} zones")
        
        # Display zones in expandable cards
        for zone in zones:
            with st.expander(f"🗺️ {zone['zone_name']} (ID: {zone['zone_id']})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Zone Name:** {zone['zone_name']}")
                    st.markdown(f"**Zone ID:** {zone['zone_id']}")
                    threshold = zone.get('violation_threshold', 10)
                    st.markdown(f"**Violation Threshold:** ⏱️ {threshold}s")
                    st.markdown(f"**Created:** {zone['created_at'][:19]}")
                    
                    # Display coordinates
                    st.markdown("**Polygon Coordinates:**")
                    st.markdown(f'<div class="coord-box">P1: ({zone["x1"]}, {zone["y1"]})</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="coord-box">P2: ({zone["x2"]}, {zone["y2"]})</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="coord-box">P3: ({zone["x3"]}, {zone["y3"]})</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="coord-box">P4: ({zone["x4"]}, {zone["y4"]})</div>', unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**Actions:**")
                    
                    # View visualization
                    if st.button("📊 Visualize", key=f"viz_{zone['zone_id']}"):
                        st.session_state[f"visualizing_{zone['zone_id']}"] = True
                        st.rerun()
                    
                    # Edit button
                    if st.button("✏️ Edit", key=f"edit_{zone['zone_id']}"):
                        st.session_state[f"editing_{zone['zone_id']}"] = True
                        st.rerun()
                    
                    # Delete button
                    if st.button("🗑️ Delete", key=f"delete_{zone['zone_id']}", type="secondary"):
                        if st.session_state.get(f"confirm_delete_{zone['zone_id']}", False):
                            try:
                                api.delete_zone(zone['zone_id'])
                                show_success(f"Deleted zone {zone['zone_name']}")
                                del st.session_state[f"confirm_delete_{zone['zone_id']}"]
                                st.rerun()
                            except APIError as e:
                                show_error(f"Failed to delete: {e}")
                        else:
                            st.session_state[f"confirm_delete_{zone['zone_id']}"] = True
                            st.warning("Click delete again to confirm")
                
                # Visualization
                if st.session_state.get(f"visualizing_{zone['zone_id']}", False):
                    st.markdown("---")
                    fig = plot_zone_polygon(zone)
                    st.plotly_chart(fig, use_container_width=True)
                    if st.button("Close Visualization", key=f"close_viz_{zone['zone_id']}"):
                        del st.session_state[f"visualizing_{zone['zone_id']}"]
                        st.rerun()
                
                # Edit form
                if st.session_state.get(f"editing_{zone['zone_id']}", False):
                    st.markdown("---")
                    st.markdown("### Edit Zone")
                    edit_zone_form(zone)
        
    except APIError as e:
        show_error(f"Failed to load zones: {e}")


def edit_zone_form(zone: dict):
    """Form to edit zone details"""
    with st.form(key=f"edit_form_{zone['zone_id']}"):
        new_name = st.text_input("Zone Name", value=zone['zone_name'])
        threshold = st.number_input(
            "Violation Threshold (seconds)", 
            value=zone.get('violation_threshold', 10), 
            min_value=1, 
            max_value=300,
            help="Time limit before triggering a violation alert"
        )
        
        st.markdown("**Polygon Coordinates:**")
        col1, col2 = st.columns(2)
        
        with col1:
            x1 = st.number_input("P1 - X", value=float(zone['x1']), format="%.2f")
            y1 = st.number_input("P1 - Y", value=float(zone['y1']), format="%.2f")
            x2 = st.number_input("P2 - X", value=float(zone['x2']), format="%.2f")
            y2 = st.number_input("P2 - Y", value=float(zone['y2']), format="%.2f")
        
        with col2:
            x3 = st.number_input("P3 - X", value=float(zone['x3']), format="%.2f")
            y3 = st.number_input("P3 - Y", value=float(zone['y3']), format="%.2f")
            x4 = st.number_input("P4 - X", value=float(zone['x4']), format="%.2f")
            y4 = st.number_input("P4 - Y", value=float(zone['y4']), format="%.2f")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Save Changes", type="primary")
        with col2:
            cancel = st.form_submit_button("❌ Cancel")
        
        if submit:
            try:
                api.update_zone(
                    zone['zone_id'],
                    zone_name=new_name,
                    violation_threshold=threshold,
                    x1=x1, y1=y1, x2=x2, y2=y2,
                    x3=x3, y3=y3, x4=x4, y4=y4
                )
                show_success(f"Updated zone {new_name}")
                del st.session_state[f"editing_{zone['zone_id']}"]
                st.rerun()
            except APIError as e:
                show_error(f"Failed to update: {e}")
        
        if cancel:
            del st.session_state[f"editing_{zone['zone_id']}"]
            st.rerun()


def create_zone_tab():
    """Form to create new zone"""
    st.subheader("Create New Zone")
    
    st.info("💡 Define a working zone by specifying 4 polygon points (P1, P2, P3, P4)")
    
    with st.form(key="create_zone_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            zone_id = st.text_input("Zone ID", help="Unique identifier (e.g., ZONE_001)")
            zone_name = st.text_input("Zone Name", help="Descriptive name (e.g., Warehouse A)")
            threshold = st.number_input(
                "Violation Threshold (seconds)", 
                value=10, 
                min_value=1, 
                max_value=300,
                help="Time limit before triggering a violation alert"
            )
        
        with col2:
            st.markdown("**Quick Templates:**")
            if st.form_submit_button("📦 Square (100x100)"):
                st.session_state['template'] = 'square'
            if st.form_submit_button("📐 Rectangle (200x100)"):
                st.session_state['template'] = 'rectangle'
        
        st.markdown("**Polygon Coordinates:**")
        
        # Apply template if selected
        template = st.session_state.get('template', None)
        if template == 'square':
            default_coords = [(0, 0), (100, 0), (100, 100), (0, 100)]
        elif template == 'rectangle':
            default_coords = [(0, 0), (200, 0), (200, 100), (0, 100)]
        else:
            default_coords = [(0, 0), (0, 0), (0, 0), (0, 0)]
        
        col1, col2 = st.columns(2)
        
        with col1:
            x1 = st.number_input("P1 - X", value=float(default_coords[0][0]), format="%.2f")
            y1 = st.number_input("P1 - Y", value=float(default_coords[0][1]), format="%.2f")
            x2 = st.number_input("P2 - X", value=float(default_coords[1][0]), format="%.2f")
            y2 = st.number_input("P2 - Y", value=float(default_coords[1][1]), format="%.2f")
        
        with col2:
            x3 = st.number_input("P3 - X", value=float(default_coords[2][0]), format="%.2f")
            y3 = st.number_input("P3 - Y", value=float(default_coords[2][1]), format="%.2f")
            x4 = st.number_input("P4 - X", value=float(default_coords[3][0]), format="%.2f")
            y4 = st.number_input("P4 - Y", value=float(default_coords[3][1]), format="%.2f")
        
        submit = st.form_submit_button("➕ Create Zone", type="primary")
        
        if submit:
            if not zone_id or not zone_name:
                show_error("Please provide both Zone ID and Zone Name")
            else:
                try:
                    new_zone = api.create_zone(
                        zone_id=zone_id,
                        zone_name=zone_name,
                        violation_threshold=threshold,
                        x1=x1, y1=y1, x2=x2, y2=y2,
                        x3=x3, y3=y3, x4=x4, y4=y4
                    )
                    show_success(f"✅ Created zone: {new_zone['zone_name']} ({new_zone['zone_id']})")
                    
                    # Clear template
                    if 'template' in st.session_state:
                        del st.session_state['template']
                    
                    st.balloons()
                except APIError as e:
                    show_error(f"Failed to create zone: {e}")


def visualize_zones_tab():
    """Visualize all zones together"""
    st.subheader("Zone Visualization")
    
    try:
        zones = api.get_zones(limit=1000)
        
        if not zones:
            st.info("No zones to visualize")
            return
        
        # Create combined visualization
        fig = go.Figure()
        
        colors = config.charts.zone_colors if hasattr(config.charts, 'zone_colors') else [
            'rgba(100, 181, 246, 0.3)', 'rgba(255, 167, 38, 0.3)', 
            'rgba(102, 187, 106, 0.3)', 'rgba(239, 83, 80, 0.3)',
            'rgba(156, 39, 176, 0.3)', 'rgba(255, 235, 59, 0.3)'
        ]
        
        for i, zone in enumerate(zones):
            x_coords = [zone['x1'], zone['x2'], zone['x3'], zone['x4'], zone['x1']]
            y_coords = [zone['y1'], zone['y2'], zone['y3'], zone['y4'], zone['y1']]
            
            color = colors[i % len(colors)]
            line_color = color.replace('0.3', '1.0').replace('rgba', 'rgb')
            
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='lines+markers',
                fill='toself',
                fillcolor=color,
                line=dict(color=line_color, width=2),
                marker=dict(size=8),
                name=f"{zone['zone_name']} ({zone['zone_id']})",
                text=[f"P{j+1}" for j in range(4)] + [""],
                hovertemplate='<b>%{text}</b><br>X: %{x}<br>Y: %{y}<extra></extra>'
            ))
        
        fig.update_layout(
            title="All Working Zones Overview",
            xaxis_title="X Coordinate",
            yaxis_title="Y Coordinate",
            showlegend=True,
            hovermode='closest',
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
            height=700
        )
        
        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Zone statistics
        st.markdown("---")
        st.subheader("Zone Statistics")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Zones", len(zones))
        
        with col2:
            # Calculate average area (simple approximation using shoelace formula)
            avg_area = sum([
                abs((z['x1']*z['y2'] - z['x2']*z['y1']) +
                    (z['x2']*z['y3'] - z['x3']*z['y2']) +
                    (z['x3']*z['y4'] - z['x4']*z['y3']) +
                    (z['x4']*z['y1'] - z['x1']*z['y4'])) / 2
                for z in zones
            ]) / len(zones)
            st.metric("Avg Area", f"{avg_area:.2f}")
        
        with col3:
            # Total coverage
            total_area = sum([
                abs((z['x1']*z['y2'] - z['x2']*z['y1']) +
                    (z['x2']*z['y3'] - z['x3']*z['y2']) +
                    (z['x3']*z['y4'] - z['x4']*z['y3']) +
                    (z['x4']*z['y1'] - z['x1']*z['y4'])) / 2
                for z in zones
            ])
            st.metric("Total Coverage", f"{total_area:.2f}")
        
    except APIError as e:
        show_error(f"Visualization failed: {e}")


if __name__ == "__main__":
    main()
