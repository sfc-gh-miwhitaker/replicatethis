@echo off
echo === Start Checklist (Snowsight-only) ===
echo - Resume warehouse: ALTER WAREHOUSE SFE_REPLICATION_CALC_WH RESUME;
echo - Resume task: ALTER TASK SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_REFRESH_TASK RESUME;
echo - Upload latest streamlit/app.py to ^@SNOWFLAKE_EXAMPLE.REPLICATION_CALC.STREAMLIT_STAGE if changed.
echo - Pricing refresh (optional): CALL SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REFRESH_PRICING_FROM_PDF();
