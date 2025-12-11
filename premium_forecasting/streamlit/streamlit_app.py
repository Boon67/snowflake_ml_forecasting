# Insurance Premium Forecasting Analysis App
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from snowflake.snowpark.context import get_active_session
import numpy as np
import pydeck as pdk

# Get Snowflake session
session = get_active_session()

# App configuration
st.set_page_config(
    page_title="Insurance Premium Forecast Analysis",
    page_icon="📊",
    layout="wide"
)

# Configuration variables (add this section)
st.sidebar.header("⚙️ Configuration")
FORECAST_TABLE = st.sidebar.text_input(
    "Forecast Summary Table",
    value="INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary",
    help="Fully qualified table name for premium forecast summary"
)

# State coordinates for map visualization (approximate center of each state)
STATE_COORDS = {
    'AL': [32.806671, -86.791130], 'AK': [61.370716, -152.404419], 'AZ': [33.729759, -111.431221],
    'AR': [34.969704, -92.373123], 'CA': [36.116203, -119.681564], 'CO': [39.059811, -105.311104],
    'CT': [41.597782, -72.755371], 'DE': [39.318523, -75.507141], 'FL': [27.766279, -81.686783],
    'GA': [33.040619, -83.643074], 'HI': [21.094318, -157.498337], 'ID': [44.240459, -114.478828],
    'IL': [40.349457, -88.986137], 'IN': [39.849426, -86.258278], 'IA': [42.011539, -93.210526],
    'KS': [38.526600, -96.726486], 'KY': [37.668140, -84.670067], 'LA': [31.169546, -91.867805],
    'ME': [44.693947, -69.381927], 'MD': [39.063946, -76.802101], 'MA': [42.230171, -71.530106],
    'MI': [43.326618, -84.536095], 'MN': [45.694454, -93.900192], 'MS': [32.741646, -89.678696],
    'MO': [38.456085, -92.288368], 'MT': [46.921925, -110.454353], 'NE': [41.125370, -98.268082],
    'NV': [38.313515, -117.055374], 'NH': [43.452492, -71.563896], 'NJ': [40.298904, -74.521011],
    'NM': [34.840515, -106.248482], 'NY': [42.165726, -74.948051], 'NC': [35.630066, -79.806419],
    'ND': [47.528912, -99.784012], 'OH': [40.388783, -82.764915], 'OK': [35.565342, -96.928917],
    'OR': [44.572021, -122.070938], 'PA': [40.590752, -77.209755], 'RI': [41.680893, -71.511780],
    'SC': [33.856892, -80.945007], 'SD': [44.299782, -99.438828], 'TN': [35.747845, -86.692345],
    'TX': [31.054487, -97.563461], 'UT': [40.150032, -111.862434], 'VT': [44.045876, -72.710686],
    'VA': [37.769337, -78.169968], 'WA': [47.400902, -121.490494], 'WV': [38.491226, -80.954453],
    'WI': [44.268543, -89.616508], 'WY': [42.755966, -107.302490]
}

st.title("🏠 Insurance Premium Forecasting Dashboard")
st.markdown("Analysis of state-by-state insurance premium forecasts and trends")

# Sidebar for controls
st.sidebar.header("🔧 Dashboard Controls")

# Load data function with caching
@st.cache_data
def load_forecast_data():
    """Load all forecast-related tables with enhanced error handling"""
    try:
        # Load forecast summary data
        summary_query = f"""
        SELECT * FROM {FORECAST_TABLE}
        ORDER BY state
        """
        forecast_summary = session.sql(summary_query).to_pandas()
        
        # Clean and standardize STATE column (assumes STATE column contains state codes like 'CA', 'NY', etc.)
        if 'STATE' in forecast_summary.columns:
            # Remove all quote characters (both single and double quotes) - multiple passes
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
            
            # Clean and standardize STATE column
            if 'STATE' in yoy_growth.columns:
                # Remove all quote characters (both single and double quotes) - multiple passes
                yoy_growth['STATE'] = (yoy_growth['STATE']
                                      .astype(str)
                                      .str.strip()
                                      .str.replace('"', '', regex=False)
                                      .str.replace("'", '', regex=False)
                                      .str.strip()
                                      .str.upper())
        except Exception as e:
            st.warning(f"Growth data unavailable: {str(e)}")
            yoy_growth = None
        
        # Load detailed predictions
        try:
            predictions_query = """
            SELECT * FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_predictions_12months
            LIMIT 2000
            """
            predictions = session.sql(predictions_query).to_pandas()
            
            # Clean SERIES column (contains state names)
            if 'SERIES' in predictions.columns:
                # Remove all quote characters (both single and double quotes) - multiple passes
                predictions['SERIES'] = (predictions['SERIES']
                                        .astype(str)
                                        .str.strip()
                                        .str.replace('"', '', regex=False)
                                        .str.replace("'", '', regex=False)
                                        .str.strip()
                                        .str.upper())
        except Exception as e:
            st.warning(f"Predictions data unavailable: {str(e)}")
            predictions = None
        
        return forecast_summary, yoy_growth, predictions
        
    except Exception as e:
        st.error(f"Critical error loading forecast data: {str(e)}")
        return None, None, None

# Data validation helper
def validate_data(df, name):
    """Validate dataframe and display info"""
    if df is not None and len(df) > 0:
        st.sidebar.success(f"✅ {name}: {len(df)} records")
        return True
    else:
        st.sidebar.error(f"❌ {name}: No data")
        return False

# Load data with progress indication
with st.spinner("🔄 Loading insurance forecast data..."):
    forecast_summary, yoy_growth, predictions = load_forecast_data()

# Validate loaded data
if forecast_summary is not None and len(forecast_summary) > 0:
    
    # Data validation sidebar
    st.sidebar.subheader("📊 Data Status")
    validate_data(forecast_summary, "Forecast Summary")
    validate_data(yoy_growth, "YoY Growth")
    validate_data(predictions, "Predictions")
    
    # Data quality checks - verify STATE column contains valid state codes
    if 'STATE' in forecast_summary.columns:
        valid_states = forecast_summary['STATE'].notna().sum()
        st.sidebar.info(f"📍 {valid_states} states with data")
    
    # Main KPI metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_premium = forecast_summary['MEAN_PREMIUM'].mean()
        st.metric("🏠 National Avg Premium", f"${avg_premium:,.0f}")
    
    with col2:
        if yoy_growth is not None and len(yoy_growth) > 0:
            avg_growth = yoy_growth['YOY_GROWTH_PCT'].mean()
            st.metric("📈 Avg YoY Growth", f"{avg_growth:.1f}%")
        else:
            st.metric("📈 Avg YoY Growth", "N/A")
    
    with col3:
        highest_premium = forecast_summary['MEAN_PREMIUM'].max()
        highest_state = forecast_summary.loc[forecast_summary['MEAN_PREMIUM'].idxmax(), 'STATE']
        st.metric("🔴 Highest Premium", f"${highest_premium:,.0f}", f"({highest_state})")
    
    with col4:
        lowest_premium = forecast_summary['MEAN_PREMIUM'].min()
        lowest_state = forecast_summary.loc[forecast_summary['MEAN_PREMIUM'].idxmin(), 'STATE']
        st.metric("🟢 Lowest Premium", f"${lowest_premium:,.0f}", f"({lowest_state})")
    
    st.divider()
    
    # ========== STATE-BY-STATE VISUALIZATION ==========
    st.header("📊 State-by-State Analysis")
    
    # Map controls
    col1, col2 = st.columns([3, 1])
    
    with col1:
        map_metric = st.selectbox(
            "📊 Select metric to visualize:",
            ["Mean Premium", "YoY Growth %", "Premium Volatility", "Price Range"],
            help="Choose which metric to display on the US map"
        )
    
    with col2:
        show_debug = st.checkbox("🔍 Show Debug Info", help="Display data validation information")
    
    # Prepare map data
    if yoy_growth is not None and len(yoy_growth) > 0:
        # Merge forecast summary with growth data on STATE column
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
    
    # Configure map settings based on selected metric
    metric_config = {
        "Mean Premium": {
            'column': 'MEAN_PREMIUM',
            'title': 'Average Premium ($)',
            'format': ':$,.0f',
            'color_scale': 'Reds'
        },
        "YoY Growth %": {
            'column': 'YOY_GROWTH_PCT',
            'title': 'Year-over-Year Growth (%)',
            'format': ':.1f%',
            'color_scale': 'RdYlGn'
        },
        "Premium Volatility": {
            'column': 'VOLATILITY',
            'title': 'Coefficient of Variation (%)',
            'format': ':.1f%',
            'color_scale': 'Oranges'
        },
        "Price Range": {
            'column': 'PRICE_RANGE',
            'title': 'Premium Range ($)',
            'format': ':$,.0f',
            'color_scale': 'Blues'
        }
    }
    
    config = metric_config[map_metric]
    color_col = config['column']
    
    # Data validation for map - STATE column should contain state codes
    map_data_clean = map_data.dropna(subset=[color_col, 'STATE']).copy()
    
    # Debug information
    if show_debug:
        with st.expander("🔍 Map Data Validation", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total States", len(map_data))
            with col2:
                st.metric("Valid Data Points", len(map_data_clean))
            with col3:
                st.metric("Missing Data", len(map_data) - len(map_data_clean))
            
            st.subheader("Sample Data Preview")
            display_cols = ['STATE', color_col]
            st.dataframe(map_data_clean[display_cols].head(10), use_container_width=True)
            
            st.subheader("Data Types")
            st.write(f"STATE type: {map_data_clean['STATE'].dtype}")
            st.write(f"{color_col} type: {map_data_clean[color_col].dtype}")
            
            st.subheader("Value Ranges")
            st.write(f"{color_col} min: {map_data_clean[color_col].min()}")
            st.write(f"{color_col} max: {map_data_clean[color_col].max()}")
            st.write(f"Null values in {color_col}: {map_data_clean[color_col].isna().sum()}")
            st.write(f"Null values in STATE: {map_data_clean['STATE'].isna().sum()}")
            
            st.subheader("Sample STATE Values (First 5)")
            st.write(f"STATE values: {list(map_data_clean['STATE'].head(5))}")
            st.write(f"STATE string repr: {[repr(s) for s in map_data_clean['STATE'].head(5)]}")
            
            st.subheader("STATE Column Details")
            st.write(f"Unique states: {len(map_data_clean['STATE'].unique())}")
            st.write(f"All STATE values: {sorted(map_data_clean['STATE'].unique())}")
    
    # Create the map visualization
    if len(map_data_clean) == 0:
        st.error(f"⚠️ No valid data available for {map_metric}")
        st.info("Please check data quality in the debug section above")
    else:
        try:
            # Ensure the color column has valid numeric values
            map_data_clean[color_col] = pd.to_numeric(map_data_clean[color_col], errors='coerce')
            
            # Remove any rows with NaN values in color column after conversion
            map_data_clean = map_data_clean.dropna(subset=[color_col])
            
            if len(map_data_clean) == 0:
                st.error(f"⚠️ No valid numeric data for {map_metric}")
                st.info("All values in the selected metric are null or invalid")
            else:
                # Final cleanup of STATE column to ensure compatibility with Plotly
                map_data_clean = map_data_clean.copy()
                map_data_clean['STATE'] = (map_data_clean['STATE']
                                          .astype(str)
                                          .str.strip()
                                          .str.upper()
                                          .str.replace(r'[^A-Z]', '', regex=True))  # Remove any non-letter characters
                
                # Filter out invalid state codes (must be exactly 2 characters)
                map_data_clean = map_data_clean[map_data_clean['STATE'].str.len() == 2]
                
                if len(map_data_clean) == 0:
                    st.error(f"⚠️ No valid state codes found after cleaning")
                    st.info("STATE values must be exactly 2 uppercase letters (e.g., CA, NY, TX)")
                else:
                    # Create pydeck map visualization
                    # Add coordinates to map data
                    map_data_with_coords = map_data_clean.copy()
                    map_data_with_coords['lat'] = map_data_with_coords['STATE'].map(lambda x: STATE_COORDS.get(x, [0, 0])[0])
                    map_data_with_coords['lon'] = map_data_with_coords['STATE'].map(lambda x: STATE_COORDS.get(x, [0, 0])[1])
                    
                    # Create formatted value for tooltip display
                    map_data_with_coords['display_value'] = map_data_with_coords[color_col].apply(lambda x: f"{x:,.1f}")
                    
                    # Normalize color values for better visualization (0-1 scale)
                    min_val = map_data_with_coords[color_col].min()
                    max_val = map_data_with_coords[color_col].max()
                    map_data_with_coords['normalized'] = (map_data_with_coords[color_col] - min_val) / (max_val - min_val)
                    
                    # Create color based on normalized value (red to green scale for growth, red scale for premiums)
                    if 'GROWTH' in color_col.upper():
                        # Red to green for growth
                        map_data_with_coords['color_r'] = map_data_with_coords['normalized'].apply(lambda x: int(255 * (1 - x)))
                        map_data_with_coords['color_g'] = map_data_with_coords['normalized'].apply(lambda x: int(255 * x))
                        map_data_with_coords['color_b'] = 50
                    else:
                        # Red scale for premiums
                        map_data_with_coords['color_r'] = map_data_with_coords['normalized'].apply(lambda x: int(139 + 116 * x))
                        map_data_with_coords['color_g'] = map_data_with_coords['normalized'].apply(lambda x: int(0 + 69 * x))
                        map_data_with_coords['color_b'] = map_data_with_coords['normalized'].apply(lambda x: int(0 + 19 * x))
                    
                    # Create pydeck layer
                    layer = pdk.Layer(
                        'ScatterplotLayer',
                        data=map_data_with_coords,
                        get_position='[lon, lat]',
                        get_fill_color='[color_r, color_g, color_b, 200]',
                        get_radius=50000,
                        pickable=True,
                        auto_highlight=True
                    )
                    
                    # Set the viewport location
                    view_state = pdk.ViewState(
                        latitude=37.5,
                        longitude=-95,
                        zoom=3.5,
                        pitch=0
                    )
                    
                    # Render the map
                    st.pydeck_chart(pdk.Deck(
                        layers=[layer],
                        initial_view_state=view_state,
                        tooltip={
                            'html': '<b>{STATE}</b><br/>' + config['title'] + ': {display_value}',
                            'style': {
                                'backgroundColor': 'steelblue',
                                'color': 'white',
                                'fontSize': '14px',
                                'padding': '10px'
                            }
                        }
                    ))
                    
                    # Map statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Highest Value", f"{map_data_clean[color_col].max():.1f}")
                    with col2:
                        st.metric("Average Value", f"{map_data_clean[color_col].mean():.1f}")
                    with col3:
                        st.metric("Lowest Value", f"{map_data_clean[color_col].min():.1f}")
                    
                    # Interactive bar chart visualization
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
                        height=max(800, len(chart_data) * 16)  # Dynamic height based on number of states
                    )
                    
                    fig_bar.update_layout(
                        xaxis_title=config['title'],
                        yaxis_title='State',
                        showlegend=False,
                        yaxis={'categoryorder': 'total ascending'}
                    )
                    
                    st.plotly_chart(fig_bar, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Map visualization error: {str(e)}")
            
            # Fallback: Horizontal bar chart
            st.subheader("📊 Fallback Visualization: Top 20 States")
            
            top_20_data = map_data_clean.nlargest(20, color_col)
            
            fig_fallback = px.bar(
                top_20_data,
                x=color_col,
                y='STATE',
                orientation='h',
                title=f'Top 20 States by {map_metric}',
                labels={color_col: config['title']},
                color=color_col,
                color_continuous_scale=config['color_scale']
            )
            
            fig_fallback.update_layout(
                height=600,
                yaxis={'categoryorder': 'total ascending'},
                showlegend=False
            )
            
            st.plotly_chart(fig_fallback, use_container_width=True)
    
    # ========== DETAILED ANALYSIS TABS ==========
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏆 State Rankings", 
        "📈 Growth Analysis", 
        "🔍 State Deep Dive", 
        "📊 Correlation Analysis",
        "📋 Raw Data"
    ])
    
    with tab1:
        st.subheader("🏆 State Performance Rankings")
        
        # Top and bottom performers
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔴 **Highest Premium States**")
            top_premium = forecast_summary.nlargest(10, 'MEAN_PREMIUM')[['STATE', 'MEAN_PREMIUM', 'PREMIUM_STDDEV']].copy()
            top_premium.columns = ['State', 'Avg Premium ($)', 'Std Dev ($)']
            top_premium['Avg Premium ($)'] = top_premium['Avg Premium ($)'].apply(lambda x: f"${x:,.0f}")
            top_premium['Std Dev ($)'] = top_premium['Std Dev ($)'].apply(lambda x: f"${x:,.0f}")
            st.dataframe(top_premium, hide_index=True, use_container_width=True)
        
        with col2:
            st.markdown("#### 🟢 **Lowest Premium States**")
            bottom_premium = forecast_summary.nsmallest(10, 'MEAN_PREMIUM')[['STATE', 'MEAN_PREMIUM', 'PREMIUM_STDDEV']].copy()
            bottom_premium.columns = ['State', 'Avg Premium ($)', 'Std Dev ($)']
            bottom_premium['Avg Premium ($)'] = bottom_premium['Avg Premium ($)'].apply(lambda x: f"${x:,.0f}")
            bottom_premium['Std Dev ($)'] = bottom_premium['Std Dev ($)'].apply(lambda x: f"${x:,.0f}")
            st.dataframe(bottom_premium, hide_index=True, use_container_width=True)
        
        # Distribution visualization
        st.markdown("#### 📊 **Premium Distribution Analysis**")
        
        # Create histogram
        fig_hist = px.histogram(
            forecast_summary,
            x='MEAN_PREMIUM',
            nbins=15,
            title="Distribution of Average Premiums Across All States",
            labels={'MEAN_PREMIUM': 'Average Premium ($)', 'count': 'Number of States'},
            marginal="box"  # Add box plot on top
        )
        
        fig_hist.update_layout(
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Median Premium", f"${forecast_summary['MEAN_PREMIUM'].median():,.0f}")
        with col2:
            st.metric("Standard Deviation", f"${forecast_summary['MEAN_PREMIUM'].std():,.0f}")
        with col3:
            q75 = forecast_summary['MEAN_PREMIUM'].quantile(0.75)
            q25 = forecast_summary['MEAN_PREMIUM'].quantile(0.25)
            st.metric("Interquartile Range", f"${q75-q25:,.0f}")
        with col4:
            range_val = forecast_summary['MEAN_PREMIUM'].max() - forecast_summary['MEAN_PREMIUM'].min()
            st.metric("Total Range", f"${range_val:,.0f}")
    
    with tab2:
        if yoy_growth is not None and len(yoy_growth) > 0:
            st.subheader("📈 Year-over-Year Growth Analysis")
            
            # Growth distribution
            fig_growth_dist = px.histogram(
                yoy_growth,
                x='YOY_GROWTH_PCT',
                nbins=20,
                title="Distribution of Year-over-Year Growth Rates",
                labels={'YOY_GROWTH_PCT': 'YoY Growth (%)', 'count': 'Number of States'},
                marginal="violin"
            )
            
            fig_growth_dist.update_layout(height=400)
            st.plotly_chart(fig_growth_dist, use_container_width=True)
            
            # Growth leaders and laggards
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🚀 **Fastest Growing States**")
                # Determine available columns
                growth_cols = ['STATE', 'YOY_GROWTH_PCT']
                col_names = ['State', 'Growth (%)']
                
                if 'TRAILING_12MO_AVG' in yoy_growth.columns:
                    growth_cols.extend(['TRAILING_12MO_AVG', 'FORECAST_12MO_AVG'])
                    col_names.extend(['Historical Avg ($)', 'Forecast Avg ($)'])
                
                top_growth = yoy_growth.nlargest(10, 'YOY_GROWTH_PCT')[growth_cols].copy()
                top_growth.columns = col_names
                
                # Format columns
                if len(col_names) > 2:
                    for col in ['Historical Avg ($)', 'Forecast Avg ($)']:
                        if col in top_growth.columns:
                            top_growth[col] = top_growth[col].apply(lambda x: f"${x:,.0f}")
                
                top_growth['Growth (%)'] = top_growth['Growth (%)'].apply(lambda x: f"{x:.2f}%")
                st.dataframe(top_growth, hide_index=True, use_container_width=True)
            
            with col2:
                st.markdown("#### 🐌 **Slowest Growing States**")
                bottom_growth = yoy_growth.nsmallest(10, 'YOY_GROWTH_PCT')[growth_cols].copy()
                bottom_growth.columns = col_names
                
                # Format columns
                if len(col_names) > 2:
                    for col in ['Historical Avg ($)', 'Forecast Avg ($)']:
                        if col in bottom_growth.columns:
                            bottom_growth[col] = bottom_growth[col].apply(lambda x: f"${x:,.0f}")
                
                bottom_growth['Growth (%)'] = bottom_growth['Growth (%)'].apply(lambda x: f"{x:.2f}%")
                st.dataframe(bottom_growth, hide_index=True, use_container_width=True)
            
            # Growth statistics
            st.markdown("#### 📊 **Growth Statistics Summary**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_growth = yoy_growth['YOY_GROWTH_PCT'].mean()
                st.metric("Average Growth", f"{avg_growth:.2f}%")
            
            with col2:
                median_growth = yoy_growth['YOY_GROWTH_PCT'].median()
                st.metric("Median Growth", f"{median_growth:.2f}%")
            
            with col3:
                std_growth = yoy_growth['YOY_GROWTH_PCT'].std()
                st.metric("Growth Std Dev", f"{std_growth:.2f}%")
            
            with col4:
                growth_range = yoy_growth['YOY_GROWTH_PCT'].max() - yoy_growth['YOY_GROWTH_PCT'].min()
                st.metric("Growth Range", f"{growth_range:.2f}%")
        
        else:
            st.warning("⚠️ Year-over-Year growth data is not available")
            st.info("Growth analysis requires the yoy_growth_all_states table to be populated")
    
    with tab3:
        st.subheader("🔍 Individual State Deep Dive")
        
        # State selection
        available_states = sorted(forecast_summary['STATE'].unique())
        
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_state = st.selectbox(
                "🏛️ Select a state for detailed analysis:",
                options=available_states,
                index=0
            )
        
        with col2:
            if st.button("📊 Analyze All States", help="View comparative analysis"):
                st.info("Use the other tabs for multi-state comparisons")
        
        if selected_state:
            # Get state data
            state_data = forecast_summary[forecast_summary['STATE'] == selected_state].iloc[0]
            
            # State header
            st.markdown(f"### 🏛️ **{selected_state}** Insurance Analysis")
            
            # Key metrics for selected state
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Average Premium", f"${state_data['MEAN_PREMIUM']:,.0f}")
            
            with col2:
                st.metric("Minimum Premium", f"${state_data['MIN_PREMIUM']:,.0f}")
            
            with col3:
                st.metric("Maximum Premium", f"${state_data['MAX_PREMIUM']:,.0f}")
            
            with col4:
                volatility = (state_data['PREMIUM_STDDEV'] / state_data['MEAN_PREMIUM'] * 100)
                st.metric("Volatility (CV%)", f"{volatility:.1f}%")
            
            # Additional metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Standard Deviation", f"${state_data['PREMIUM_STDDEV']:,.0f}")
            
            with col2:
                price_range = state_data['MAX_PREMIUM'] - state_data['MIN_PREMIUM']
                st.metric("Price Range", f"${price_range:,.0f}")
            
            with col3:
                if yoy_growth is not None:
                    state_growth_data = yoy_growth[yoy_growth['STATE'] == selected_state]
                    if not state_growth_data.empty:
                        growth_pct = state_growth_data.iloc[0]['YOY_GROWTH_PCT']
                        st.metric("YoY Growth", f"{growth_pct:.2f}%")
                    else:
                        st.metric("YoY Growth", "N/A")
                else:
                    st.metric("YoY Growth", "N/A")
            
            with col4:
                # National ranking
                state_rank = (forecast_summary['MEAN_PREMIUM'] > state_data['MEAN_PREMIUM']).sum() + 1
                total_states = len(forecast_summary)
                st.metric("National Rank", f"#{state_rank} of {total_states}")
            
            # Comparison to national average
            st.markdown("#### 🎯 **Comparison to National Average**")
            
            national_avg = forecast_summary['MEAN_PREMIUM'].mean()
            diff_from_avg = state_data['MEAN_PREMIUM'] - national_avg
            pct_diff = (diff_from_avg / national_avg) * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Difference from National Avg", 
                    f"${diff_from_avg:,.0f}",
                    f"{pct_diff:+.1f}%"
                )
            
            with col2:
                if pct_diff > 10:
                    status = "🔴 Significantly Above Average"
                elif pct_diff > 0:
                    status = "🟡 Above Average"
                elif pct_diff > -10:
                    status = "🟢 Below Average"
                else:
                    status = "🟢 Significantly Below Average"
                
                st.info(f"**Status:** {status}")
            
            # Time series forecast for selected state
            if predictions is not None:
                state_predictions = predictions[predictions['SERIES'] == selected_state]
                
                if not state_predictions.empty:
                    st.markdown("#### 📈 **Premium Forecast Timeline**")
                    
                    # Create time series plot
                    fig_ts = go.Figure()
                    
                    # Sort by timestamp
                    state_predictions = state_predictions.sort_values('TS')
                    
                    # Add forecast line
                    fig_ts.add_trace(go.Scatter(
                        x=state_predictions['TS'],
                        y=state_predictions['FORECAST'],
                        mode='lines+markers',
                        name='Forecast',
                        line=dict(color='#1f77b4', width=3),
                        marker=dict(size=6)
                    ))
                    
                    # Add confidence intervals if available
                    if all(col in state_predictions.columns for col in ['UPPER_BOUND', 'LOWER_BOUND']):
                        # Upper bound
                        fig_ts.add_trace(go.Scatter(
                            x=state_predictions['TS'],
                            y=state_predictions['UPPER_BOUND'],
                            mode='lines',
                            name='Upper Bound',
                            line=dict(color='lightgray', width=1, dash='dash'),
                            showlegend=False
                        ))
                        
                        # Lower bound with fill
                        fig_ts.add_trace(go.Scatter(
                            x=state_predictions['TS'],
                            y=state_predictions['LOWER_BOUND'],
                            mode='lines',
                            name='Lower Bound',
                            line=dict(color='lightgray', width=1, dash='dash'),
                            fill='tonexty',
                            fillcolor='rgba(128,128,128,0.2)',
                            showlegend=False
                        ))
                    
                    fig_ts.update_layout(
                        title=f"Premium Forecast Timeline - {selected_state}",
                        xaxis_title="Date",
                        yaxis_title="Premium ($)",
                        height=450,
                        hovermode='x unified',
                        template='plotly_white'
                    )
                    
                    st.plotly_chart(fig_ts, use_container_width=True)
                    
                    # Forecast summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        avg_forecast = state_predictions['FORECAST'].mean()
                        st.metric("Avg Forecast Premium", f"${avg_forecast:,.0f}")
                    
                    with col2:
                        forecast_trend = state_predictions['FORECAST'].iloc[-1] - state_predictions['FORECAST'].iloc[0]
                        st.metric("Forecast Trend", f"${forecast_trend:,.0f}")
                    
                    with col3:
                        forecast_periods = len(state_predictions)
                        st.metric("Forecast Periods", f"{forecast_periods}")
                
                else:
                    st.info(f"📊 No forecast timeline data available for {selected_state}")
            else:
                st.info("📊 Forecast timeline data is not available")
    
    with tab4:
        st.subheader("📊 Cross-Metric Correlation Analysis")
        
        if yoy_growth is not None and len(yoy_growth) > 0:
            # Merge data for correlation analysis
            correlation_data = forecast_summary.merge(
                yoy_growth[['STATE', 'YOY_GROWTH_PCT']], 
                on='STATE', 
                how='inner'
            )
            
            if len(correlation_data) > 10:
                # Premium vs Growth scatter plot
                st.markdown("#### 💹 **Premium vs Growth Rate Analysis**")
                
                fig_scatter = px.scatter(
                    correlation_data,
                    x='MEAN_PREMIUM',
                    y='YOY_GROWTH_PCT',
                    hover_name='STATE',
                    title="Insurance Premium vs Growth Rate by State",
                    labels={
                        'MEAN_PREMIUM': 'Average Premium ($)',
                        'YOY_GROWTH_PCT': 'YoY Growth Rate (%)'
                    },
                    size='PREMIUM_STDDEV',
                    size_max=20
                )
                
                fig_scatter.update_layout(height=500)
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Correlation matrix
                st.markdown("#### 🔢 **Correlation Matrix**")
                
                # Select numeric columns for correlation
                numeric_cols = ['MEAN_PREMIUM', 'PREMIUM_STDDEV', 'MIN_PREMIUM', 'MAX_PREMIUM', 'YOY_GROWTH_PCT']
                available_cols = [col for col in numeric_cols if col in correlation_data.columns]
                
                if len(available_cols) > 1:
                    corr_matrix = correlation_data[available_cols].corr()
                    
                    # Create heatmap
                    fig_corr = px.imshow(
                        corr_matrix,
                        text_auto=True,
                        aspect="auto",
                        title="Correlation Matrix of Premium Metrics",
                        color_continuous_scale='RdBu_r'
                    )
                    
                    fig_corr.update_layout(height=400)
                    st.plotly_chart(fig_corr, use_container_width=True)
                    
                    # Insights
                    premium_growth_corr = corr_matrix.loc['MEAN_PREMIUM', 'YOY_GROWTH_PCT'] if 'YOY_GROWTH_PCT' in corr_matrix.columns else None
                    
                    if premium_growth_corr is not None:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Premium-Growth Correlation", f"{premium_growth_corr:.3f}")
                        
                        with col2:
                            if abs(premium_growth_corr) > 0.5:
                                strength = "Strong"
                            elif abs(premium_growth_corr) > 0.3:
                                strength = "Moderate"
                            else:
                                strength = "Weak"
                            
                            direction = "Positive" if premium_growth_corr > 0 else "Negative"
                            st.info(f"**Relationship:** {strength} {direction}")
            else:
                st.warning("⚠️ Insufficient data for correlation analysis (need >10 states with both metrics)")
        else:
            st.warning("⚠️ Growth data not available for correlation analysis")
    
    with tab5:
        st.subheader("📋 Raw Data Export and Inspection")
        
        # Data selector
        data_choice = st.selectbox(
            "📂 Select dataset to view:",
            ["Forecast Summary", "YoY Growth Data", "Sample Predictions"],
            help="Choose which dataset to display and download"
        )
        
        # Display and download logic
        if data_choice == "Forecast Summary":
            st.markdown("#### 📊 **Premium Forecast Summary Data**")
            st.dataframe(forecast_summary, use_container_width=True, height=400)
            
            # Download button
            csv_data = forecast_summary.to_csv(index=False)
            st.download_button(
                "📥 Download Forecast Summary CSV",
                csv_data,
                "insurance_forecast_summary.csv",
                "text/csv",
                help="Download complete forecast summary data"
            )
            
        elif data_choice == "YoY Growth Data" and yoy_growth is not None:
            st.markdown("#### 📈 **Year-over-Year Growth Data**")
            st.dataframe(yoy_growth, use_container_width=True, height=400)
            
            # Download button
            csv_data = yoy_growth.to_csv(index=False)
            st.download_button(
                "📥 Download Growth Data CSV",
                csv_data,
                "insurance_growth_data.csv",
                "text/csv"
            )
            
        elif data_choice == "Sample Predictions" and predictions is not None:
            st.markdown("#### 🔮 **Premium Predictions Data**")
            st.dataframe(predictions, use_container_width=True, height=400)
            
            # Download button
            csv_data = predictions.to_csv(index=False)
            st.download_button(
                "📥 Download Predictions CSV",
                csv_data,
                "insurance_predictions.csv",
                "text/csv"
            )
        else:
            st.error(f"❌ {data_choice} is not available")
        
        # Data summary statistics
        if data_choice == "Forecast Summary":
            st.markdown("#### 📈 **Data Summary Statistics**")
            st.dataframe(forecast_summary.describe(), use_container_width=True)

else:
    # Error state - no data loaded
    st.error("❌ **Critical Error:** Unable to load insurance forecast data")
    
    st.markdown(f"""
    ### 🔧 **Troubleshooting Steps:**
    
    **Required Tables & Permissions:**
    - `{FORECAST_TABLE}` ✅
    - `INSURANCE_ANALYTICS.POLICY_DATA.yoy_growth_all_states` ⚠️ (Optional)
    - `INSURANCE_ANALYTICS.POLICY_DATA.premium_predictions_12months` ⚠️ (Optional)
    
    **Setup Instructions:**
    1. 🏃‍♂️ **Run the forecasting model:** Execute `premium_forecasting_model.sql` script first
    2. 🔐 **Check permissions:** Ensure you have SELECT access to the database and schema
    3. ⚡ **Verify warehouse:** Confirm your warehouse is running and accessible
    4. 📊 **Validate data:** Check that tables contain data using basic SQL queries
    
    **Quick Validation Query:**
    ```sql
    SELECT COUNT(*) as record_count 
    FROM {FORECAST_TABLE};
    ```
    """)
    
    # Show connection test
    try:
        test_query = "SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()"
        connection_info = session.sql(test_query).collect()[0]
        
        st.success("✅ **Connection Status:** Connected to Snowflake")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Warehouse:** {connection_info[0]}")
        with col2:
            st.info(f"**Database:** {connection_info[1]}")
        with col3:
            st.info(f"**Schema:** {connection_info[2]}")
            
    except Exception as e:
        st.error(f"❌ **Connection Error:** {str(e)}")

# ========== FOOTER ==========
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px;'>
    <h4>📊 Insurance Premium Forecasting Dashboard</h4>
    <p><strong>Built with Snowflake + Streamlit</strong> | 
    <em>Real-time analytics for insurance premium forecasting</em></p>
    <p><small>Data refreshed automatically • Interactive visualizations • Export capabilities</small></p>
</div>
""", unsafe_allow_html=True)