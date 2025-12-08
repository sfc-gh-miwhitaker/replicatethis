#!/usr/bin/env bash
set -euo pipefail

echo "=== Status Checklist (Snowsight-only) ==="
echo "- Warehouse state:"
echo "  SHOW WAREHOUSES LIKE 'SFE_REPLICATION_CALC_WH';"
echo "- Task state:"
echo "  SHOW TASKS LIKE 'PRICING_REFRESH_TASK';"
echo "- Stages:"
echo "  LIST @SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICE_STAGE;"
echo "  LIST @SNOWFLAKE_EXAMPLE.REPLICATION_CALC.STREAMLIT_STAGE;"
echo "- Pricing table rows:"
echo "  SELECT COUNT(*) FROM SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_CURRENT;"
echo "- DB metadata view sample:"
echo "  SELECT * FROM SNOWFLAKE_EXAMPLE.REPLICATION_CALC.DB_METADATA LIMIT 5;"
