"""
Utility Functions for Insurance Premium Dashboard
"""
import streamlit as st


def render_dashboard_controls():
    """
    Render main dashboard control panel
    
    Returns:
        str: Selected map metric
    """
    map_metric = st.selectbox(
        "🗺️ Select Map Metric",
        options=["Mean Premium", "YoY Growth %", "Premium Volatility", "Price Range"],
        help="Choose which metric to display on the US map"
    )
    
    return map_metric


def display_data_validation(map_data, map_data_clean):
    """
    Display data validation information in an expander
    
    Args:
        map_data (pd.DataFrame): Original map data
        map_data_clean (pd.DataFrame): Cleaned map data
        
    Returns:
        None (renders to Streamlit)
    """
    with st.expander("🔍 Map Data Validation", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total States", len(map_data))
        with col2:
            st.metric("Valid States", len(map_data_clean))
        with col3:
            missing = len(map_data) - len(map_data_clean)
            st.metric("Missing/Invalid", missing, delta=f"-{missing}" if missing > 0 else "0")
        
        # Show sample of STATE values
        st.write("**Sample STATE values (first 10):**")
        sample_states = map_data_clean['STATE'].head(10).tolist()
        st.code(", ".join(sample_states))
        
        # Check for invalid STATE values
        invalid_states = map_data[~map_data['STATE'].isin(map_data_clean['STATE'])]['STATE'].unique()
        if len(invalid_states) > 0:
            st.warning(f"⚠️ Found {len(invalid_states)} invalid STATE values:")
            st.code(", ".join([str(s) for s in invalid_states]))


def display_summary_cards(forecast_summary, yoy_growth):
    """
    Display summary metrics cards at the top of dashboard
    
    Args:
        forecast_summary (pd.DataFrame): Forecast summary data
        yoy_growth (pd.DataFrame): YoY growth data
        
    Returns:
        None (renders to Streamlit)
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_premium = forecast_summary['MEAN_PREMIUM'].mean()
        st.metric(
            "National Avg Premium",
            f"${avg_premium:,.0f}",
            help="Average across all states"
        )
    
    with col2:
        if yoy_growth is not None and len(yoy_growth) > 0:
            avg_growth = yoy_growth['YOY_GROWTH_PCT'].mean()
            st.metric(
                "Avg YoY Growth",
                f"{avg_growth:.1f}%",
                delta=f"{avg_growth:.1f}%",
                help="Average year-over-year growth"
            )
        else:
            st.metric("Avg YoY Growth", "N/A")
    
    with col3:
        num_states = len(forecast_summary)
        st.metric(
            "States Analyzed",
            f"{num_states}",
            help="Number of states with data"
        )
    
    with col4:
        volatility = (forecast_summary['PREMIUM_STDDEV'] / forecast_summary['MEAN_PREMIUM'] * 100).mean()
        st.metric(
            "Avg Volatility",
            f"{volatility:.1f}%",
            help="Average coefficient of variation"
        )

