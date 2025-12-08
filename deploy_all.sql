/*******************************************************************************
 * DEMO METADATA (Machine-readable - Do not modify format)
 * PROJECT_NAME: Streamlit DR Replication Cost Calculator
 * AUTHOR: SE Community
 * CREATED: 2025-12-08
 * EXPIRES: 2026-01-07
 * GITHUB_REPO: https://github.com/sfc-gh-miwhitaker/replicatethis
 * PURPOSE: Snowflake-native replication/DR cost calculator (Streamlit)
 *
 * DEPLOYMENT INSTRUCTIONS:
 * 1. Open Snowsight (https://app.snowflake.com)
 * 2. Copy this ENTIRE script
 * 3. Paste into a new SQL worksheet
 * 4. Click "Run All" (or press Cmd/Ctrl + Enter repeatedly)
 * 5. Monitor output for any errors
 ******************************************************************************/

-- Expiration Check (simple SELECT pattern)
SET EXPIRATION_DATE = '2026-01-07'::DATE;
SELECT
    CASE
        WHEN CURRENT_DATE() > $EXPIRATION_DATE
            THEN 'EXPIRED: ' || TO_VARCHAR($EXPIRATION_DATE)
        ELSE 'ACTIVE: Expires ' || TO_VARCHAR($EXPIRATION_DATE)
    END AS EXPIRATION_STATUS;

/*******************************************************************************
 * SECTION 1: Context
 ******************************************************************************/
USE ROLE ACCOUNTADMIN;

/*******************************************************************************
 * SECTION 2: Git Integration (optional if repo already staged)
 ******************************************************************************/
-- If SFE_GIT_API_INTEGRATION already exists, this is idempotent.
CREATE OR REPLACE API INTEGRATION SFE_GIT_API_INTEGRATION
    API_PROVIDER = git_https_api
    API_ALLOWED_PREFIXES = (
        'https://github.com/sfc-gh-miwhitaker/replicatethis'
    )
    ENABLED = TRUE
    COMMENT = 'DEMO: Replication cost calc (Expires: 2026-01-07)';

CREATE DATABASE IF NOT EXISTS SNOWFLAKE_EXAMPLE;

CREATE SCHEMA IF NOT EXISTS SNOWFLAKE_EXAMPLE.TOOLS
    COMMENT = 'DEMO TOOLS (Expires: 2026-01-07)';

CREATE OR REPLACE GIT REPOSITORY SNOWFLAKE_EXAMPLE.TOOLS.REPLICATE_THIS_REPO
    API_INTEGRATION = SFE_GIT_API_INTEGRATION
    ORIGIN = 'https://github.com/sfc-gh-miwhitaker/replicatethis'
    COMMENT = 'Source repo for replication cost calc (Expires: 2026-01-07)';

SHOW GIT BRANCHES IN SNOWFLAKE_EXAMPLE.TOOLS.REPLICATE_THIS_REPO;

/*******************************************************************************
 * SECTION 3: Warehouse & Schema
 ******************************************************************************/
CREATE WAREHOUSE IF NOT EXISTS SFE_REPLICATION_CALC_WH
    WAREHOUSE_SIZE = XSMALL
    AUTO_SUSPEND = 300
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'DEMO: Replication cost calculator WH (Expires: 2026-01-07)';

CREATE SCHEMA IF NOT EXISTS SNOWFLAKE_EXAMPLE.REPLICATION_CALC
    COMMENT = 'DEMO: Replication/DR cost calculator (Expires: 2026-01-07)';

USE SCHEMA SNOWFLAKE_EXAMPLE.REPLICATION_CALC;
USE WAREHOUSE SFE_REPLICATION_CALC_WH;

/*******************************************************************************
 * SECTION 4: Stages
 ******************************************************************************/
CREATE OR REPLACE STAGE PRICE_STAGE
    COMMENT = 'Pricing ingest assets (Expires: 2026-01-07)';

CREATE OR REPLACE STAGE STREAMLIT_STAGE
    COMMENT = 'Streamlit app code (Expires: 2026-01-07)';

/*******************************************************************************
 * SECTION 5: Tables and Views
 ******************************************************************************/
CREATE OR REPLACE TABLE PRICING_RAW (
    SOURCE_URL STRING,
    CONTENT_BASE64 STRING,
    INGESTED_AT TIMESTAMP_TZ
) COMMENT = 'Raw PDF content for audit (Expires: 2026-01-07)';

CREATE OR REPLACE TABLE PRICING_CURRENT (
    SERVICE_TYPE STRING,
    CLOUD STRING,
    REGION STRING,
    UNIT STRING,
    RATE NUMBER(10,4),
    CURRENCY STRING,
    IS_ESTIMATE BOOLEAN,
    REFRESHED_AT TIMESTAMP_TZ
) COMMENT = 'Normalized pricing rows (BC) (Expires: 2026-01-07)';

CREATE OR REPLACE VIEW DB_METADATA AS
WITH LATEST_USAGE AS (
    SELECT
        DATABASE_NAME,
        AVERAGE_DATABASE_BYTES,
        USAGE_DATE,
        ROW_NUMBER() OVER (
            PARTITION BY DATABASE_NAME
            ORDER BY USAGE_DATE DESC
        ) AS RN
    FROM SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY
)
SELECT
    DATABASE_NAME,
    (AVERAGE_DATABASE_BYTES / POWER(1024, 4))::NUMBER(18,6) AS SIZE_TB,
    USAGE_DATE AS AS_OF
FROM LATEST_USAGE
WHERE RN = 1
QUALIFY RN = 1;

/*******************************************************************************
 * SECTION 6: Pricing Refresh Procedure (Snowpark)
 ******************************************************************************/
CREATE OR REPLACE PROCEDURE REFRESH_PRICING_FROM_PDF()
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('requests', 'snowflake-snowpark-python')
HANDLER = 'run'
EXECUTE AS OWNER
COMMENT = 'Fetch PDF; populate pricing (Expires: 2026-01-07)'
AS
$$
import base64
import datetime
import requests
from snowflake.snowpark import Session

PDF_URL = "https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf"

FALLBACK_RATES = [
    {"service_type": "DATA_TRANSFER", "cloud": "AWS", "region": "us-east-1",
     "unit": "TB", "rate": 2.50, "currency": "CREDITS"},
    {"service_type": "REPLICATION_COMPUTE", "cloud": "AWS", "region": "us-east-1",
     "unit": "TB", "rate": 1.00, "currency": "CREDITS"},
    {"service_type": "STORAGE_TB_MONTH", "cloud": "AWS", "region": "us-east-1",
     "unit": "TB_MONTH", "rate": 0.25, "currency": "CREDITS"},
    {"service_type": "SERVERLESS_MAINT", "cloud": "AWS", "region": "us-east-1",
     "unit": "TB_MONTH", "rate": 0.10, "currency": "CREDITS"},
    {"service_type": "DATA_TRANSFER", "cloud": "AZURE", "region": "eastus2",
     "unit": "TB", "rate": 2.70, "currency": "CREDITS"},
    {"service_type": "REPLICATION_COMPUTE", "cloud": "AZURE", "region": "eastus2",
     "unit": "TB", "rate": 1.10, "currency": "CREDITS"},
    {"service_type": "STORAGE_TB_MONTH", "cloud": "AZURE", "region": "eastus2",
     "unit": "TB_MONTH", "rate": 0.27, "currency": "CREDITS"},
    {"service_type": "SERVERLESS_MAINT", "cloud": "AZURE", "region": "eastus2",
     "unit": "TB_MONTH", "rate": 0.12, "currency": "CREDITS"},
    {"service_type": "DATA_TRANSFER", "cloud": "GCP", "region": "us-central1",
     "unit": "TB", "rate": 2.60, "currency": "CREDITS"},
    {"service_type": "REPLICATION_COMPUTE", "cloud": "GCP", "region": "us-central1",
     "unit": "TB", "rate": 1.05, "currency": "CREDITS"},
    {"service_type": "STORAGE_TB_MONTH", "cloud": "GCP", "region": "us-central1",
     "unit": "TB_MONTH", "rate": 0.26, "currency": "CREDITS"},
    {"service_type": "SERVERLESS_MAINT", "cloud": "GCP", "region": "us-central1",
     "unit": "TB_MONTH", "rate": 0.11, "currency": "CREDITS"},
]


def try_fetch_pdf():
    try:
        resp = requests.get(PDF_URL, timeout=30)
        resp.raise_for_status()
        return base64.b64encode(resp.content).decode()
    except Exception:
        return None


def run(session: Session) -> str:
    pdf_b64 = try_fetch_pdf()
    now = datetime.datetime.utcnow()

    session.sql("TRUNCATE TABLE PRICING_RAW").collect()
    session.table("PRICING_RAW").insert(
        [
            {
                "SOURCE_URL": PDF_URL,
                "CONTENT_BASE64": pdf_b64 if pdf_b64 else "UNAVAILABLE",
                "INGESTED_AT": now,
            }
        ]
    )

    session.sql("TRUNCATE TABLE PRICING_CURRENT").collect()
    rows = []
    for rate_row in FALLBACK_RATES:
        rows.append(
            {
                "SERVICE_TYPE": rate_row["service_type"],
                "CLOUD": rate_row["cloud"],
                "REGION": rate_row["region"],
                "UNIT": rate_row["unit"],
                "RATE": rate_row["rate"],
                "CURRENCY": rate_row["currency"],
                "IS_ESTIMATE": True,
                "REFRESHED_AT": now,
            }
        )
    session.table("PRICING_CURRENT").insert(rows)
    return (
        f"Pricing refreshed at {now.isoformat()}Z; PDF fetched="
        f"{pdf_b64 is not None}"
    )
$$;

/*******************************************************************************
 * SECTION 7: Scheduled Task
 ******************************************************************************/
CREATE OR REPLACE TASK PRICING_REFRESH_TASK
    WAREHOUSE = SFE_REPLICATION_CALC_WH
    SCHEDULE = 'USING CRON 0 7 * * * UTC'
    COMMENT = 'Daily pricing refresh (Expires: 2026-01-07)'
AS
    CALL REFRESH_PRICING_FROM_PDF();

ALTER TASK PRICING_REFRESH_TASK RESUME;

/*******************************************************************************
 * SECTION 8: Grants (minimal for demo)
 ******************************************************************************/
GRANT USAGE ON WAREHOUSE SFE_REPLICATION_CALC_WH TO ROLE ACCOUNTADMIN;
GRANT USAGE ON SCHEMA SNOWFLAKE_EXAMPLE.REPLICATION_CALC TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA SNOWFLAKE_EXAMPLE.REPLICATION_CALC
    TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA SNOWFLAKE_EXAMPLE.REPLICATION_CALC
    TO ROLE ACCOUNTADMIN;
GRANT USAGE, OPERATE ON TASK PRICING_REFRESH_TASK TO ROLE ACCOUNTADMIN;
GRANT USAGE ON STAGE PRICE_STAGE TO ROLE ACCOUNTADMIN;
GRANT USAGE ON STAGE STREAMLIT_STAGE TO ROLE ACCOUNTADMIN;
GRANT USAGE ON PROCEDURE REFRESH_PRICING_FROM_PDF() TO ROLE ACCOUNTADMIN;

/*******************************************************************************
 * SECTION 9: Seed and Status
 ******************************************************************************/
CALL REFRESH_PRICING_FROM_PDF();

SELECT
    'Deployment complete' AS STATUS,
    'Upload app.py to @STREAMLIT_STAGE and create Streamlit app' AS NEXT_STEP,
    'Schema: SNOWFLAKE_EXAMPLE.REPLICATION_CALC' AS SCHEMA_PATH,
    'Warehouse: SFE_REPLICATION_CALC_WH' AS WAREHOUSE_NAME;
