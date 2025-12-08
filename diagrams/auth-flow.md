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
  actor Admin as ACCOUNTADMIN
  actor User as Cost Analyst
  participant Snowsight
  participant Streamlit as Streamlit App
  participant SF as Snowflake

  Admin->>Snowsight: Login with SSO/Keypair
  Admin->>SF: Run deploy_all.sql (create schema, stage, tables, proc, task, app)
  User->>Snowsight: Login (SSO/Keypair)
  User->>Streamlit: Open REPLICATION_CALCULATOR
  Streamlit->>SF: Query PRICING_CURRENT, DB_METADATA (role-based access)
  User->>Streamlit: Click "Refresh pricing now"
  Streamlit->>SF: CALL REFRESH_PRICING_FROM_PDF (uses bound role/warehouse)
```

## Component Descriptions
- Identity: SSO/Keypair via Snowsight; roles managed in Snowflake.
- Roles: `ACCOUNTADMIN` for deploy; app runs with assigned app role to read pricing/metadata and call proc.
- Session: Snowsight-provided session passed to Streamlit app.
- Authorization: SQL grants to schema/tables/procedure; task runs with owner’s rights.
- Warehouse: `SFE_REPLICATION_CALC_WH` for pricing refresh/task and metadata queries.

## Change History
See `.cursor/DIAGRAM_CHANGELOG.md` for vhistory.
