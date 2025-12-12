"""
Insurance Premium Forecasting Dashboard - Modular Version
Main application file that imports from separate modules
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

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
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏆 State Rankings",
        "📈 Growth Analysis",
        "🔍 State Deep Dive",
        "📊 Correlation Analysis",
        "📋 Raw Data"
    ])
    
    # ========== TAB 1: State Rankings ==========
    with tab1:
        st.markdown("## 🏆 State Performance Rankings")
        
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
    
    # ========== TAB 2: Growth Analysis ==========
    with tab2:
        st.markdown("## 📈 YoY Growth Analysis")
        
        if yoy_growth is not None and len(yoy_growth) > 0:
            # Growth distribution
            import plotly.express as px
            
            st.markdown("### 📊 Growth Distribution Across States")
            fig_hist = px.histogram(
                yoy_growth,
                x='YOY_GROWTH_PCT',
                nbins=30,
                title='Distribution of YoY Growth Rates',
                labels={'YOY_GROWTH_PCT': 'YoY Growth (%)'},
                color_discrete_sequence=['#1f77b4']
            )
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # Top and bottom growth states
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🚀 Top 10 Growth Leaders")
                top_growth = yoy_growth.nlargest(10, 'YOY_GROWTH_PCT')[['STATE', 'YOY_GROWTH_PCT']]
                st.dataframe(top_growth.reset_index(drop=True), use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("### 📉 Bottom 10 Growth States")
                bottom_growth = yoy_growth.nsmallest(10, 'YOY_GROWTH_PCT')[['STATE', 'YOY_GROWTH_PCT']]
                st.dataframe(bottom_growth.reset_index(drop=True), use_container_width=True, hide_index=True)
            
            # Growth statistics
            st.markdown("### 📊 Growth Statistics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Average Growth", f"{yoy_growth['YOY_GROWTH_PCT'].mean():.2f}%")
            with col2:
                st.metric("Median Growth", f"{yoy_growth['YOY_GROWTH_PCT'].median():.2f}%")
            with col3:
                st.metric("Std Deviation", f"{yoy_growth['YOY_GROWTH_PCT'].std():.2f}%")
            with col4:
                positive_growth = (yoy_growth['YOY_GROWTH_PCT'] > 0).sum()
                st.metric("States with Positive Growth", f"{positive_growth}/{len(yoy_growth)}")
        else:
            st.info("No YoY growth data available")
    
    # ========== TAB 3: State Deep Dive ==========
    with tab3:
        st.markdown("## 🔍 State Deep Dive")
        
        # State selector
        selected_state = st.selectbox(
            "Select a State",
            options=sorted(forecast_summary['STATE'].unique()),
            help="Choose a state to view detailed analysis"
        )
        
        if selected_state:
            state_data = forecast_summary[forecast_summary['STATE'] == selected_state].iloc[0]
            
            # State header
            st.markdown(f"### Analysis for {selected_state}")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mean Premium", f"${state_data['MEAN_PREMIUM']:,.2f}")
            with col2:
                st.metric("Std Deviation", f"${state_data['PREMIUM_STDDEV']:,.2f}")
            with col3:
                st.metric("Min Premium", f"${state_data['MIN_PREMIUM']:,.2f}")
            with col4:
                st.metric("Max Premium", f"${state_data['MAX_PREMIUM']:,.2f}")
            
            # Additional metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                price_range = state_data['MAX_PREMIUM'] - state_data['MIN_PREMIUM']
                st.metric("Price Range", f"${price_range:,.2f}")
            
            with col2:
                volatility = (state_data['PREMIUM_STDDEV'] / state_data['MEAN_PREMIUM'] * 100)
                st.metric("Volatility (CV%)", f"{volatility:.1f}%")
            
            with col3:
                if yoy_growth is not None and len(yoy_growth) > 0:
                    state_growth = yoy_growth[yoy_growth['STATE'] == selected_state]
                    if not state_growth.empty:
                        growth_val = state_growth.iloc[0]['YOY_GROWTH_PCT']
                        st.metric("YoY Growth", f"{growth_val:.2f}%", delta=f"{growth_val:.2f}%")
                    else:
                        st.metric("YoY Growth", "N/A")
                else:
                    st.metric("YoY Growth", "N/A")
            
            with col4:
                # Calculate national rank
                ranked = forecast_summary.sort_values('MEAN_PREMIUM', ascending=False).reset_index(drop=True)
                rank = ranked[ranked['STATE'] == selected_state].index[0] + 1
                st.metric("National Rank", f"#{rank} of {len(forecast_summary)}")
            
            # Comparison to National Average
            st.markdown("---")
            st.markdown("### 📊 Comparison to National Average")
            
            national_avg = forecast_summary['MEAN_PREMIUM'].mean()
            diff_from_avg = state_data['MEAN_PREMIUM'] - national_avg
            pct_diff = (diff_from_avg / national_avg) * 100
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric(
                    "Difference from National Avg",
                    f"${diff_from_avg:,.0f}",
                    delta=f"{pct_diff:.1f}%"
                )
            
            with col2:
                if diff_from_avg < 0:
                    status = "🟢 Below Average"
                    status_color = "#d4edda"
                elif diff_from_avg > 0:
                    status = "🔴 Above Average"
                    status_color = "#f8d7da"
                else:
                    status = "⚪ At Average"
                    status_color = "#e2e3e5"
                
                st.markdown(f"""
                <div style="background-color: {status_color}; padding: 20px; border-radius: 5px; text-align: center;">
                    <h3 style="margin: 0;">Status: {status}</h3>
                </div>
                """, unsafe_allow_html=True)
            
            # Premium Forecast Timeline
            st.markdown("---")
            st.markdown("### 📈 Premium Forecast Timeline")
            
            if predictions_12mo is not None and len(predictions_12mo) > 0:
                # Filter predictions for selected state
                state_predictions = predictions_12mo[predictions_12mo['SERIES'] == selected_state]
                
                if not state_predictions.empty:
                    # Create timeline chart
                    fig_timeline = go.Figure()
                    
                    # Add the forecast line
                    fig_timeline.add_trace(go.Scatter(
                        x=state_predictions['TS'],
                        y=state_predictions['FORECAST'],
                        mode='lines',
                        name='Forecast',
                        line=dict(color='#1f77b4', width=3)
                    ))
                    
                    # Add confidence interval if available
                    if 'UPPER_BOUND' in state_predictions.columns and 'LOWER_BOUND' in state_predictions.columns:
                        fig_timeline.add_trace(go.Scatter(
                            x=state_predictions['TS'],
                            y=state_predictions['UPPER_BOUND'],
                            mode='lines',
                            name='Upper Bound',
                            line=dict(width=0),
                            showlegend=False
                        ))
                        
                        fig_timeline.add_trace(go.Scatter(
                            x=state_predictions['TS'],
                            y=state_predictions['LOWER_BOUND'],
                            mode='lines',
                            name='Lower Bound',
                            line=dict(width=0),
                            fillcolor='rgba(31, 119, 180, 0.2)',
                            fill='tonexty',
                            showlegend=False
                        ))
                    
                    fig_timeline.update_layout(
                        title=f'Premium Forecast Timeline - {selected_state}',
                        xaxis_title='Date',
                        yaxis_title='Premium ($)',
                        hovermode='x unified',
                        height=400
                    )
                    
                    st.plotly_chart(fig_timeline, use_container_width=True)
                    
                    # Forecast statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        avg_forecast = state_predictions['FORECAST'].mean()
                        st.metric("Average Forecast", f"${avg_forecast:,.2f}")
                    with col2:
                        trend = state_predictions['FORECAST'].iloc[-1] - state_predictions['FORECAST'].iloc[0]
                        st.metric("Trend", f"${trend:,.2f}")
                    with col3:
                        forecast_vol = state_predictions['FORECAST'].std()
                        st.metric("Forecast Volatility", f"${forecast_vol:,.2f}")
                else:
                    st.info(f"No forecast data available for {selected_state}")
            else:
                st.info("No 12-month prediction data available")
    
    # ========== TAB 4: Correlation Analysis ==========
    with tab4:
        st.markdown("## 📊 Correlation Analysis")
        
        # Merge all data for correlation
        corr_data = forecast_summary.copy()
        if yoy_growth is not None and len(yoy_growth) > 0:
            corr_data = corr_data.merge(yoy_growth[['STATE', 'YOY_GROWTH_PCT']], on='STATE', how='left')
        
        # Calculate additional metrics
        corr_data['PRICE_RANGE'] = corr_data['MAX_PREMIUM'] - corr_data['MIN_PREMIUM']
        corr_data['VOLATILITY'] = (corr_data['PREMIUM_STDDEV'] / corr_data['MEAN_PREMIUM'] * 100)
        
        # Select numeric columns for correlation
        numeric_cols = ['MEAN_PREMIUM', 'PREMIUM_STDDEV', 'MIN_PREMIUM', 'MAX_PREMIUM', 
                       'PRICE_RANGE', 'VOLATILITY']
        if 'YOY_GROWTH_PCT' in corr_data.columns:
            numeric_cols.append('YOY_GROWTH_PCT')
        
        correlation_data = corr_data[numeric_cols].corr()
        
        # Create heatmap
        import plotly.graph_objects as go
        
        fig = go.Figure(data=go.Heatmap(
            z=correlation_data.values,
            x=correlation_data.columns,
            y=correlation_data.columns,
            colorscale='RdBu',
            zmid=0,
            text=correlation_data.values.round(2),
            texttemplate='%{text}',
            textfont={"size": 10},
            colorbar=dict(title="Correlation")
        ))
        
        fig.update_layout(
            title='Correlation Matrix of Premium Metrics',
            xaxis_title='',
            yaxis_title='',
            height=600
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Scatter plots for key relationships
        st.markdown("### Key Relationships")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'YOY_GROWTH_PCT' in corr_data.columns:
                fig_scatter1 = px.scatter(
                    corr_data,
                    x='MEAN_PREMIUM',
                    y='YOY_GROWTH_PCT',
                    title='Mean Premium vs YoY Growth',
                    labels={'MEAN_PREMIUM': 'Mean Premium ($)', 'YOY_GROWTH_PCT': 'YoY Growth (%)'},
                    trendline='ols'
                )
                st.plotly_chart(fig_scatter1, use_container_width=True)
        
        with col2:
            fig_scatter2 = px.scatter(
                corr_data,
                x='MEAN_PREMIUM',
                y='VOLATILITY',
                title='Mean Premium vs Volatility',
                labels={'MEAN_PREMIUM': 'Mean Premium ($)', 'VOLATILITY': 'Volatility (%)'},
                trendline='ols'
            )
            st.plotly_chart(fig_scatter2, use_container_width=True)
    
    # ========== TAB 5: Raw Data ==========
    with tab5:
        st.markdown("## 📋 Raw Data")
        
        st.markdown("### Forecast Summary Data")
        st.dataframe(forecast_summary, use_container_width=True)
        
        # Download button
        csv = forecast_summary.to_csv(index=False)
        st.download_button(
            label="📥 Download Forecast Data as CSV",
            data=csv,
            file_name="premium_forecast_summary.csv",
            mime="text/csv"
        )
        
        if yoy_growth is not None and len(yoy_growth) > 0:
            st.markdown("### YoY Growth Data")
            st.dataframe(yoy_growth, use_container_width=True)
            
            csv_growth = yoy_growth.to_csv(index=False)
            st.download_button(
                label="📥 Download YoY Growth Data as CSV",
                data=csv_growth,
                file_name="yoy_growth_data.csv",
                mime="text/csv"
            )
else:
    st.error("❌ Could not load data. Please check table configuration.")
    st.info(f"📋 Configured table: `{DEFAULT_TABLE}`")

