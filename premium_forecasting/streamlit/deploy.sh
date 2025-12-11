#!/bin/bash

# ============================================================
# Streamlit App Deployment Script for Snowflake
# Deploys Insurance Premium Forecasting Dashboard using Snow CLI
# Target: INSURANCE_ANALYTICS.PUBLIC
# 
# For complete documentation, see README.md
# ============================================================

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}${BOLD}========================================${NC}"
echo -e "${BLUE}${BOLD}Insurance Premium Dashboard Deployment${NC}"
echo -e "${BLUE}${BOLD}========================================${NC}"
echo ""

# Check if snow CLI is installed
if ! command -v snow &> /dev/null; then
    echo -e "${RED}Error: Snow CLI is not installed${NC}"
    echo -e "${YELLOW}Install it with: pip install snowflake-cli-labs${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Snow CLI found${NC}"

# Check if required files exist
if [ ! -f "streamlit_app.py" ]; then
    echo -e "${RED}Error: streamlit_app.py not found in current directory${NC}"
    exit 1
fi

if [ ! -f "snowflake.yml" ]; then
    echo -e "${RED}Error: snowflake.yml not found in current directory${NC}"
    echo -e "${YELLOW}The snowflake.yml configuration file is required for deployment${NC}"
    exit 1
fi

if [ ! -f "environment.yml" ]; then
    echo -e "${RED}Error: environment.yml not found in current directory${NC}"
    echo -e "${YELLOW}The environment.yml file is required to install Python packages (plotly, pandas, etc.)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found streamlit_app.py${NC}"
echo -e "${GREEN}✓ Found snowflake.yml${NC}"
echo -e "${GREEN}✓ Found environment.yml${NC}"
echo ""

# Deploy using Snow CLI
echo -e "${YELLOW}Deploying Streamlit app to INSURANCE_ANALYTICS.PUBLIC...${NC}"
echo ""

# Deploy the Streamlit app using snowflake.yml configuration
snow streamlit deploy \
    --replace \
    --database "INSURANCE_ANALYTICS" \
    --schema "PUBLIC"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}${BOLD}DEPLOYMENT COMPLETE!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}${BOLD}App Details:${NC}"
    echo -e "  • Name: ${BOLD}INSURANCE_PREMIUM_DASHBOARD${NC}"
    echo -e "  • Database: ${BOLD}INSURANCE_ANALYTICS${NC}"
    echo -e "  • Schema: ${BOLD}PUBLIC${NC}"
    echo ""
    echo -e "${YELLOW}${BOLD}To access your app:${NC}"
    echo "  1. Log into Snowsight UI"
    echo "  2. Navigate to 'Streamlit' in the left menu"
    echo "  3. Find 'INSURANCE_PREMIUM_DASHBOARD'"
    echo "  4. Click to launch the dashboard"
    echo ""
    echo -e "${YELLOW}${BOLD}Required Data Tables:${NC}"
    echo "  • INSURANCE_ANALYTICS.POLICY_DATA.premium_forecast_summary"
    echo "  • INSURANCE_ANALYTICS.POLICY_DATA.yoy_growth_all_states"
    echo "  • INSURANCE_ANALYTICS.POLICY_DATA.premium_predictions_12months"
    echo ""
    echo -e "${BLUE}${BOLD}Quick Commands:${NC}"
    echo "  # Get app URL:"
    echo "  snow streamlit get-url insurance_premium_dashboard"
    echo ""
    echo "  # Describe app:"
    echo "  snow streamlit describe insurance_premium_dashboard"
    echo ""
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}${BOLD}DEPLOYMENT FAILED${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "  1. Verify Snow CLI is configured: ${BOLD}snow connection test${NC}"
    echo "  2. Check permissions: Need CREATE STREAMLIT on INSURANCE_ANALYTICS.PUBLIC"
    echo "  3. Verify database exists: INSURANCE_ANALYTICS"
    echo "  4. Check snowflake.yml is properly configured"
    echo "  5. Run with verbose flag: Add -v to see detailed logs"
    echo ""
    exit 1
fi
