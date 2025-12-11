# Insurance Premium Forecasting Dashboard

An interactive Streamlit dashboard for analyzing insurance premium forecasts across US states, deployed on Snowflake.

![Insurance Premium Forecasting Dashboard](screenshots/Insurance_Premium_forecasting.gif)

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Deployment](#deployment)
- [Data Requirements](#data-requirements)
- [Usage Guide](#usage-guide)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Maintenance](#maintenance)
- [Recent Changes](#recent-changes)

---

## 📊 Overview

This dashboard provides comprehensive analytics for insurance premium data including:
- **Interactive US choropleth maps** - Visualize metrics across all US states
- **State-by-state premium comparisons** - Rankings and performance analysis
- **Year-over-year growth analysis** - Track premium trends over time
- **Premium forecasting and predictions** - 12-month forward projections
- **Cross-metric correlation analysis** - Understand relationships between metrics
- **Data export capabilities** - Download data for offline analysis

### Technology Stack
- **Frontend:** Streamlit
- **Visualization:** Plotly Express & Graph Objects
- **Data Processing:** Pandas, NumPy
- **Backend:** Snowflake Snowpark
- **Deployment:** Snow CLI

---

## ⚡ Quick Start

### 1. Install Prerequisites

```bash
# Install Snow CLI
pip install snowflake-cli-labs

# Test connection (assumes Snow CLI is already configured)
snow connection test
```

### 2. Deploy to Snowflake

```bash
# Navigate to project directory
cd /path/to/streamlit_insurance_premium_analysis

# Deploy with one command
./deploy.sh
```

### 3. Access Your Dashboard

1. Open Snowsight: https://app.snowflake.com
2. Navigate to **Streamlit** in the left menu
3. Click on **INSURANCE_PREMIUM_DASHBOARD**
4. Dashboard loads automatically!

---

## 🎯 Features

### Interactive US Map
- Visualize multiple metrics across all US states
- Color-coded choropleth map with hover details
- Selectable metrics:
  - **Mean Premium** - Average insurance premium by state
  - **YoY Growth %** - Year-over-year growth percentage
  - **Premium Volatility** - Coefficient of variation
  - **Price Range** - Difference between min and max premiums

### State Rankings
- Top 10 highest and lowest premium states
- Premium distribution analysis with histograms
- Summary statistics (median, std dev, IQR, range)

### Growth Analysis
- YoY growth rate distribution
- Fastest and slowest growing states
- Growth statistics and trends
- Historical vs forecast comparisons

### State Deep Dive
- Individual state analytics and metrics
- Comparison to national averages
- Premium forecast timelines with confidence intervals
- State-specific performance indicators

### Correlation Analysis
- Premium vs growth rate scatter plots
- Correlation matrices for all metrics
- Relationship strength indicators
- Visual insights into metric relationships

### Data Export
- Download raw data as CSV
- Export all three data tables
- Summary statistics included
- Perfect for offline analysis

---

## 📋 Prerequisites

### Required Software
- **Snow CLI** installed and configured
  ```bash
  pip install snowflake-cli-labs
  snow connection test
  ```
- Snow CLI must have **default connection** configured
- Connection needs **CREATE STREAMLIT** permissions on `INSURANCE_ANALYTICS.PUBLIC`

### Snowflake Requirements
- Active Snowflake account
- Access to `INSURANCE_ANALYTICS` database
- `ACCOUNTADMIN` or `SYSADMIN` role (for deployment)
- Access to `COMPUTE_WH` warehouse (or configure different warehouse)

### Required Data Tables
The dashboard needs these tables in `INSURANCE_ANALYTICS.POLICY_DATA`:

#### 1. premium_forecast_summary (Required)
```sql
STATE               VARCHAR(2)      -- State codes: CA, NY, TX, etc.
MEAN_PREMIUM        NUMBER          -- Average premium
PREMIUM_STDDEV      NUMBER          -- Standard deviation
MIN_PREMIUM         NUMBER          -- Minimum premium
MAX_PREMIUM         NUMBER          -- Maximum premium
```

#### 2. yoy_growth_all_states (Optional)
```sql
STATE               VARCHAR(2)      -- State codes
YOY_GROWTH_PCT      NUMBER          -- Growth percentage
TRAILING_12MO_AVG   NUMBER          -- Historical average
FORECAST_12MO_AVG   NUMBER          -- Forecast average
```

#### 3. premium_predictions_12months (Optional)
```sql
SERIES              VARCHAR(2)      -- State codes
TS                  TIMESTAMP       -- Prediction timestamp
FORECAST            NUMBER          -- Forecasted value
UPPER_BOUND         NUMBER          -- Upper confidence bound
LOWER_BOUND         NUMBER          -- Lower confidence bound
```

**Important:** The STATE/SERIES columns must contain **2-letter state codes** (e.g., 'CA', 'NY', 'TX'), not full state names.

---

## 🚀 Deployment

### Method 1: Using Deploy Script (Recommended)

```bash
# Navigate to project directory
cd /path/to/streamlit_insurance_premium_analysis

# Run deployment script
./deploy.sh
```

The script will:
- ✓ Check Snow CLI is installed and configured
- ✓ Validate required files exist
- ✓ Deploy to INSURANCE_ANALYTICS.PUBLIC
- ✓ Create stage automatically
- ✓ Upload streamlit_app.py
- ✓ Create Streamlit application
- ✓ Display access URL and instructions

### Method 2: Using Snow CLI Directly

```bash
# Deploy with Snow CLI
snow streamlit deploy \
    --database "INSURANCE_ANALYTICS" \
    --schema "PUBLIC" \
    --replace
```

**Note:** Requires `snowflake.yml` configuration file (included in project).

### Method 3: Manual Deployment via Snowsight UI

1. Navigate to **Streamlit** section in Snowsight
2. Click **+ Streamlit App**
3. Configure:
   - **App Name:** INSURANCE_PREMIUM_DASHBOARD
   - **Location:** INSURANCE_ANALYTICS.PUBLIC
   - **Warehouse:** COMPUTE_WH
4. Copy contents of `streamlit_app.py` into editor
5. Click **Run** to deploy

### Verify Deployment

```bash
# Get app URL
snow streamlit get-url insurance_premium_dashboard

# Describe app
snow streamlit describe insurance_premium_dashboard

# List all Streamlit apps
snow streamlit list
```

---

## 📊 Data Requirements

### Verify Your Data

Before deploying, ensure your tables exist and contain the correct format:

```sql
-- Check if tables exist
SELECT COUNT(*) as record_count 
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary;

SELECT COUNT(*) as record_count 
FROM INSURANCE_ANALYTICS.POLICY_DATA.yoy_growth_all_states;

SELECT COUNT(*) as record_count 
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_predictions_12months;

-- Verify STATE column format (should return: CA, NY, TX, etc.)
SELECT DISTINCT STATE 
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary 
ORDER BY STATE;
```

### STATE Column Format

The dashboard expects **2-letter state codes**, not full names:

✅ **Correct:** CA, NY, TX, FL, WA
❌ **Incorrect:** California, New York, Texas, Florida, Washington

If your data has full state names, you'll need to convert them before deployment.

---

## 💻 Usage Guide

### Accessing the Dashboard

1. **Open Snowsight**
   - Navigate to https://app.snowflake.com
   - Log in with your credentials

2. **Find the App**
   - Click **Streamlit** in the left navigation
   - Locate **INSURANCE_PREMIUM_DASHBOARD**
   - Click to launch

### Dashboard Sections

#### 1. KPI Metrics Row
- National average premium
- Average YoY growth percentage
- Highest premium state
- Lowest premium state

#### 2. Interactive US Map
- **Select Metric:** Choose which metric to visualize
- **Color Coding:** States colored by metric value
- **Hover Details:** See state name and exact values
- **Debug Mode:** Enable "Show Debug Info" for data validation

#### 3. State Rankings Tab
- View top 10 and bottom 10 states by premium
- See premium distribution histogram
- Review summary statistics

#### 4. Growth Analysis Tab
- Analyze YoY growth rates
- Compare fastest vs slowest growing states
- View growth distribution

#### 5. State Deep Dive Tab
- Select any state for detailed analysis
- Compare to national averages
- View forecast timeline
- See state ranking

#### 6. Correlation Analysis Tab
- Scatter plots of premium vs growth
- Correlation matrix heatmap
- Relationship insights

#### 7. Raw Data Tab
- Browse all data tables
- Download as CSV
- View summary statistics

---

## ⚙️ Configuration

### Customize Warehouse

Edit `snowflake.yml`:
```yaml
streamlit:
  query_warehouse: YOUR_WAREHOUSE_NAME  # Change from COMPUTE_WH
```

### Deploy to Different Database/Schema

Modify deploy command:
```bash
snow streamlit deploy \
    --database "YOUR_DATABASE" \
    --schema "YOUR_SCHEMA" \
    --replace
```

### Grant User Access

```sql
-- Grant access to the Streamlit app
GRANT USAGE ON STREAMLIT INSURANCE_ANALYTICS.PUBLIC.INSURANCE_PREMIUM_DASHBOARD 
TO ROLE YOUR_USER_ROLE;

-- Grant access to data tables
GRANT SELECT ON ALL TABLES IN SCHEMA INSURANCE_ANALYTICS.POLICY_DATA 
TO ROLE YOUR_USER_ROLE;

-- Grant warehouse usage
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE YOUR_USER_ROLE;
```

---

## 🔧 Troubleshooting

### Issue: Blank Map Display

**Symptoms:** Map shows but no states are colored

**Solutions:**
1. Enable **"Show Debug Info"** checkbox in the app
2. Check STATE column format:
   ```sql
   SELECT DISTINCT STATE FROM premium_forecast_summary;
   ```
   Should return: CA, NY, TX, etc. (2-letter codes)
3. Verify numeric values in metric columns:
   ```sql
   SELECT STATE, MEAN_PREMIUM 
   FROM premium_forecast_summary 
   WHERE MEAN_PREMIUM IS NULL;
   ```
4. Check for data type issues in debug panel

### Issue: "Table not found" Error

**Solutions:**
1. Verify tables exist:
   ```sql
   SHOW TABLES IN SCHEMA INSURANCE_ANALYTICS.POLICY_DATA;
   ```
2. Run forecasting model SQL scripts to populate tables
3. Check permissions:
   ```sql
   SHOW GRANTS ON SCHEMA INSURANCE_ANALYTICS.POLICY_DATA;
   ```

### Issue: Deployment Failed

**Solutions:**
1. Verify Snow CLI configuration:
   ```bash
   snow connection test
   ```
2. Check permissions:
   - Need CREATE STREAMLIT on target schema
   - Need USAGE on database
3. Verify database exists:
   ```sql
   SHOW DATABASES LIKE 'INSURANCE_ANALYTICS';
   ```
4. Check `snowflake.yml` exists in project directory
5. Run with verbose logging:
   ```bash
   snow streamlit deploy --replace -v
   ```

### Issue: "Insufficient privileges" Error

**Solutions:**
1. Verify role has necessary permissions:
   ```sql
   USE ROLE ACCOUNTADMIN;
   GRANT CREATE STREAMLIT ON SCHEMA INSURANCE_ANALYTICS.PUBLIC TO ROLE YOUR_ROLE;
   ```
2. Ensure warehouse access:
   ```sql
   GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE YOUR_ROLE;
   ```
3. Check database and schema access:
   ```sql
   GRANT USAGE ON DATABASE INSURANCE_ANALYTICS TO ROLE YOUR_ROLE;
   GRANT USAGE ON SCHEMA INSURANCE_ANALYTICS.PUBLIC TO ROLE YOUR_ROLE;
   ```

### Issue: Warehouse Not Running

**Solutions:**
```sql
-- Start warehouse
ALTER WAREHOUSE COMPUTE_WH RESUME;

-- Enable auto-resume
ALTER WAREHOUSE COMPUTE_WH SET AUTO_RESUME = TRUE;
```

### Issue: Missing or Incorrect Data

**Solutions:**
1. Run data validation queries (see Data Requirements section)
2. Check STATE column format (must be 2-letter codes)
3. Verify numeric columns don't have text values
4. Look for NULL values in required columns

### Issue: ModuleNotFoundError (e.g., 'plotly', 'pandas')

**Symptoms:** Error message like `ModuleNotFoundError: No module named 'plotly'`

**Solutions:**
1. Verify `environment.yml` exists in project directory
2. Check `snowflake.yml` references environment file:
   ```yaml
   env_file: environment.yml
   ```
3. Redeploy to install packages:
   ```bash
   ./deploy.sh
   ```
4. Verify environment.yml includes all required packages:
   - snowflake-snowpark-python
   - streamlit
   - pandas
   - numpy
   - plotly

---

## 📁 Project Structure

```
streamlit_insurance_premium_analysis/
├── streamlit_app.py          # Main Streamlit application
├── snowflake.yml             # Snow CLI configuration (REQUIRED)
├── environment.yml           # Python package dependencies (REQUIRED)
├── deploy.sh                 # Deployment script
├── README.md                 # Complete documentation
└── output/                   # Generated by Snow CLI (auto-created)
```

### Key Files

| File | Purpose | Required |
|------|---------|----------|
| `streamlit_app.py` | Main dashboard code | ✅ Yes |
| `snowflake.yml` | Snow CLI configuration | ✅ Yes |
| `environment.yml` | Python package dependencies | ✅ Yes |
| `deploy.sh` | Deployment script | ⚠️ Recommended |
| `README.md` | Complete documentation | ⚠️ Recommended |

### Package Dependencies

The `environment.yml` file specifies required Python packages:

```yaml
name: streamlit_env
channels:
  - snowflake
dependencies:
  - python=3.11
  - snowflake-snowpark-python
  - streamlit
  - pandas
  - numpy
  - plotly
```

This file is automatically uploaded and used by Snowflake to create the correct Python environment for your Streamlit app.

---

## 🔄 Maintenance

### Update the Dashboard

After making changes to `streamlit_app.py`:

```bash
# Redeploy with replace flag
./deploy.sh

# Or manually
snow streamlit deploy --replace
```

The `--replace` flag updates the existing app without removing it.

### Monitor Performance

```sql
-- Check query history
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE QUERY_TEXT ILIKE '%premium_forecast_summary%'
ORDER BY START_TIME DESC
LIMIT 100;

-- Monitor warehouse usage
SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE WAREHOUSE_NAME = 'COMPUTE_WH'
ORDER BY START_TIME DESC;
```

### Data Refresh

The app loads data on startup and caches it. To refresh:
1. Restart the app in Snowsight
2. Or click the ⟳ button in the app interface
3. Data cache can be cleared programmatically if needed

### Performance Optimization

1. **Use appropriate warehouse size** based on user count
2. **Enable result caching** in Snowflake
3. **Consider materializing views** for frequently accessed data
4. **Enable auto-suspend** on warehouse for cost savings:
   ```sql
   ALTER WAREHOUSE COMPUTE_WH SET AUTO_SUSPEND = 300;
   ALTER WAREHOUSE COMPUTE_WH SET AUTO_RESUME = TRUE;
   ```

---

## 📝 Recent Changes

### Version 1.0.1 (Current)

#### Fixed
- **Blank map issue** - Added explicit numeric type conversion and null handling
- **Data validation** - Enhanced debugging capabilities with detailed info panel
- **Error handling** - Better graceful degradation when optional tables missing

#### Changed
- **Removed STATE_ABBREV_MAP** - Simplified to use STATE column directly
- **State codes required** - Now expects 2-letter state codes (CA, NY, TX)
- **Deployment method** - Updated to use Snow CLI with snowflake.yml

#### Added
- **snowflake.yml** - Configuration file for Snow CLI
- **deploy.sh** - Automated deployment script with Snow CLI
- **Debug mode** - Optional data validation panel in dashboard
- **Comprehensive documentation** - All docs consolidated in README

### Migration Notes

If upgrading from an earlier version:

1. **Check STATE column format:**
   ```sql
   SELECT DISTINCT STATE 
   FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary;
   ```
   Must return 2-letter codes (CA, NY, TX), not full names.

2. **Convert if needed:**
   ```sql
   -- Example conversion (adjust for your data)
   UPDATE premium_forecast_summary
   SET STATE = CASE 
     WHEN STATE = 'CALIFORNIA' THEN 'CA'
     WHEN STATE = 'NEW YORK' THEN 'NY'
     -- ... etc
   END
   WHERE LENGTH(STATE) > 2;
   ```

3. **Redeploy:**
   ```bash
   ./deploy.sh
   ```

---

## 🔑 Quick Reference

### Common Commands

```bash
# Deploy/Update
./deploy.sh

# Get app URL
snow streamlit get-url insurance_premium_dashboard

# Describe app
snow streamlit describe insurance_premium_dashboard

# List all apps
snow streamlit list

# Drop app (if needed)
snow streamlit drop insurance_premium_dashboard
```

### Data Validation Queries

```sql
-- Count records in each table
SELECT 'forecast_summary' as table_name, COUNT(*) as records 
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary
UNION ALL
SELECT 'yoy_growth', COUNT(*) 
FROM INSURANCE_ANALYTICS.POLICY_DATA.yoy_growth_all_states
UNION ALL
SELECT 'predictions', COUNT(*) 
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_predictions_12months;

-- Check STATE format
SELECT DISTINCT STATE, LENGTH(STATE) as code_length
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary
ORDER BY STATE;

-- Find NULL values
SELECT STATE, 
       MEAN_PREMIUM, 
       PREMIUM_STDDEV, 
       MIN_PREMIUM, 
       MAX_PREMIUM
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary
WHERE MEAN_PREMIUM IS NULL 
   OR PREMIUM_STDDEV IS NULL 
   OR MIN_PREMIUM IS NULL 
   OR MAX_PREMIUM IS NULL;
```

---

## 📞 Support & Resources

### Documentation
- **This README** - Complete guide with all information in one place
- All deployment, usage, and troubleshooting information is consolidated here

### Getting Help

1. **Enable Debug Mode** in the dashboard to see data validation
2. **Check troubleshooting section** above for common issues
3. **Review Recent Changes section** for updates and migration notes
4. **Verify data format** matches requirements in Data Requirements section
5. **Check Snowflake permissions** using provided SQL queries

### Best Practices

1. ✅ Always use 2-letter state codes in data tables
2. ✅ Test with small data set first
3. ✅ Enable debug mode when troubleshooting
4. ✅ Grant least-privilege access to users
5. ✅ Monitor warehouse usage and costs
6. ✅ Set up auto-suspend on warehouses
7. ✅ Document any custom modifications
8. ✅ Keep data tables updated regularly

---

## 📄 License & Credits

**Project:** Insurance Premium Forecasting Dashboard  
**Platform:** Snowflake Streamlit  
**Version:** 1.0.1  
**Last Updated:** December 2025  
**License:** Internal Use

Built with:
- [Streamlit](https://streamlit.io/)
- [Plotly](https://plotly.com/)
- [Snowflake](https://www.snowflake.com/)
- [Pandas](https://pandas.pydata.org/)

---

**🎉 Ready to deploy? Run `./deploy.sh` to get started!**
