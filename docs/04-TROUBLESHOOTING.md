# Troubleshooting - Streamlit DR Replication Cost Calculator

## Pricing table empty
- Run a manual refresh: `CALL SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REFRESH_PRICING_FROM_PDF();`
- Confirm network access to `https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf`.
- Verify task `PRICING_REFRESH_TASK` is started: `ALTER TASK ... RESUME;`

## Streamlit app cannot load pricing
- Ensure `PRICING_CURRENT` has rows; check `is_estimate` flags and `refreshed_at`.
- Confirm stage upload completed: `LIST @SNOWFLAKE_EXAMPLE.REPLICATION_CALC.STREAMLIT_STAGE;`

## Database list empty
- Confirm role has access to `SNOWFLAKE.ACCOUNT_USAGE.DATABASES`.
- Check warehouse running: `ALTER WAREHOUSE SFE_REPLICATION_CALC_WH RESUME;`

## Expiration failure
- If `deploy_all.sql` aborts due to expiration (after 2026-01-07), extend or clone with a new expiration date per project policy.
