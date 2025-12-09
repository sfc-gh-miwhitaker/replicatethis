# Troubleshooting - Streamlit DR Replication Cost Calculator

## Pricing Issues

### Pricing table empty
- Run a manual refresh: `CALL SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REFRESH_PRICING_FROM_PDF();`
- Confirm network access to `https://www.snowflake.com/legal-files/CreditConsumptionTable.pdf`.
- Verify task `PRICING_REFRESH_TASK` is started: `ALTER TASK PRICING_REFRESH_TASK RESUME;`
- Check fallback rates loaded: `SELECT COUNT(*) FROM PRICING_FALLBACK;` (should be 12 rows)

### Network/Firewall Issues
**Symptom:** PDF fetch fails with timeout or connection errors

**Cause:** Snowflake warehouse cannot reach external URL

**Solutions:**
1. **Check External Access:**
   ```sql
   -- Verify network rule exists (may be required in some environments)
   SHOW NETWORK RULES;
   ```

2. **Test connectivity from warehouse:**
   ```sql
   -- Run from worksheet using SFE_REPLICATION_CALC_WH
   USE WAREHOUSE SFE_REPLICATION_CALC_WH;
   CALL REFRESH_PRICING_FROM_PDF();
   -- Check error message in PRICING_RAW table
   SELECT CONTENT_BASE64 FROM PRICING_RAW ORDER BY INGESTED_AT DESC LIMIT 1;
   ```

3. **Fallback mode:**
   - If PDF is persistently unavailable, the system uses fallback rates from `PRICING_FALLBACK` table
   - All costs will be marked as estimates
   - Update fallback rates manually if needed:
     ```sql
     UPDATE PRICING_FALLBACK
     SET RATE = 2.75
     WHERE SERVICE_TYPE = 'DATA_TRANSFER' AND CLOUD = 'AWS';
     ```

## Privilege Issues

### Insufficient Privileges Error
**Symptom:** `SQL access control error: Insufficient privileges to operate on...`

**Cause:** Missing grants on required objects

**Solutions:**

1. **For deployment (ACCOUNTADMIN required):**
   ```sql
   USE ROLE ACCOUNTADMIN;
   -- Re-run deploy_all.sql
   ```

2. **For regular usage (any user):**
   ```sql
   -- Objects are granted to PUBLIC, any role can access
   USE ROLE PUBLIC;
   SELECT * FROM SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_CURRENT;
   ```

3. **Grant ACCOUNT_USAGE access (if DB_METADATA view returns empty):**
   ```sql
   USE ROLE ACCOUNTADMIN;
   GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE PUBLIC;
   -- Or grant to your specific role:
   GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <YOUR_ROLE>;
   ```

4. **Check specific object grants:**
   ```sql
   SHOW GRANTS TO ROLE PUBLIC;
   SHOW GRANTS ON SCHEMA SNOWFLAKE_EXAMPLE.REPLICATION_CALC;
   ```

### Task Execution Failures
**Symptom:** `PRICING_REFRESH_TASK` not running or failing

**Solutions:**
1. **Check task status:**
   ```sql
   SHOW TASKS LIKE 'PRICING_REFRESH_TASK' IN SCHEMA SNOWFLAKE_EXAMPLE.REPLICATION_CALC;
   SELECT * FROM TABLE(INFORMATION_SCHEMA.TASK_HISTORY(
       TASK_NAME => 'PRICING_REFRESH_TASK',
       SCHEDULED_TIME_RANGE_START => DATEADD('day', -7, CURRENT_TIMESTAMP())
   ));
   ```

2. **Ensure task ownership:**
   ```sql
   USE ROLE ACCOUNTADMIN;
   ALTER TASK PRICING_REFRESH_TASK RESUME;
   ```

3. **Check warehouse availability:**
   ```sql
   SHOW WAREHOUSES LIKE 'SFE_REPLICATION_CALC_WH';
   -- Ensure state is not SUSPENDED and auto_resume is TRUE
   ```

## Streamlit App Issues

### Streamlit app cannot load pricing
- Ensure `PRICING_CURRENT` has rows; check `is_estimate` flags and `refreshed_at`.
- Verify Streamlit app was created:
  ```sql
  SHOW STREAMLITS IN SCHEMA SNOWFLAKE_EXAMPLE.REPLICATION_CALC;
  ```
- Check app is loading from correct Git path:
  ```sql
  -- App should use: @SNOWFLAKE_EXAMPLE.TOOLS.REPLICATE_THIS_REPO/branches/main/streamlit
  DESC STREAMLIT REPLICATION_CALCULATOR;
  ```
- Confirm PUBLIC has access:
  ```sql
  SHOW GRANTS ON STREAMLIT REPLICATION_CALCULATOR;
  ```

### Database list empty
**Symptom:** No databases appear in multiselect dropdown

**Cause:** Missing access to `SNOWFLAKE.ACCOUNT_USAGE`

**Solutions:**
1. Grant IMPORTED PRIVILEGES:
   ```sql
   USE ROLE ACCOUNTADMIN;
   GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <YOUR_ROLE>;
   ```

2. Verify warehouse is running:
   ```sql
   ALTER WAREHOUSE SFE_REPLICATION_CALC_WH RESUME;
   SHOW WAREHOUSES LIKE 'SFE_REPLICATION_CALC_WH';
   ```

3. Test DB_METADATA view manually:
   ```sql
   -- Use any role (PUBLIC has access)
   SELECT * FROM SNOWFLAKE_EXAMPLE.REPLICATION_CALC.DB_METADATA LIMIT 5;
   ```

### Data Staleness Warning
**Symptom:** Database sizes show old dates in `AS_OF` column

**Cause:** `DATABASE_STORAGE_USAGE_HISTORY` updates daily with latency

**Solution:**
- This is normal; storage metrics have 1-2 day latency
- Check `DATA_AGE_DAYS` column in `DB_METADATA` view
- For current estimates, use known database sizes

## Deployment Issues

### Expiration failure
- If `deploy_all.sql` aborts due to expiration (after 2026-01-07), extend or clone with a new expiration date per project policy.
- Update `SET EXPIRATION_DATE = '2026-01-07'::DATE;` at top of script

### API Integration Already Exists
**Symptom:** `SQL compilation error: Object 'SFE_GIT_API_INTEGRATION' already exists`

**Solution:**
- This is expected and safe (idempotent)
- The script uses `CREATE OR REPLACE` for most objects
- Continue execution

### Role/Warehouse Name Conflicts
**Symptom:** Objects with `SFE_` prefix already exist from other demos

**Solution:**
- This is expected per demo standards
- `SFE_GIT_API_INTEGRATION` is shared across all demos
- Project-specific objects are in dedicated schema `REPLICATION_CALC`

## Performance Issues

### Slow Pricing Refresh
**Symptom:** `REFRESH_PRICING_FROM_PDF()` takes >60 seconds

**Cause:** Network latency or PDF download timeout

**Solutions:**
1. Check retry logic in procedure (3 attempts with 5s delay)
2. Increase warehouse size if needed:
   ```sql
   ALTER WAREHOUSE SFE_REPLICATION_CALC_WH SET WAREHOUSE_SIZE = SMALL;
   ```
3. Monitor execution:
   ```sql
   SELECT * FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
   WHERE QUERY_TEXT LIKE '%REFRESH_PRICING_FROM_PDF%'
   ORDER BY START_TIME DESC LIMIT 5;
   ```

### Streamlit App Slow to Load
**Solutions:**
1. Ensure warehouse is auto-resume enabled
2. Check database count (large account with 1000+ databases may be slow)
3. Use filtering in SQL if needed:
   ```sql
   -- Modify DB_METADATA view to filter system databases
   WHERE DATABASE_NAME NOT LIKE 'SNOWFLAKE%'
   ```

## Getting Additional Help

If issues persist:
1. Check Snowflake query history for detailed error messages
2. Review `PRICING_RAW` table for PDF fetch diagnostics
3. Verify all prerequisites in `docs/01-SETUP.md`
4. Consult Snowflake documentation for RBAC and account usage
