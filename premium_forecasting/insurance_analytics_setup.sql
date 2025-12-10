-- Insurance Analytics Dataset Setup
-- Creates synthetic automotive insurance data for price prediction modeling
-- Coverage: All 50 US states, with WY and VT limited to 17 policies each

-- Configuration Variables
SET start_date = '2020-01-01';  -- Starting date for data generation
SET months_of_data = 72;        -- Number of months to generate (72 = 6 years)

-- Create database and schema
CREATE OR REPLACE DATABASE insurance_analytics;
CREATE OR REPLACE SCHEMA insurance_analytics.policy_data;

-- Generate synthetic carrier performance data
CREATE OR REPLACE TABLE insurance_analytics.policy_data.carrier_product_performance_dim AS
WITH date_spine AS (
    SELECT DATEADD(month, seq4(), $start_date::DATE) as policy_month
    FROM TABLE(GENERATOR(rowcount => $months_of_data))
),
states AS (
    SELECT state, CASE WHEN state IN ('WY', 'VT') THEN TRUE ELSE FALSE END as is_limited
    FROM (VALUES 
        ('AL'), ('AK'), ('AZ'), ('AR'), ('CA'), ('CO'), ('CT'), ('DE'), ('FL'), ('GA'),
        ('HI'), ('ID'), ('IL'), ('IN'), ('IA'), ('KS'), ('KY'), ('LA'), ('ME'), ('MD'),
        ('MA'), ('MI'), ('MN'), ('MS'), ('MO'), ('MT'), ('NE'), ('NV'), ('NH'), ('NJ'),
        ('NM'), ('NY'), ('NC'), ('ND'), ('OH'), ('OK'), ('OR'), ('PA'), ('RI'), ('SC'),
        ('SD'), ('TN'), ('TX'), ('UT'), ('VT'), ('VA'), ('WA'), ('WV'), ('WI'), ('WY')
    ) t(state)
),
carriers AS (
    SELECT carrier FROM (VALUES
        ('State Farm'), ('Geico'), ('Progressive'), ('Allstate'), ('USAA'),
        ('Liberty Mutual'), ('Farmers'), ('Nationwide'), ('Travelers'), ('American Family')
    ) t(carrier)
),
base_policies AS (
    SELECT 
        s.state,
        s.is_limited,
        c.carrier as unique_carrier_name,
        d.policy_month + UNIFORM(0, 27, RANDOM())::INT as policy_effective_date,
        CASE WHEN UNIFORM(0, 1, RANDOM()) > 0.5 THEN 6 ELSE 12 END as policy_term,
        'Personal Auto' as business_line,
        TRUE as is_applicant,
        ROW_NUMBER() OVER (PARTITION BY s.state ORDER BY RANDOM()) as row_num
    FROM date_spine d
    CROSS JOIN states s
    CROSS JOIN carriers c
    WHERE CASE 
        WHEN s.is_limited THEN UNIFORM(0, 1, RANDOM()) > 0.97
        ELSE UNIFORM(0, 1, RANDOM()) > 0.3 
    END
)
SELECT 
    state,
    policy_effective_date,
    policy_term,
    unique_carrier_name,
    business_line,
    is_applicant,
    CASE 
        WHEN state IN ('CA', 'NY', 'FL') THEN ROUND(800 + (DATEDIFF(month, $start_date, policy_effective_date) * 8) + UNIFORM(-100, 150, RANDOM()), 2)
        WHEN state IN ('TX', 'IL', 'OH') THEN ROUND(650 + (DATEDIFF(month, $start_date, policy_effective_date) * 6.5) + UNIFORM(-80, 120, RANDOM()), 2)
        ELSE ROUND(550 + (DATEDIFF(month, $start_date, policy_effective_date) * 5) + UNIFORM(-60, 100, RANDOM()), 2)
    END as premium,
    CASE 
        WHEN UNIFORM(0, 1, RANDOM()) > 0.85 THEN DATEADD(day, UNIFORM(30, 330, RANDOM()), policy_effective_date)
        ELSE NULL
    END as cancellation_date
FROM base_policies
WHERE CASE 
    WHEN is_limited THEN row_num <= 17
    ELSE TRUE
END;

-- Create aggregated view for price prediction
CREATE OR REPLACE VIEW insurance_analytics.policy_data.premium_view_normalized AS 
SELECT 
    state,
    DATE_TRUNC('MONTH', policy_effective_date) as policy_effective_date,
    AVG(CASE WHEN policy_term = 6 THEN premium * 2 ELSE premium END) as premium_12mo
FROM insurance_analytics.policy_data.carrier_product_performance_dim
WHERE policy_effective_date >= '2012-01-01' 
    AND policy_effective_date < '2025-12-01'
    AND policy_term IN (6, 12)
    AND state IS NOT NULL
    AND state NOT IN ('D', 'M', 'NA', 'S')
    AND business_line = 'Personal Auto'
    AND ((DATE(cancellation_date) > DATE(policy_effective_date)) OR cancellation_date IS NULL)
    AND is_applicant = TRUE
    AND unique_carrier_name NOT IN ('Root Insurance')
GROUP BY state, DATE_TRUNC('MONTH', policy_effective_date)
ORDER BY state, policy_effective_date;

-- Validation queries
SELECT 'State Coverage Check' as validation_type, COUNT(DISTINCT state) as total_states, COUNT(*) as total_policies
FROM insurance_analytics.policy_data.carrier_product_performance_dim;

SELECT 'Limited States Check' as validation_type, state, COUNT(*) as policy_count
FROM insurance_analytics.policy_data.carrier_product_performance_dim
WHERE state IN ('WY', 'VT')
GROUP BY state;

SELECT 'View Record Count' as validation_type, COUNT(*) as aggregated_records
FROM insurance_analytics.policy_data.premium_view_normalized;
