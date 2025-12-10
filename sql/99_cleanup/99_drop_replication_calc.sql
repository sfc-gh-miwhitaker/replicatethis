/*****************************************************************************
 * CLEANUP SCRIPT: Replication Cost Calculator Demo
 *
 * Author: SE Community
 * Purpose: Removes all objects created by deploy_all.sql
 * Expires: 2026-01-07
 *
 * USAGE:
 * 1. Copy this entire script into Snowsight
 * 2. Click "Run All" to remove all demo objects
 * 3. Verify cleanup completed successfully
 *
 * SAFETY: Uses IF EXISTS - safe to run multiple times
 *
 * NOTE: Does NOT remove shared infrastructure:
 * - SFE_GIT_API_INTEGRATION (may be used by other demos)
 * - SNOWFLAKE_EXAMPLE database (contains other demos)
 * - SNOWFLAKE_EXAMPLE.TOOLS schema (shared Git repos)
 *****************************************************************************/

-- ============================================================================
-- CONTEXT SETTING (MANDATORY)
-- ============================================================================
-- Cleanup script: Uses SYSADMIN for most drops, ACCOUNTADMIN for integrations.
-- No specific database/warehouse context needed (drops are fully qualified).
-- ============================================================================
USE ROLE SYSADMIN;

/*****************************************************************************
 * SECTION 1: Suspend and Drop Tasks
 * Must suspend before dropping to avoid active task errors
 *****************************************************************************/

-- Suspend task first (required before drop)
ALTER TASK IF EXISTS SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_REFRESH_TASK
SUSPEND;

-- Drop the task
DROP TASK IF EXISTS SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_REFRESH_TASK;

/*****************************************************************************
 * SECTION 2: Drop Application Objects
 *****************************************************************************/

-- Drop Streamlit app (created by deploy_all.sql)
DROP STREAMLIT IF EXISTS SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REPLICATION_CALCULATOR;

/*****************************************************************************
 * SECTION 3: Drop Schema (CASCADE removes all tables, views, stages, procs)
 *****************************************************************************/

-- CASCADE will drop:
-- - PRICING_DATA table
-- - REPLICATION_GROUPS table
-- - V_PRICING_SUMMARY view
-- - PRICE_STAGE stage
-- - REFRESH_PRICING_FROM_PDF() procedure
DROP SCHEMA IF EXISTS SNOWFLAKE_EXAMPLE.REPLICATION_CALC CASCADE;

/*****************************************************************************
 * SECTION 4: Drop Warehouse
 *****************************************************************************/

DROP WAREHOUSE IF EXISTS SFE_REPLICATION_CALC_WH;

/*****************************************************************************
 * SECTION 5: Drop External Access Objects (ACCOUNTADMIN)
 * These are project-specific and safe to remove
 *****************************************************************************/
USE ROLE ACCOUNTADMIN;

-- Drop external access integration (used by pricing refresh procedure)
DROP INTEGRATION IF EXISTS SFE_SNOWFLAKE_PDF_ACCESS;

-- Drop network rule (allows HTTPS to www.snowflake.com)
DROP NETWORK RULE IF EXISTS SFE_SNOWFLAKE_PDF_NETWORK_RULE;

/*****************************************************************************
 * VERIFICATION: Show remaining objects
 *****************************************************************************/

-- Verify schema is gone
SHOW SCHEMAS LIKE 'REPLICATION_CALC' IN DATABASE SNOWFLAKE_EXAMPLE;

-- Verify warehouse is gone
SHOW WAREHOUSES LIKE 'SFE_REPLICATION_CALC_WH';

-- Final status
SELECT '✅ Cleanup Complete!' AS status,
       'All demo objects have been removed' AS message,
       'Shared infrastructure (Git integration, SNOWFLAKE_EXAMPLE DB) preserved'
           AS note;
