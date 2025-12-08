#!/usr/bin/env bash
set -euo pipefail

echo "=== Replication Cost Calculator Orchestrator (Snowsight-only) ==="
echo "1) Run docs/01-SETUP.md prerequisites (ACCOUNTADMIN, BC edition)"
echo "2) Open Snowsight and run deploy_all.sql (copy/paste, Run All)"
echo "3) Upload streamlit/app.py to @SNOWFLAKE_EXAMPLE.REPLICATION_CALC.STREAMLIT_STAGE"
echo "4) Create Streamlit app pointing to app.py"
echo "5) Optional: CALL SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REFRESH_PRICING_FROM_PDF()"
echo
echo "Helper scripts:"
echo "  tools/02_start.sh   - Reminder to resume warehouse/task if paused"
echo "  tools/03_status.sh  - Prints expected objects/stages"
echo "  tools/04_stop.sh    - Suggests suspending warehouse/task"
echo
echo "Note: No local services are started in Snowsight-only mode."
