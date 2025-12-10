# Data Flow - Streamlit DR Replication Cost Calculator
Author: SE Community
Last Updated: 2025-12-10
Expires: 2026-01-07
Status: Reference Implementation

![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?style=for-the-badge&logo=snowflake&logoColor=white)

Reference Implementation: This code demonstrates production-grade architectural patterns and best practices. Review and customize security, networking, and logic for your organization's specific requirements before deployment.

## Overview
Data ingestion and transformation flow for replication/DR cost estimation using Business Critical pricing.

```mermaid
graph TB
  subgraph "External"
    PDF[Credit Consumption PDF<br/>snowflake.com/legal-files/CreditConsumptionTable.pdf]
  end
  subgraph "SNOWFLAKE_EXAMPLE.REPLICATION_CALC"
    Stage[PRICE_STAGE<br/>PDF staging]
    Raw[(PRICING_RAW<br/>Audit Trail)]
    Proc[REFRESH_PRICING_FROM_PDF<br/>Snowpark Python<br/>AI_PARSE_DOCUMENT]
    Current[(PRICING_CURRENT<br/>Active Rates)]
    DBMeta[(DB_METADATA view)]
    Streamlit[Streamlit App<br/>Cost Calculator]
    Task[PRICING_REFRESH_TASK<br/>Daily 7am UTC]
  end
  subgraph "SNOWFLAKE.ACCOUNT_USAGE"
    Storage[(TABLE_STORAGE_METRICS)]
  end
  subgraph "GitHub Repository"
    GitRepo[Git Repo<br/>sfc-gh-miwhitaker/replicatethis]
  end

  GitRepo -->|deployed from| Streamlit
  PDF -->|External Access| Proc
  Proc -->|stages PDF| Stage
  Proc -->|AI_PARSE_DOCUMENT| Stage
  Proc -->|records fetch| Raw
  Proc -->|truncate & reload| Current
  Storage -->|SUM ACTIVE_BYTES| DBMeta
  DBMeta --> Streamlit
  Current --> Streamlit
  Streamlit -->|costs in Credits + USD| User[End User]
  Streamlit -->|CSV export| User
  Task -->|triggers| Proc
```

## Component Descriptions

### Data Storage
- **PRICE_STAGE**: Internal stage for staging the Credit Consumption PDF for AI parsing
- **PRICING_RAW**: Audit trail recording PDF fetch status and timestamps
- **PRICING_CURRENT**: Active normalized rates per cloud/region/service with IS_ESTIMATE flag
- **DB_METADATA**: View joining INFORMATION_SCHEMA.DATABASES with TABLE_STORAGE_METRICS for sizes

### Processing
- **REFRESH_PRICING_FROM_PDF**: Snowpark Python procedure with AI parsing
  - Downloads PDF via External Access Integration
  - Stages PDF to PRICE_STAGE
  - Calls SNOWFLAKE.CORTEX.PARSE_DOCUMENT for text extraction
  - Attempts to parse pricing tables from extracted content
  - Falls back to hardcoded rates if parsing fails (IS_ESTIMATE = TRUE)
- **PRICING_REFRESH_TASK**: Scheduled task running daily at 7am UTC

### User Interface
- **Streamlit App**: Auto-deployed from Git repository
  - Loads directly from `@SNOWFLAKE_EXAMPLE.TOOLS.REPLICATE_THIS_REPO/branches/main/streamlit`
  - No manual file uploads required
  - Interactive cost calculator with:
    - Price per credit input for contract/discount pricing
    - Dual display: Credits AND USD costs
    - Cloud/region selection (source auto-detected, destination selectable)
    - Daily, monthly, and annual cost projections
    - Lowest-cost region recommendations
    - CSV export with full assumptions and USD values

## Key Features

### Native Snowflake Architecture
- External Access Integration for PDF download (no external orchestration)
- AI_PARSE_DOCUMENT for native PDF text extraction
- Streamlit in Snowflake for UI (no external hosting)
- Git repository integration (auto-deploy from GitHub)

### Reliability
- Fallback rates ensure app always functional
- Graceful error handling throughout
- IS_ESTIMATE flag indicates data source (parsed vs fallback)

### Usability
- Price per credit slider for discount calculations
- Costs shown in both Credits and USD
- Database selection with size display
- Data freshness indicator (AS_OF timestamp)
- CSV export with all assumptions documented

### Security & Governance
- Role-based security: ACCOUNTADMIN → SYSADMIN → PUBLIC
- Minimal privilege: ACCOUNTADMIN only for account-level objects
- Objects owned by SYSADMIN (best practice)
- PUBLIC granted read-only access (SELECT, USAGE)
- Audit trail in PRICING_RAW table

## Change History
See `.cursor/DIAGRAM_CHANGELOG.md` for vhistory.
