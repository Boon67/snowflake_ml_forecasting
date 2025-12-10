# Insurance Premium Forecasting with Snowflake ML

Time series forecasting model for predicting automotive insurance premiums by state using Snowflake's ML.FORECAST function.

## Overview

This project creates a multi-state forecasting model that predicts insurance premiums 12 months into the future for all 50 US states. It uses synthetic data generation for training and provides comprehensive analysis tools.

## Project Components

### 1. Data Setup (`insurance_analytics_setup.sql`)
Generates synthetic automotive insurance data with configurable parameters:

**Configuration Variables:**
- `start_date` - Starting date for data generation (default: '2020-01-01')
- `months_of_data` - Number of months to generate (default: 72 = 6 years)

**Features:**
- Creates database and schema structure
- Generates carrier performance data across 50 states
- Creates normalized view for time series modeling
- Includes validation queries

**Objects Created:**
- `insurance_analytics.policy_data.carrier_product_performance_dim` - Raw policy data
- `insurance_analytics.policy_data.premium_view_normalized` - Aggregated monthly premiums by state

### 2. Forecasting Model (`premium_forecasting_model.sql`)
Builds and deploys the ML forecasting model with sample usage examples.

**Configuration Variables:**
- `source_table` - Source table/view for training data (default: 'insurance_analytics.policy_data.premium_view_normalized')

**Model Features:**
- Multi-series forecasting (one model per state)
- Uses 'best' method (ensemble of Prophet, ARIMA, Exponential Smoothing, GBM)
- Error handling with 'SKIP' mode for problematic states
- Evaluation metrics enabled

**Objects Created:**
- `premium_forecast_model` - ML model instance
- `premium_predictions_12months` - Detailed monthly forecasts for all states
- `premium_forecast_summary` - Aggregated statistics (mean, min, max) per state
- `yoy_growth_all_states` - Year-over-year growth analysis

## Quick Start

### Step 1: Generate Training Data
```sql
-- Configure and run data setup
SET start_date = '2020-01-01';
SET months_of_data = 72;

-- Execute insurance_analytics_setup.sql
```

### Step 2: Train Forecasting Model
```sql
-- Configure source and train model
SET source_table = 'insurance_analytics.policy_data.premium_view_normalized';

-- Execute premium_forecasting_model.sql
```

### Step 3: View Results
```sql
-- View summary statistics for all states
SELECT * FROM insurance_analytics.policy_data.premium_forecast_summary
ORDER BY mean_premium DESC;

-- View detailed predictions for a specific state
SELECT * FROM insurance_analytics.policy_data.premium_predictions_12months
WHERE SERIES = 'CA'
ORDER BY TS;

-- View year-over-year growth analysis
SELECT * FROM insurance_analytics.policy_data.yoy_growth_all_states
ORDER BY yoy_growth_pct DESC;
```

## Key Outputs

### Premium Forecast Summary Table
Aggregated statistics per state:
- `state` - State abbreviation
- `forecast_start_date` - First forecast date
- `forecast_end_date` - Last forecast date
- `mean_premium` - Average premium over 12 months
- `min_premium` - Minimum monthly premium
- `max_premium` - Maximum monthly premium
- `premium_stddev` - Standard deviation
- `avg_lower_bound` - Average 95% confidence interval lower bound
- `avg_upper_bound` - Average 95% confidence interval upper bound

### Premium Predictions Table
Detailed monthly forecasts:
- `SERIES` - State code
- `TS` - Forecast timestamp
- `FORECAST` - Predicted premium value
- `LOWER_BOUND` - Lower confidence bound (95%)
- `UPPER_BOUND` - Upper confidence bound (95%)

### YoY Growth Analysis Table
Growth comparison:
- `state` - State abbreviation
- `trailing_12mo_avg` - Historical average (last 12 months)
- `forecast_12mo_avg` - Forecasted average (next 12 months)
- `yoy_growth_pct` - Year-over-year growth percentage
- `min_premium` - Minimum forecasted premium
- `max_premium` - Maximum forecasted premium

## Sample Analysis Queries

### Top 10 Most Expensive States
```sql
SELECT state, mean_premium, min_premium, max_premium
FROM insurance_analytics.policy_data.premium_forecast_summary
ORDER BY mean_premium DESC
LIMIT 10;
```

### States with Highest Price Volatility
```sql
SELECT state, mean_premium, premium_stddev,
       (premium_stddev / mean_premium * 100) as cv_pct
FROM insurance_analytics.policy_data.premium_forecast_summary
ORDER BY premium_stddev DESC
LIMIT 10;
```

### Fastest Growing Markets
```sql
SELECT state, trailing_12mo_avg, forecast_12mo_avg, yoy_growth_pct
FROM insurance_analytics.policy_data.yoy_growth_all_states
ORDER BY yoy_growth_pct DESC
LIMIT 10;
```

## Model Evaluation

Check model performance metrics:
```sql
CALL premium_forecast_model!SHOW_EVALUATION_METRICS();
```

View feature importance:
```sql
CALL premium_forecast_model!EXPLAIN_FEATURE_IMPORTANCE();
```

Check training errors:
```sql
CALL premium_forecast_model!SHOW_TRAINING_LOGS();
```

## Technical Details

### Data Generation
- Synthetic data spans configurable time periods
- Premium pricing varies by state tier (CA/NY/FL highest, TX/IL/OH mid, others lower)
- Includes time-based price inflation (~5-8% annual growth)
- Random variation added for realism
- Limited states (WY, VT) have reduced sample sizes

### Model Configuration
- **Algorithm**: 'best' (ensemble approach)
- **Series**: 50 individual state models
- **Evaluation**: Cross-validation enabled
- **Error Handling**: Skip problematic states
- **Forecast Horizon**: 12 months ahead

### Warehouse Recommendations
- **Standard warehouse (XS-S)**: Suitable for this dataset size
- **Training time**: Approximately 5-10 minutes for all 50 states
- **Inference time**: < 1 minute for all states

## Customization

### Adjust Forecast Horizon
```sql
-- Forecast 24 months instead of 12
CREATE OR REPLACE TABLE premium_predictions_24months AS
SELECT * FROM TABLE(premium_forecast_model!FORECAST(FORECASTING_PERIODS => 24));
```

### Forecast Specific States Only
```sql
-- Predict for California only
SELECT * FROM TABLE(premium_forecast_model!FORECAST(
    SERIES_VALUE => TO_VARIANT('CA'),
    FORECASTING_PERIODS => 12
));
```

### Retrain Model with New Data
```sql
-- Refresh data and retrain
CREATE OR REPLACE SNOWFLAKE.ML.FORECAST premium_forecast_model(...);
```

## Notes

- Models are immutable - retrain to incorporate new data
- Training data should be updated regularly for best accuracy
- Forecast accuracy degrades beyond 12-18 months
- Review evaluation metrics to assess model quality
- Consider retraining monthly or quarterly

## Requirements

- Snowflake account with ML Functions enabled
- CREATE SNOWFLAKE.ML.FORECAST privilege on schema
- Sufficient warehouse compute for model training
- Database creation privileges

## License

This is a demonstration project for educational purposes.
