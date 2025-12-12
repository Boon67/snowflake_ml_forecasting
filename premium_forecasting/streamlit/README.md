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
- [Architecture](#architecture)
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

## 🏗️ Architecture

### Modular Design Pattern

The application follows a **separation of concerns** pattern with distinct modules:

#### 1. **config.py** - Configuration Layer
- **Metric Definitions**: Color scales, formats, display titles
- **Table Options**: Database table configurations
- **Constants**: State coordinates, app settings
- **Single Source of Truth**: All configuration in one place

#### 2. **data_loader.py** - Data Access Layer
- **Snowpark Integration**: Connects to Snowflake using `get_active_session()`
- **Data Loading**: `load_forecast_data()` fetches from three tables
- **Data Preparation**: `prepare_map_data()` merges and calculates metrics
- **Caching**: `@st.cache_data` for performance optimization
- **Error Handling**: Graceful fallbacks for missing tables

#### 3. **visualizations.py** - Presentation Layer
- **PyDeck Maps**: `create_choropleth_map()` with GeoJSON rendering
- **Plotly Charts**: `create_bar_chart()`, `create_time_series_chart()`
- **Color Mapping**: `get_color_for_scale()` converts Plotly scales to RGB
- **Consistent Styling**: Unified color schemes across visualizations

#### 4. **utils.py** - UI Component Layer
- **Sidebar Controls**: `render_sidebar_config()`, `render_dashboard_controls()`
- **Summary Cards**: `display_summary_cards()` for key metrics
- **Debug Info**: `display_data_validation()` for troubleshooting
- **Reusable Components**: UI elements used across the app

#### 5. **streamlit_app.py** - Application Layer
- **Orchestration**: Imports and coordinates all modules
- **Page Layout**: Defines application structure and flow
- **Session Management**: Handles Snowpark session
- **Error Boundaries**: Top-level exception handling

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User opens app → streamlit_app.py                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Load config → config.py (METRIC_CONFIG, TABLE_OPTIONS)  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Render sidebar → utils.render_sidebar_config()          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Fetch data → data_loader.load_forecast_data()           │
│    • premium_forecast_summary                               │
│    • yoy_growth_all_states                                  │
│    • premium_predictions_12months                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Prepare map data → data_loader.prepare_map_data()       │
│    • Merge tables                                           │
│    • Calculate derived metrics                              │
│    • Clean and validate                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Render visualizations                                    │
│    • visualizations.create_choropleth_map()                 │
│    • visualizations.create_bar_chart()                      │
│    • visualizations.create_time_series_chart()              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. Display summary cards → utils.display_summary_cards()   │
└─────────────────────────────────────────────────────────────┘
```

### Snowflake Deployment Model

**V2 Definition Format** (`snowflake.yml`):
```yaml
definition_version: 2
entities:
  insurance_premium_dashboard:
    type: streamlit
    identifier:
      name: insurance_premium_dashboard
    main_file: streamlit_app.py
    artifacts:
      - streamlit_app.py
      - config.py
      - data_loader.py
      - visualizations.py
      - utils.py
      - us_states_geojson.py
      - environment.yml
```

**All modules uploaded together** - Snowflake supports local imports:
```python
from config import METRIC_CONFIG, TABLE_OPTIONS
from data_loader import load_forecast_data
from visualizations import create_choropleth_map
```

### Why Modular?

**Scenario:** Add a new "Claims Ratio" metric

**Monolithic Approach:**
1. Find metric config buried in 1000+ line file
2. Update color mapping function 300 lines away
3. Modify tooltip logic 500 lines away
4. Risk breaking existing code
5. Hard to test changes

**Modular Approach:**
1. Edit `config.py` → Add to `METRIC_CONFIG`
2. Done! App automatically:
   - Shows new metric in dropdown
   - Applies correct color scale
   - Formats tooltips properly
3. Easy to unit test
4. No risk to other features

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

### Modular Architecture

The application uses a clean, modular structure for better maintainability and reusability:

```
premium_forecasting/streamlit/
├── streamlit_app.py          # Main application (~115 lines)
├── config.py                 # Configuration & constants
├── data_loader.py            # Data loading & preparation
├── visualizations.py         # Chart & map creation
├── utils.py                  # UI components & utilities
├── us_states_geojson.py      # Embedded GeoJSON data
├── snowflake.yml             # V2 Snow CLI config
├── environment.yml           # Python dependencies
├── deploy.sh                 # Deployment script
├── README.md                 # This file
└── screenshots/
    └── Insurance_Premium_forecasting.gif
```

### Module Breakdown

| Module | Lines | Purpose |
|--------|-------|---------|
| `streamlit_app.py` | ~115 | Main orchestration and page layout |
| `config.py` | ~70 | Metric configs, table options, constants |
| `data_loader.py` | ~116 | Snowflake data access with caching |
| `visualizations.py` | ~216 | PyDeck maps, Plotly charts, color scales |
| `utils.py` | ~147 | Sidebar controls, debug info, UI cards |
| `us_states_geojson.py` | ~15K | US states GeoJSON (CSP-compliant) |

**Total:** ~670 lines of application code (excluding GeoJSON data)

### Benefits of Modular Structure

✅ **Maintainable** - Easy to find and fix issues, clear separation of concerns  
✅ **Reusable** - Import modules in other apps, build component libraries  
✅ **Testable** - Unit test individual functions, mock data easily  
✅ **Collaborative** - Multiple devs work on different modules  
✅ **Scalable** - Simple to add new metrics, charts, or features  

### Adding a New Metric (Example)

**Before (Monolithic):** Edit in 4-5 places across 200+ lines  
**After (Modular):** Edit `config.py` only:

```python
"New Metric": {
    'column': 'NEW_COLUMN',
    'title': 'New Metric Title',
    'format': ':.2f',
    'color_scale': 'Greens'
}
```
Done! The rest works automatically.

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

**Version 3.0.0** (Current - December 2024)
- **Modular architecture** - 5 focused modules for maintainability
- **V2 definition format** - Modern Snowflake CLI configuration
- **Enhanced color scales** - RdYlGn with proper business logic mapping
- **Improved tooltips** - Dynamic formatting (currency vs percentage)
- **Dropdown table selector** - Easy switching between forecast tables

**Version 2.0.0** (December 2024)
- PyDeck GeoJsonLayer for full state shapes
- Embedded GeoJSON (CSP-compliant, no external dependencies)
- Fixed tooltip rendering with proper value display
- Dynamic color mapping across visualizations

**Version 1.0.0** (November 2024)
- Initial monolithic release with basic functionality

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
