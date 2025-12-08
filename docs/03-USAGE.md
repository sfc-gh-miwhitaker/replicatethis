# Usage - Streamlit DR Replication Cost Calculator (Business Critical)

## Launch
1. Open Snowsight ➜ Apps ➜ `REPLICATION_CALCULATOR`.
2. Wait for the session to load pricing and database metadata.

## Workflow
1. **Pricing freshness**: Check the timestamp and source version. If empty or stale, click “Refresh pricing now” to call the Snowpark procedure (pulls the PDF).
2. **Select database(s)**: Choose one or more databases. Sizes come from `DB_METADATA` (latest storage history).
3. **Choose destination**: Pick destination cloud/region. Source cloud/region derive from `CURRENT_REGION()`.
4. **Change rate & cadence**: Set daily change % and refresh cadence (per day). The calculator estimates transfer volume from size × change × cadence.
5. **Review costs**: See itemized costs:
   - Data transfer (source cloud/region ➜ destination)
   - Replication compute (REPLICATION service type)
   - Storage for secondary
   - Serverless maintenance (MVs/search optimization) if present in pricing
6. **Export**: Download table as CSV for records (from the Streamlit UI).

## Assumptions
- Business Critical pricing/features.
- Rates sourced from the Credit Consumption Table; entries flagged if estimates.
- Storage uses destination region pricing; data transfer uses source region pricing; replication compute uses Business Critical REPLICATION rate.

## Manual refresh (SQL alternative)
```sql
CALL SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REFRESH_PRICING_FROM_PDF();
```
