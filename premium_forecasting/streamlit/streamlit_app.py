"""
Insurance Premium Forecasting Dashboard - Modular Version
Main application file that imports from separate modules
"""
import streamlit as st

# Import from local modules
from config import METRIC_CONFIG, DEFAULT_TABLE, APP_CONFIG
from data_loader import load_forecast_data, prepare_map_data
from visualizations import create_choropleth_map, create_bar_chart
from utils import (
    render_dashboard_controls,
    display_summary_cards
)

# App configuration
st.set_page_config(
    page_title="Insurance Premium Forecast Analysis",
    page_icon=APP_CONFIG['page_icon'],
    layout=APP_CONFIG['layout']
)

st.title(APP_CONFIG['title'])
st.markdown(APP_CONFIG['subtitle'])

# Load data from default table
forecast_summary, yoy_growth, predictions_12mo = load_forecast_data(DEFAULT_TABLE)

if forecast_summary is not None:
    # Display summary cards
    display_summary_cards(forecast_summary, yoy_growth)
    
    st.markdown("---")
    
    # Dashboard controls (main area)
    map_metric = render_dashboard_controls()
    
    # Prepare map data
    map_data = prepare_map_data(forecast_summary, yoy_growth)
    
    # Get metric configuration
    config = METRIC_CONFIG[map_metric]
    color_col = config['column']
    
    # Clean data for visualization
    map_data_clean = map_data.dropna(subset=[color_col, 'STATE']).copy()
    
    # Filter to valid 2-letter state codes
    map_data_clean = map_data_clean[
        (map_data_clean['STATE'].str.len() == 2) & 
        (map_data_clean['STATE'].str.isalpha())
    ]
    
    # Main visualization section
    if len(map_data_clean) == 0:
        st.error("⚠️ No valid state codes found after cleaning")
        st.info("STATE values must be exactly 2 uppercase letters (e.g., CA, NY, TX)")
    else:
        # Create choropleth map
        st.markdown(f"### 🗺️ US Premium Map: {map_metric}")
        try:
            create_choropleth_map(map_data_clean, config, map_metric)
        except Exception as e:
            st.error(f"❌ Map visualization error: {str(e)}")
        
        # Create bar chart
        try:
            create_bar_chart(map_data_clean, config, map_metric)
        except Exception as e:
            st.error(f"❌ Bar chart error: {str(e)}")
        
        # Top and Bottom States Analysis
        st.markdown("### 📈 Top & Bottom States Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### 🔝 Top 10 States - Highest {map_metric}")
            top_10 = map_data_clean.nlargest(10, color_col)[['STATE', color_col]]
            st.dataframe(
                top_10.reset_index(drop=True),
                use_container_width=True,
                hide_index=True
            )
        
        with col2:
            st.markdown(f"#### 🔻 Bottom 10 States - Lowest {map_metric}")
            bottom_10 = map_data_clean.nsmallest(10, color_col)[['STATE', color_col]]
            st.dataframe(
                bottom_10.reset_index(drop=True),
                use_container_width=True,
                hide_index=True
            )
        
        # Data Export
        st.markdown("### 📥 Export Data")
        csv = map_data_clean.to_csv(index=False)
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name=f"premium_forecast_{map_metric.replace(' ', '_').lower()}.csv",
            mime="text/csv"
        )
else:
    st.error("❌ Could not load data. Please check table configuration.")
    st.info(f"📋 Configured table: `{DEFAULT_TABLE}`")

