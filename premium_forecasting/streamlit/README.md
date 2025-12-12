# Insurance Premium Forecasting Dashboard

An interactive Streamlit dashboard for analyzing insurance premium forecasts across US states, deployed on Snowflake.

![Insurance Premium Forecasting Dashboard](screenshots/Insurance_Premium_forecasting.gif)

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Deployment](#deployment)
- [Data Requirements](#data-requirements)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)

---

## ⚡ Quick Start

### 1. Deploy to Snowflake

```bash
cd /path/to/premium_forecasting/streamlit
./deploy.sh
```

### 2. Access Dashboard

1. Open Snowsight: https://app.snowflake.com
2. Navigate to **Streamlit** → **INSURANCE_PREMIUM_DASHBOARD**

**Prerequisites:** Snow CLI installed and configured with appropriate permissions.

---

## 🎯 Features

- **Interactive US Choropleth Map** - Full state shapes with PyDeck GeoJsonLayer
- **Embedded GeoJSON** - CSP-compliant, no external dependencies
- **Multiple Metrics** - Mean Premium, YoY Growth %, Volatility, Price Range
- **State Rankings** - Top/bottom 10 states with distribution analysis
- **Growth Analysis** - YoY trends and forecasts
- **State Deep Dive** - Individual state analytics
- **Correlation Analysis** - Multi-metric relationship insights
- **Data Export** - Download as CSV

**Technology:** Streamlit, Plotly, PyDeck, Snowflake Snowpark, Pandas

---

## 📋 Prerequisites

### Required
- **Snow CLI** - `pip install snowflake-cli-labs`
- **Snowflake Account** with `CREATE STREAMLIT` permissions
- **Database:** `INSURANCE_ANALYTICS`
- **Warehouse:** `COMPUTE_WH` (or custom)

### Required Data Tables

**INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary** (Required)
```sql
STATE               VARCHAR(2)      -- 2-letter codes: CA, NY, TX
MEAN_PREMIUM        NUMBER
PREMIUM_STDDEV      NUMBER
MIN_PREMIUM         NUMBER
MAX_PREMIUM         NUMBER
```

**INSURANCE_ANALYTICS.POLICY_DATA.yoy_growth_all_states** (Optional)
```sql
STATE               VARCHAR(2)
YOY_GROWTH_PCT      NUMBER
TRAILING_12MO_AVG   NUMBER
FORECAST_12MO_AVG   NUMBER
```

**INSURANCE_ANALYTICS.POLICY_DATA.premium_predictions_12months** (Optional)
```sql
SERIES              VARCHAR(2)      -- State codes
TS                  TIMESTAMP
FORECAST            NUMBER
UPPER_BOUND         NUMBER
LOWER_BOUND         NUMBER
```

⚠️ **Important:** STATE columns must use **2-letter codes** (CA, NY, TX), not full names.

---

## 🚀 Deployment

### Method 1: Deploy Script (Recommended)

```bash
cd /path/to/premium_forecasting/streamlit
./deploy.sh
```

### Method 2: Snow CLI

```bash
snow streamlit deploy --database "INSURANCE_ANALYTICS" --schema "PUBLIC" --replace
```

### Method 3: Snowsight UI

1. Navigate to **Streamlit** → **+ Streamlit App**
2. Configure: Name = `INSURANCE_PREMIUM_DASHBOARD`, Location = `INSURANCE_ANALYTICS.PUBLIC`
3. Copy `streamlit_app.py` contents into editor
4. Click **Run**

### Verify

```bash
snow streamlit get-url insurance_premium_dashboard
snow streamlit list
```

---

## ⚙️ Configuration

### Configurable Forecast Table

Use the sidebar **⚙️ Configuration** section to change the forecast table name (default: `INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary`).

### Custom Warehouse

Edit `snowflake.yml`:
```yaml
streamlit:
  query_warehouse: YOUR_WAREHOUSE_NAME
```

### Grant Access

```sql
-- App access
GRANT USAGE ON STREAMLIT INSURANCE_ANALYTICS.PUBLIC.INSURANCE_PREMIUM_DASHBOARD 
TO ROLE YOUR_ROLE;

-- Data access
GRANT SELECT ON ALL TABLES IN SCHEMA INSURANCE_ANALYTICS.POLICY_DATA 
TO ROLE YOUR_ROLE;

-- Warehouse access
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE YOUR_ROLE;
```

---

## 🔧 Troubleshooting

### Blank or Dark Map

**Solution:**
1. Enable "Show Debug Info" in sidebar
2. Verify STATE column has 2-letter codes:
   ```sql
   SELECT DISTINCT STATE FROM premium_forecast_summary ORDER BY STATE;
   ```
3. Check for NULL values in metric columns

### Incorrect Tooltips

**Fixed in current version.** Tooltips now show actual state names and values.

### Table Not Found

```sql
-- Verify tables exist
SHOW TABLES IN SCHEMA INSURANCE_ANALYTICS.POLICY_DATA;

-- Check permissions
SHOW GRANTS ON SCHEMA INSURANCE_ANALYTICS.POLICY_DATA;
```

### Deployment Failed

```bash
# Test connection
snow connection test

# Deploy with verbose logging
snow streamlit deploy --replace -v
```

Check permissions:
```sql
GRANT CREATE STREAMLIT ON SCHEMA INSURANCE_ANALYTICS.PUBLIC TO ROLE YOUR_ROLE;
GRANT USAGE ON DATABASE INSURANCE_ANALYTICS TO ROLE YOUR_ROLE;
```

### Module Not Found (plotly, pandas, pydeck)

Ensure `environment.yml` exists and is referenced in `snowflake.yml`:
```yaml
env_file: environment.yml
```

Redeploy: `./deploy.sh`

### STATE Column Format Issues

✅ **Correct:** CA, NY, TX, FL, WA  
❌ **Incorrect:** California, New York, Texas

Convert if needed:
```sql
UPDATE premium_forecast_summary
SET STATE = CASE 
  WHEN STATE = 'California' THEN 'CA'
  WHEN STATE = 'New York' THEN 'NY'
  -- ... etc
END
WHERE LENGTH(STATE) > 2;
```

---

## 📁 Project Structure

```
premium_forecasting/streamlit/
├── streamlit_app.py          # Main app (130 KB with embedded GeoJSON)
├── snowflake.yml             # Snow CLI config
├── environment.yml           # Python dependencies
├── deploy.sh                 # Deployment script
├── README.md                 # This file
└── screenshots/
    └── Insurance_Premium_forecasting.gif
```

### Required Files

| File | Purpose | Size |
|------|---------|------|
| `streamlit_app.py` | Main application with embedded GeoJSON | 130 KB |
| `snowflake.yml` | Snow CLI configuration | < 1 KB |
| `environment.yml` | Python packages: streamlit, pandas, numpy, plotly, pydeck | < 1 KB |

### Dependencies (environment.yml)

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
  - pydeck
```

---

## 🔬 Technical Details

### Map Visualization

**Technology:** PyDeck GeoJsonLayer with embedded GeoJSON data (~90KB)

**How it works:**
1. GeoJSON data embedded in `streamlit_app.py` (52 US state/territory polygons)
2. Premium values merged into GeoJSON properties at runtime
3. Color gradient calculated: Blue (low) → Purple (mid) → Red (high)
4. PyDeck renders filled polygons with interactive tooltips

**Benefits:**
- ✅ CSP-compliant (no external URLs)
- ✅ Single file deployment
- ✅ Fast loading (data loaded once)
- ✅ Full state shapes (not just circles)

### Color Mapping

```python
# Normalize to 0-1 range
normalized = (value - min) / (max - min)

# RGB gradient
r = int(255 * normalized)                              # Increases with value
g = int(100 * (1 - abs(normalized - 0.5) * 2))        # Peak at midpoint
b = int(255 * (1 - normalized))                        # Decreases with value
```

### Tooltip Format

PyDeck tooltips reference GeoJSON properties directly:
```python
tooltip = {'text': '{name}\n{code}\nAverage Premium ($): ${value:.2f}'}
```

Displays:
```
California
CA
Average Premium ($): $1234.56
```

### Performance

- **GeoJSON Load:** Once at startup (~10-50ms)
- **Map Render:** Browser-side (<100ms)
- **State Updates:** <50ms
- **Memory:** ~2MB for GeoJSON

---

## 🔑 Quick Reference

### Common Commands

```bash
# Deploy
./deploy.sh

# Get URL
snow streamlit get-url insurance_premium_dashboard

# List apps
snow streamlit list

# Drop app
snow streamlit drop insurance_premium_dashboard
```

### Data Validation

```sql
-- Check record counts
SELECT 'forecast_summary' as table_name, COUNT(*) as records 
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary;

-- Verify STATE format
SELECT DISTINCT STATE, LENGTH(STATE) 
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary
ORDER BY STATE;

-- Find NULLs
SELECT STATE, MEAN_PREMIUM, PREMIUM_STDDEV 
FROM INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary
WHERE MEAN_PREMIUM IS NULL OR PREMIUM_STDDEV IS NULL;
```

### Performance Optimization

```sql
-- Enable auto-suspend
ALTER WAREHOUSE COMPUTE_WH SET AUTO_SUSPEND = 300;
ALTER WAREHOUSE COMPUTE_WH SET AUTO_RESUME = TRUE;
```

---

## 📝 Version History

**Version 2.0.0** (Current - December 2024)
- PyDeck GeoJsonLayer for full state shapes
- Embedded GeoJSON (130 KB, single file)
- Fixed tooltip rendering
- CSP-compliant, no external dependencies

**Version 1.0.0** (November 2024)
- Initial release with basic functionality

---

## 💻 Usage Tips

1. **Select Metrics** - Use dropdown to switch between Premium, Growth, Volatility, Price Range
2. **Hover States** - See detailed values in tooltip
3. **Enable Debug** - Check "Show Debug Info" when troubleshooting data issues
4. **Configure Table** - Change forecast table name via sidebar configuration
5. **Export Data** - Use "Raw Data" tab to download CSV

---

## 📄 License

**Version:** 2.0.0  
**Last Updated:** December 2024  
**License:** Internal Use

Built with [Streamlit](https://streamlit.io/), [Plotly](https://plotly.com/), [PyDeck](https://deckgl.readthedocs.io/), and [Snowflake](https://www.snowflake.com/)

---

**🎉 Ready to deploy? Run `./deploy.sh` to get started!**
