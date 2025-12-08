# Deployment - Streamlit DR Replication Cost Calculator (Business Critical)

## Run All (Snowsight)
1. Open Snowsight ➜ Worksheets.
2. Paste `deploy_all.sql` from repo root.
3. Run All. The script:
   - Enforces expiration (fails after 2026-01-07).
   - Creates schema `SNOWFLAKE_EXAMPLE.REPLICATION_CALC`.
   - Creates warehouse `SFE_REPLICATION_CALC_WH`.
   - Creates stage `PRICE_STAGE` and `STREAMLIT_STAGE`.
   - Creates pricing tables/views, metadata view, Snowpark procedure, and daily refresh task.

## Upload Streamlit App
1. In a new worksheet, upload code to the Streamlit stage:
   ```sql
   PUT file://streamlit/app.py @SNOWFLAKE_EXAMPLE.REPLICATION_CALC.STREAMLIT_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
   ```
2. Create the Streamlit app:
   ```sql
   CREATE OR REPLACE STREAMLIT REPLICATION_CALCULATOR
     ROOT = '@SNOWFLAKE_EXAMPLE.REPLICATION_CALC.STREAMLIT_STAGE'
     MAIN_FILE = 'app.py';
   ```
3. Open Apps ➜ `REPLICATION_CALCULATOR`.

## Manual Pricing Refresh (optional)
Run after deployment or before scheduled task:
```sql
CALL SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REFRESH_PRICING_FROM_PDF();
```

## Cleanup
Use `sql/99_cleanup/99_drop_replication_calc.sql` if you need to remove demo objects (preserves shared DB/SEMANTIC_MODELS).
