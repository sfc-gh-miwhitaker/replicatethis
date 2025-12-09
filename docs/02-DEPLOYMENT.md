# Deployment - Streamlit DR Replication Cost Calculator (Business Critical)

## One-Script Deployment (Snowsight)

**Total deployment time: ~5 minutes**

### Steps

1. **Open Snowsight**: Navigate to Worksheets
2. **Copy the script**: Open `deploy_all.sql` from the repository root
3. **Paste into Snowsight**: Create a new worksheet and paste the entire script
4. **Run All**: Click "Run All" button (or press Cmd/Ctrl + Enter repeatedly)

### What the Script Does

The `deploy_all.sql` script automatically:

#### Phase 1: Git Integration (ACCOUNTADMIN)
- ✅ Checks expiration date (expires 2026-01-07)
- ✅ Creates `SFE_GIT_API_INTEGRATION` (if not exists)
- ✅ Creates `SNOWFLAKE_EXAMPLE.TOOLS` schema
- ✅ Creates Git repository: `REPLICATE_THIS_REPO`
- ✅ Fetches latest code from GitHub

#### Phase 2: Object Creation (SYSADMIN)
- ✅ Switches to SYSADMIN role
- ✅ Creates warehouse: `SFE_REPLICATION_CALC_WH`
- ✅ Creates schema: `SNOWFLAKE_EXAMPLE.REPLICATION_CALC`
- ✅ Creates stage: `PRICE_STAGE`
- ✅ **Creates Streamlit app: `REPLICATION_CALCULATOR`** (auto-deployed from Git)
- ✅ Creates tables: `PRICING_RAW`, `PRICING_CURRENT`, `PRICING_HISTORY`, `PRICING_FALLBACK`
- ✅ Creates view: `DB_METADATA`
- ✅ Creates procedure: `REFRESH_PRICING_FROM_PDF()`
- ✅ Creates task: `PRICING_REFRESH_TASK` (daily at 7am UTC)
- ✅ Calls initial pricing refresh

#### Phase 3: Access Grants (SYSADMIN)
- ✅ Grants USAGE on warehouse to PUBLIC
- ✅ Grants SELECT on tables/views to PUBLIC
- ✅ Grants USAGE on Streamlit app to PUBLIC
- ✅ Grants OPERATE on task to SYSADMIN

### Verify Deployment

After "Run All" completes, you should see:

```
✅ Deployment Complete!
Open Snowsight → Streamlit → REPLICATION_CALCULATOR
```

**Note:** The script grants ACCOUNT_USAGE access to SYSADMIN (already has it by default). Database sizes will populate from `SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY` (1-2 day latency for new databases).

### Next Steps

1. Navigate to Snowsight → Streamlit → `REPLICATION_CALCULATOR`
2. See `docs/03-USAGE.md` for how to use the calculator

## Manual Pricing Refresh (Optional)

The script automatically refreshes pricing on deployment. To manually refresh:

```sql
CALL SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REFRESH_PRICING_FROM_PDF();
```

## Troubleshooting

If deployment fails, see `docs/04-TROUBLESHOOTING.md`.

## Cleanup

To remove all demo objects:

```sql
-- Copy and run sql/99_cleanup/99_drop_replication_calc.sql
```

This removes:
- Schema `SNOWFLAKE_EXAMPLE.REPLICATION_CALC` (CASCADE)
- Warehouse `SFE_REPLICATION_CALC_WH`
- Streamlit app `REPLICATION_CALCULATOR`
- Task `PRICING_REFRESH_TASK`

**Preserved (shared infrastructure):**
- `SFE_GIT_API_INTEGRATION` (may be used by other demos)
- `SNOWFLAKE_EXAMPLE` database
- `SNOWFLAKE_EXAMPLE.TOOLS` schema and Git repository
