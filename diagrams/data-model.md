# Data Model - Streamlit DR Replication Cost Calculator
Author: SE Community
Last Updated: 2025-12-08
Expires: 2026-01-07
Status: Reference Implementation

![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?style=for-the-badge&logo=snowflake&logoColor=white)

Reference Implementation: This code demonstrates production-grade architectural patterns and best practices. Review and customize security, networking, and logic for your organization's specific requirements before deployment.

## Overview
Data model for pricing ingestion, normalized rates, and database metadata used by the Streamlit replication/DR cost calculator (Business Critical).

```mermaid
erDiagram
  PRICING_RAW {
    string source_url
    string content_base64
    timestamp ingested_at
  }
  PRICING_CURRENT {
    string service_type
    string cloud
    string region
    string unit
    number rate
    string currency
    boolean is_estimate
    timestamp refreshed_at
  }
  DB_METADATA {
    string database_name
    number size_tb
    timestamp as_of
  }

  PRICING_RAW ||--|| PRICING_CURRENT : "parsed into"
  PRICING_CURRENT ||--o{ DB_METADATA : "used for cost calc"
```

## Component Descriptions
- PRICING_RAW: Stores fetched Credit Consumption PDF content (base64) and source URL.
- PRICING_CURRENT: Normalized pricing rows (BC rates) per service/cloud/region with estimate flag and refreshed_at.
- DB_METADATA: Latest database sizes from ACCOUNT_USAGE for sizing transfer/storage.

## Change History
See `.cursor/DIAGRAM_CHANGELOG.md` for vhistory.
