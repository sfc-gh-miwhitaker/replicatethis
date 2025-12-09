# Auth Flow - Streamlit DR Replication Cost Calculator
Author: SE Community
Last Updated: 2025-12-08
Expires: 2026-01-07
Status: Reference Implementation

![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?style=for-the-badge&logo=snowflake&logoColor=white)

Reference Implementation: This code demonstrates production-grade architectural patterns and best practices. Review and customize security, networking, and logic for your organization's specific requirements before deployment.

## Overview
Authentication and authorization for deployment and use of the replication/DR cost calculator in Snowflake (Business Critical).

```mermaid
sequenceDiagram
  actor Admin as Deploying Admin
  actor User as Any Snowflake User
  participant Snowsight
  participant Streamlit as Streamlit App
  participant SF as Snowflake

  Note over Admin,SF: Deployment Phase
  Admin->>Snowsight: Login (needs ACCOUNTADMIN)
  Admin->>SF: USE ROLE ACCOUNTADMIN
  SF->>SF: Create Git API Integration
  Admin->>SF: USE ROLE SYSADMIN
  SF->>SF: Create warehouse, schema, tables, views, proc, task, Streamlit app
  SF->>SF: GRANT SELECT/USAGE to PUBLIC

  Note over User,SF: Usage Phase
  User->>Snowsight: Login (any auth method)
  User->>Streamlit: Open REPLICATION_CALCULATOR
  Note over Streamlit: User has PUBLIC grants
  Streamlit->>SF: Query PRICING_CURRENT, DB_METADATA
  SF-->>Streamlit: Return data
  User->>Streamlit: Click "Refresh pricing now"
  Streamlit->>SF: CALL REFRESH_PRICING_FROM_PDF()
  SF-->>Streamlit: Pricing refreshed
```

## Component Descriptions

### Authentication
- **Identity**: SSO, Key Pair, or username/password via Snowsight
- **Session**: Snowsight-provided session passed to Streamlit app
- **No custom authentication**: Uses standard Snowflake auth mechanisms

### Authorization (Role-Based Security)

#### Deployment Roles
- **ACCOUNTADMIN**: Creates Git API integration only (line 30-43 in deploy_all.sql)
- **SYSADMIN**: Creates all database objects - owns them (line 58+ in deploy_all.sql)
  - Warehouse, schema, tables, views, stages, procedures, tasks, Streamlit app

#### Usage Roles
- **PUBLIC**: Granted SELECT and USAGE permissions (lines 246-258 in deploy_all.sql)
  - Any Snowflake user can run the demo
  - Read-only access to pricing tables/views
  - USAGE on warehouse for queries
  - USAGE on Streamlit app
  - Can execute the pricing refresh procedure

#### Task Execution
- **SYSADMIN**: Granted OPERATE on PRICING_REFRESH_TASK (line 261)
  - Task runs with owner's rights (SYSADMIN context)
  - Background process, not user-facing

### Warehouse
- **SFE_REPLICATION_CALC_WH**: Used by Streamlit app queries and pricing refresh
  - Auto-suspend after 5 minutes
  - Auto-resume on query
  - XSmall size for demo workloads

## Change History
See `.cursor/DIAGRAM_CHANGELOG.md` for vhistory.
