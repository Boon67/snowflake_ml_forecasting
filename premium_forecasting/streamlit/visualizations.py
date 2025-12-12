"""
Visualization Functions for Insurance Premium Dashboard
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
from us_states_geojson import US_STATES_GEOJSON
from config import STATE_COORDS


def get_color_for_scale(normalized_value, color_scale):
    """
    Convert Plotly color scales to RGB values for PyDeck
    
    Args:
        normalized_value (float): Value normalized to 0-1 range
        color_scale (str): Color scale name
        
    Returns:
        list: [R, G, B, Alpha] color values
    """
    if color_scale == 'Reds':
        r = int(255)
        g = int(255 * (1 - normalized_value * 0.8))
        b = int(255 * (1 - normalized_value * 0.8))
    elif color_scale == 'Blues':
        r = int(255 * (1 - normalized_value * 0.8))
        g = int(255 * (1 - normalized_value * 0.6))
        b = int(255)
    elif color_scale == 'Oranges':
        r = int(255)
        g = int(255 * (1 - normalized_value * 0.4))
        b = int(255 * (1 - normalized_value * 0.8))
    elif color_scale == 'RdYlGn':
        # Red-Yellow-Green diverging scale (low=red, high=green)
        if normalized_value < 0.5:
            r = 255
            g = int(255 * normalized_value * 2)
            b = 0
        else:
            r = int(255 * (1 - (normalized_value - 0.5) * 2))
            g = 255
            b = 0
    elif color_scale == 'RdYlGn_r':
        # Reversed Red-Yellow-Green scale (low=green, high=red)
        if normalized_value < 0.5:
            r = int(255 * normalized_value * 2)
            g = 255
            b = 0
        else:
            r = 255
            g = int(255 * (1 - (normalized_value - 0.5) * 2))
            b = 0
    else:
        # Default: Blue to Red
        r = int(255 * normalized_value)
        g = int(100 * (1 - abs(normalized_value - 0.5) * 2))
        b = int(255 * (1 - normalized_value))
    
    return [r, g, b, 180]


def create_choropleth_map(map_data_clean, config, map_metric):
    """
    Create interactive choropleth map with PyDeck
    
    Args:
        map_data_clean (pd.DataFrame): Cleaned map data
        config (dict): Metric configuration
        map_metric (str): Selected metric name
        
    Returns:
        None (renders map directly to Streamlit)
    """
    color_col = config['column']
    
    # Load GeoJSON and merge with values
    geojson_with_data = US_STATES_GEOJSON.copy()
    state_values = dict(zip(map_data_clean['STATE'], map_data_clean[color_col]))
    
    # Normalize values for color mapping
    min_val = map_data_clean[color_col].min()
    max_val = map_data_clean[color_col].max()
    value_range = max_val - min_val if max_val != min_val else 1
    
    # Add properties to GeoJSON features
    for feature in geojson_with_data['features']:
        state_code = feature['properties']['code']
        if state_code in state_values:
            value = state_values[state_code]
            normalized_value = (value - min_val) / value_range
            # Round value to 2 decimal places for tooltip display
            feature['properties']['value'] = round(float(value), 2)
            feature['properties']['fill_color'] = get_color_for_scale(
                normalized_value, 
                config['color_scale']
            )
        else:
            feature['properties']['value'] = 0
            feature['properties']['fill_color'] = [200, 200, 200, 100]
    
    # Create PyDeck GeoJsonLayer
    geojson_layer = pdk.Layer(
        'GeoJsonLayer',
        geojson_with_data,
        opacity=0.8,
        stroked=True,
        filled=True,
        extruded=False,
        wireframe=False,
        get_fill_color='properties.fill_color',
        get_line_color=[255, 255, 255],
        get_line_width=2,
        pickable=True
    )
    
    # Set view state for US map
    view_state = pdk.ViewState(
        latitude=37.8,
        longitude=-96,
        zoom=3.5,
        pitch=0
    )
    
    # Create tooltip with metric-specific formatting
    if map_metric in ["Mean Premium", "Price Range"]:
        value_format = '${value}'  # Dollar format
    elif map_metric in ["YoY Growth %", "Premium Volatility"]:
        value_format = '{value}%'  # Percentage format
    else:
        value_format = '{value}'  # Default format
    
    tooltip_config = {
        'html': '<b>{name}</b><br/>State: {code}<br/>' + config['title'] + ': ' + value_format,
        'style': {
            'backgroundColor': 'steelblue',
            'color': 'white'
        }
    }
    
    deck = pdk.Deck(
        layers=[geojson_layer],
        initial_view_state=view_state,
        tooltip=tooltip_config
    )
    
    # Display the pydeck map
    st.pydeck_chart(deck)
    
    # Map statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Highest Value", f"{map_data_clean[color_col].max():.1f}")
    with col2:
        st.metric("Average Value", f"{map_data_clean[color_col].mean():.1f}")
    with col3:
        st.metric("Lowest Value", f"{map_data_clean[color_col].min():.1f}")


def create_bar_chart(map_data_clean, config, map_metric):
    """
    Create interactive horizontal bar chart
    
    Args:
        map_data_clean (pd.DataFrame): Cleaned map data
        config (dict): Metric configuration
        map_metric (str): Selected metric name
        
    Returns:
        None (renders chart directly to Streamlit)
    """
    color_col = config['column']
    
    st.markdown("### 📊 Interactive State Comparison")
    st.caption("Hover over bars for detailed information • Click and drag to zoom • Double-click to reset")
    
    # Sort data for better visualization
    chart_data = map_data_clean.sort_values(color_col, ascending=True).copy()
    
    fig_bar = px.bar(
        chart_data,
        x=color_col,
        y='STATE',
        orientation='h',
        title=f'{map_metric} by State (Sorted)',
        labels={color_col: config['title'], 'STATE': 'State'},
        color=color_col,
        color_continuous_scale=config['color_scale'],
        height=max(800, len(chart_data) * 16)
    )
    
    fig_bar.update_layout(
        xaxis_title=config['title'],
        yaxis_title='State',
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

