-- Premium Forecasting Model using SNOWFLAKE.ML.FORECAST
-- Predicts insurance premiums by state for future years (e.g., 2026)
-- 
-- Usage: This script creates a forecasting model for all 50 states
--        and provides sample queries to predict premiums for any state/year

-- Configuration Variables
SET source_table = 'insurance_analytics.policy_data.premium_view_normalized';

USE DATABASE insurance_analytics;
USE SCHEMA policy_data;

-- Step 1: Verify training data from source table
SELECT 
    state,
    MIN(policy_effective_date) as earliest_date,
    MAX(policy_effective_date) as latest_date,
    COUNT(*) as data_points
FROM IDENTIFIER($source_table)
GROUP BY state
ORDER BY state;

-- Step 2: Create forecasting model for all states
-- This trains one model per state (50 models total)
-- Note: Using direct table reference since SYSTEM$QUERY_REFERENCE requires string literal
-- See https://docs.snowflake.com/en/user-guide/ml-functions/preprocessing#overriding-by-kind-of-value
SET model_query = 'SELECT state as series_id, policy_effective_date as timestamp_col, premium_12mo as target_value FROM ' || $source_table || ' WHERE policy_effective_date IS NOT NULL AND premium_12mo IS NOT NULL';

CREATE OR REPLACE SNOWFLAKE.ML.FORECAST premium_forecast_model(
    INPUT_DATA => SYSTEM$QUERY_REFERENCE($model_query),
    SERIES_COLNAME => 'SERIES_ID',
    TIMESTAMP_COLNAME => 'TIMESTAMP_COL',
    TARGET_COLNAME => 'TARGET_VALUE',
    CONFIG_OBJECT => {
        'method': 'best',
        'on_error': 'SKIP',
        'evaluate': TRUE
    }
)
COMMENT = 'Multi-state premium forecasting model for predicting insurance prices by state and year';

-- Step 3: Check model evaluation metrics
CALL premium_forecast_model!SHOW_EVALUATION_METRICS();

-- Step 4: Check feature importance
CALL premium_forecast_model!EXPLAIN_FEATURE_IMPORTANCE();

-- Step 5: Check for any training errors
CALL premium_forecast_model!SHOW_TRAINING_LOGS();

-- ================================================================================
-- SAMPLE USAGE: Predict premiums for all states for next 12 months
-- ================================================================================

-- Generate 12-month forecasts for all states and save to table
CREATE OR REPLACE TABLE INSURANCE_ANALYTICS.POLICY_DATA.premium_predictions_12months AS
SELECT * FROM TABLE(premium_forecast_model!FORECAST(FORECASTING_PERIODS => 12));

-- Aggregate statistics by state for the 12-month forecast period
CREATE OR REPLACE TABLE INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary AS
SELECT 
    SERIES as state,
    MIN(TS) as forecast_start_date,
    MAX(TS) as forecast_end_date,
    AVG(FORECAST) as mean_premium,
    MIN(FORECAST) as min_premium,
    MAX(FORECAST) as max_premium,
    STDDEV(FORECAST) as premium_stddev,
    AVG(LOWER_BOUND) as avg_lower_bound,
    AVG(UPPER_BOUND) as avg_upper_bound
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_predictions_12months
GROUP BY SERIES
ORDER BY state;

SELECT * FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary;

-- ================================================================================
-- ADDITIONAL EXAMPLES: Individual state predictions
-- ================================================================================

-- Example 1: View detailed predictions for South Dakota (SD)
SELECT * 
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_predictions_12months
WHERE SERIES = 'SD'
ORDER BY TS;

-- Example 2: View detailed predictions for Florida (FL)
SELECT * 
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_predictions_12months
WHERE SERIES = 'FL'
ORDER BY TS;

-- Example 3: Compare top 10 states by forecasted average premium
SELECT 
    state,
    mean_premium,
    min_premium,
    max_premium,
    (max_premium - min_premium) as price_range
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary
ORDER BY mean_premium DESC
LIMIT 10;

-- Example 4: Calculate year-over-year growth for all states
CREATE OR REPLACE TABLE INSURANCE_ANALYTICS.POLICY_DATA.yoy_growth_all_states AS
WITH historical_avg AS (
    SELECT 
        state,
        AVG(premium_12mo) as avg_premium_historical
    FROM IDENTIFIER($source_table)
    WHERE policy_effective_date >= DATEADD(month, -12, CURRENT_DATE())
    GROUP BY state
)
SELECT 
    f.state,
    h.avg_premium_historical as trailing_12mo_avg,
    f.mean_premium as forecast_12mo_avg,
    ((f.mean_premium - h.avg_premium_historical) / h.avg_premium_historical * 100) as yoy_growth_pct,
    f.min_premium,
    f.max_premium
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary f
LEFT JOIN historical_avg h ON f.state = h.state
ORDER BY yoy_growth_pct DESC;

SELECT * FROM INSURANCE_ANALYTICS.POLICY_DATA.yoy_growth_all_states;

-- Example 5: Identify states with highest volatility (price fluctuation)
SELECT 
    state,
    mean_premium,
    premium_stddev,
    (premium_stddev / mean_premium * 100) as coefficient_of_variation_pct
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary
ORDER BY premium_stddev DESC
LIMIT 10;

-- Example 6: Monthly trend analysis for specific states
SELECT 
    SERIES as state,
    TS as forecast_date,
    FORECAST as predicted_premium,
    LOWER_BOUND,
    UPPER_BOUND,
    (UPPER_BOUND - LOWER_BOUND) as prediction_interval_width
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_predictions_12months
WHERE SERIES IN ('CA', 'TX', 'FL', 'NY', 'SD')
ORDER BY state, forecast_date;

-- ================================================================================
-- UTILITY QUERIES
-- ================================================================================

-- View model details
SHOW SNOWFLAKE.ML.FORECAST LIKE 'premium_forecast_model';

-- Drop model if needed
-- DROP SNOWFLAKE.ML.FORECAST premium_forecast_model;

-- Refresh model with new data (requires recreating)
-- CREATE OR REPLACE SNOWFLAKE.ML.FORECAST premium_forecast_model(...);
