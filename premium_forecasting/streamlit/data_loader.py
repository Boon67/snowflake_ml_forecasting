"""
Data Loading Functions for Insurance Premium Dashboard
"""
import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session


@st.cache_data
def load_forecast_data(forecast_table):
    """
    Load all forecast-related tables with enhanced error handling
    
    Args:
        forecast_table (str): Fully qualified table name for forecast summary
        
    Returns:
        tuple: (forecast_summary, yoy_growth, predictions_12mo)
    """
    session = get_active_session()
    
    try:
        # Load forecast summary data
        summary_query = f"""
        SELECT * FROM {forecast_table}
        ORDER BY state
        """
        forecast_summary = session.sql(summary_query).to_pandas()
        
        # Clean and standardize STATE column
        if 'STATE' in forecast_summary.columns:
            forecast_summary['STATE'] = (forecast_summary['STATE']
                                        .astype(str)
                                        .str.strip()
                                        .str.replace('"', '', regex=False)
                                        .str.replace("'", '', regex=False)
                                        .str.strip()
                                        .str.upper())
        
        # Load YoY growth data
        try:
            growth_query = """
            SELECT * FROM INSURANCE_ANALYTICS.POLICY_DATA.yoy_growth_all_states
            ORDER BY state
            """
            yoy_growth = session.sql(growth_query).to_pandas()
            
            if 'STATE' in yoy_growth.columns:
                yoy_growth['STATE'] = (yoy_growth['STATE']
                                      .astype(str)
                                      .str.strip()
                                      .str.replace('"', '', regex=False)
                                      .str.replace("'", '', regex=False)
                                      .str.strip()
                                      .str.upper())
        except Exception as e:
            st.warning(f"⚠️ Could not load YoY growth data: {str(e)}")
            yoy_growth = None
        
        # Load 12-month predictions
        try:
            pred_query = """
            SELECT * FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_predictions_12months
            ORDER BY series, ts
            """
            predictions_12mo = session.sql(pred_query).to_pandas()
            
            if 'SERIES' in predictions_12mo.columns:
                predictions_12mo['SERIES'] = (predictions_12mo['SERIES']
                                             .astype(str)
                                             .str.strip()
                                             .str.replace('"', '', regex=False)
                                             .str.replace("'", '', regex=False)
                                             .str.strip()
                                             .str.upper())
        except Exception as e:
            st.warning(f"⚠️ Could not load 12-month predictions: {str(e)}")
            predictions_12mo = None
        
        return forecast_summary, yoy_growth, predictions_12mo
        
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.info(f"📋 Tables checked: `{forecast_table}`")
        return None, None, None


def prepare_map_data(forecast_summary, yoy_growth):
    """
    Prepare and merge data for map visualization
    
    Args:
        forecast_summary (pd.DataFrame): Forecast summary data
        yoy_growth (pd.DataFrame): Year-over-year growth data
        
    Returns:
        pd.DataFrame: Merged and prepared map data
    """
    # Merge forecast summary with growth data
    if yoy_growth is not None and len(yoy_growth) > 0:
        map_data = forecast_summary.merge(
            yoy_growth[['STATE', 'YOY_GROWTH_PCT']], 
            on='STATE', 
            how='left'
        )
    else:
        map_data = forecast_summary.copy()
        map_data['YOY_GROWTH_PCT'] = 0
    
    # Calculate derived metrics
    map_data['PRICE_RANGE'] = map_data['MAX_PREMIUM'] - map_data['MIN_PREMIUM']
    map_data['VOLATILITY'] = (map_data['PREMIUM_STDDEV'] / map_data['MEAN_PREMIUM'] * 100).fillna(0)
    
    return map_data

