# Setup - Streamlit DR Replication Cost Calculator (Business Critical)

## Prerequisites
- Snowflake Business Critical edition (required for replication/failover features).
- Roles: `ACCOUNTADMIN` (for setup) and a working warehouse quota.
- Network access to fetch `https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf` from inside Snowflake.

## Steps (Snowsight-only)
1. Sign in to Snowsight with `ACCOUNTADMIN`.
2. Set a worksheet context to your target account.
3. Continue to `docs/02-DEPLOYMENT.md` to run `deploy_all.sql`.

## Security & Naming
- All objects live in `SNOWFLAKE_EXAMPLE.REPLICATION_CALC`.
- Warehouse uses `SFE_REPLICATION_CALC_WH` (SFE_ prefix for account-level objects).
- No credentials are stored; all external access is to the public PDF URL.
