-- deploy_all.sql - Streamlit DR Replication Cost Calculator (Business Critical)
-- Author: SE Community | Expires: 2026-01-07

-- Expiration guard (halts session if expired)
SET EXPIRATION_DATE = '2026-01-07'::DATE;

SELECT SYSTEM$ABORT_SESSION(
         'Deployment blocked: expired on ' || TO_VARCHAR($EXPIRATION_DATE)
       )
WHERE CURRENT_DATE() > $EXPIRATION_DATE;

SELECT 'Within expiration window' AS EXPIRATION_CHECK
WHERE CURRENT_DATE() <= $EXPIRATION_DATE;

-- Context
USE ROLE ACCOUNTADMIN;

-- Warehouse (SFE_ prefix for account-level object)
CREATE WAREHOUSE IF NOT EXISTS SFE_REPLICATION_CALC_WH
  WAREHOUSE_SIZE = XSMALL
  AUTO_SUSPEND = 300
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'DEMO: Replication cost calculator warehouse';

-- Schema
CREATE SCHEMA IF NOT EXISTS SNOWFLAKE_EXAMPLE.REPLICATION_CALC
  COMMENT = 'DEMO: Replication/DR cost calculator';

-- Stages
CREATE OR REPLACE STAGE SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICE_STAGE;
CREATE OR REPLACE STAGE SNOWFLAKE_EXAMPLE.REPLICATION_CALC.STREAMLIT_STAGE;

-- Tables
CREATE OR REPLACE TABLE SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_RAW (
  SOURCE_URL STRING,
  CONTENT_BASE64 STRING,
  INGESTED_AT TIMESTAMP_TZ
);

CREATE OR REPLACE TABLE SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_CURRENT (
  SERVICE_TYPE STRING, -- DATA_TRANSFER, REPLICATION_COMPUTE, STORAGE_TB_MONTH, SERVERLESS_MAINT
  CLOUD STRING,
  REGION STRING,
  UNIT STRING, -- TB or TB_MONTH
  RATE NUMBER(10,4), -- credits per unit
  CURRENCY STRING,
  IS_ESTIMATE BOOLEAN,
  REFRESHED_AT TIMESTAMP_TZ
);

-- View: database metadata (latest size)
CREATE OR REPLACE VIEW SNOWFLAKE_EXAMPLE.REPLICATION_CALC.DB_METADATA AS
WITH LATEST_USAGE AS (
  SELECT
    DATABASE_NAME,
    AVERAGE_BYTES,
    USAGE_DATE,
    ROW_NUMBER() OVER (
      PARTITION BY DATABASE_NAME
      ORDER BY USAGE_DATE DESC
    ) AS RN
  FROM SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY
)
SELECT
  DATABASE_NAME,
  (AVERAGE_BYTES / POWER(1024, 4))::NUMBER(18,6) AS SIZE_TB,
  USAGE_DATE AS AS_OF
FROM LATEST_USAGE
WHERE RN = 1
QUALIFY RN = 1;

-- Procedure: fetch PDF and populate pricing (fallback estimates)
CREATE OR REPLACE PROCEDURE
  SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REFRESH_PRICING_FROM_PDF()
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.10'
PACKAGES = ('requests', 'snowflake-snowpark-python')
HANDLER = 'run'
EXECUTE AS OWNER
AS
$$
import base64
import datetime
import requests
from snowflake.snowpark import Session

PDF_URL = "https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf"

FALLBACK_RATES = [
    {
        "service_type": "DATA_TRANSFER",
        "cloud": "AWS",
        "region": "us-east-1",
        "unit": "TB",
        "rate": 2.50,
        "currency": "CREDITS",
    },
    {
        "service_type": "REPLICATION_COMPUTE",
        "cloud": "AWS",
        "region": "us-east-1",
        "unit": "TB",
        "rate": 1.00,
        "currency": "CREDITS",
    },
    {
        "service_type": "STORAGE_TB_MONTH",
        "cloud": "AWS",
        "region": "us-east-1",
        "unit": "TB_MONTH",
        "rate": 0.25,
        "currency": "CREDITS",
    },
    {
        "service_type": "SERVERLESS_MAINT",
        "cloud": "AWS",
        "region": "us-east-1",
        "unit": "TB_MONTH",
        "rate": 0.10,
        "currency": "CREDITS",
    },
    {
        "service_type": "DATA_TRANSFER",
        "cloud": "AZURE",
        "region": "eastus2",
        "unit": "TB",
        "rate": 2.70,
        "currency": "CREDITS",
    },
    {
        "service_type": "REPLICATION_COMPUTE",
        "cloud": "AZURE",
        "region": "eastus2",
        "unit": "TB",
        "rate": 1.10,
        "currency": "CREDITS",
    },
    {
        "service_type": "STORAGE_TB_MONTH",
        "cloud": "AZURE",
        "region": "eastus2",
        "unit": "TB_MONTH",
        "rate": 0.27,
        "currency": "CREDITS",
    },
    {
        "service_type": "SERVERLESS_MAINT",
        "cloud": "AZURE",
        "region": "eastus2",
        "unit": "TB_MONTH",
        "rate": 0.12,
        "currency": "CREDITS",
    },
    {
        "service_type": "DATA_TRANSFER",
        "cloud": "GCP",
        "region": "us-central1",
        "unit": "TB",
        "rate": 2.60,
        "currency": "CREDITS",
    },
    {
        "service_type": "REPLICATION_COMPUTE",
        "cloud": "GCP",
        "region": "us-central1",
        "unit": "TB",
        "rate": 1.05,
        "currency": "CREDITS",
    },
    {
        "service_type": "STORAGE_TB_MONTH",
        "cloud": "GCP",
        "region": "us-central1",
        "unit": "TB_MONTH",
        "rate": 0.26,
        "currency": "CREDITS",
    },
    {
        "service_type": "SERVERLESS_MAINT",
        "cloud": "GCP",
        "region": "us-central1",
        "unit": "TB_MONTH",
        "rate": 0.11,
        "currency": "CREDITS",
    },
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
    for r in FALLBACK_RATES:
        rows.append(
            {
                "SERVICE_TYPE": r["service_type"],
                "CLOUD": r["cloud"],
                "REGION": r["region"],
                "UNIT": r["unit"],
                "RATE": r["rate"],
                "CURRENCY": r["currency"],
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

-- Task: daily pricing refresh
CREATE OR REPLACE TASK SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_REFRESH_TASK
  WAREHOUSE = SFE_REPLICATION_CALC_WH
  SCHEDULE = 'USING CRON 0 7 * * * UTC'
  COMMENT = 'Daily refresh of pricing from Credit Consumption PDF'
AS
  CALL SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REFRESH_PRICING_FROM_PDF();

-- Start the task (can be paused if not desired)
ALTER TASK SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_REFRESH_TASK RESUME;

-- Grants (minimal for demo)
GRANT USAGE ON WAREHOUSE SFE_REPLICATION_CALC_WH TO ROLE ACCOUNTADMIN;
GRANT USAGE ON SCHEMA SNOWFLAKE_EXAMPLE.REPLICATION_CALC TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA SNOWFLAKE_EXAMPLE.REPLICATION_CALC
  TO ROLE ACCOUNTADMIN;
GRANT ALL PRIVILEGES ON ALL VIEWS IN SCHEMA SNOWFLAKE_EXAMPLE.REPLICATION_CALC
  TO ROLE ACCOUNTADMIN;
GRANT USAGE, OPERATE ON TASK
  SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_REFRESH_TASK
  TO ROLE ACCOUNTADMIN;
GRANT USAGE ON STAGE SNOWFLAKE_EXAMPLE.REPLICATION_CALC.STREAMLIT_STAGE
  TO ROLE ACCOUNTADMIN;

-- Seed initial pricing
CALL SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REFRESH_PRICING_FROM_PDF();

SELECT
  'Deployment complete. Upload app.py to STREAMLIT_STAGE and create Streamlit app.'
  AS STATUS;
