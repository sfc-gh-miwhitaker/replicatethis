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
- ✅ **Creates Streamlit app: `REPLICATION_CALCULATOR`** (auto-deployed from Git)
- ✅ Creates table: `PRICING_CURRENT`
- ✅ Creates view: `DB_METADATA`
- ✅ Seeds pricing data (48 baseline rates for AWS/Azure/GCP)

#### Phase 3: Access Grants (SYSADMIN)
- ✅ Grants USAGE on warehouse to PUBLIC
- ✅ Grants SELECT on tables/views to PUBLIC
- ✅ Grants USAGE on Streamlit app to PUBLIC
- ✅ Grants INSERT/UPDATE/DELETE on PRICING_CURRENT to SYSADMIN

### Verify Deployment

After "Run All" completes, you should see:

```
✅ Deployment Complete!
Open Snowsight → Streamlit → REPLICATION_CALCULATOR
48 pricing rates loaded
```

**Note:** The script grants ACCOUNT_USAGE access to SYSADMIN (already has it by default). Database sizes will populate from `SNOWFLAKE.ACCOUNT_USAGE.DATABASE_STORAGE_USAGE_HISTORY` (1-2 day latency for new databases).

Pricing rates are pre-loaded baseline values. Administrators can update them via the Streamlit app's "Admin: Manage Pricing" page.

### Next Steps

1. Navigate to Snowsight → Streamlit → `REPLICATION_CALCULATOR`
2. See `docs/03-USAGE.md` for how to use the calculator and admin features

## Updating Pricing (Optional)

Administrators (SYSADMIN or ACCOUNTADMIN) can update pricing rates through the Streamlit app:

1. Navigate to Snowsight → Streamlit → `REPLICATION_CALCULATOR`
2. Use sidebar to switch to "Admin: Manage Pricing"
3. Edit rates in the data editor
4. Click "Save Changes"

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
