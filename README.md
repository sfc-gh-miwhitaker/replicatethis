# Streamlit DR Replication Cost Calculator (Business Critical)

![Reference Implementation](https://img.shields.io/badge/Reference-Implementation-blue)
![Ready to Run](https://img.shields.io/badge/Ready%20to%20Run-Yes-green)
![Expires](https://img.shields.io/badge/Expires-2026--01--07-orange)

> DEMONSTRATION PROJECT - EXPIRES: 2026-01-07
> This demo uses Snowflake features current as of December 2025.
> After expiration, this repository will be archived and made private.

**Author:** SE Community
**Purpose:** Reference implementation for a Snowflake-native Streamlit cost calculator for database replication/DR
**Created:** 2025-12-08 | **Expires:** 2026-01-07 (30 days) | **Status:** ACTIVE

## 👋 First Time Here?

**This is a 100% Snowflake-native demo. No local setup required!**

Follow these in order:
1. `docs/01-SETUP.md` — Prerequisites & role checks (2 min)
2. `docs/02-DEPLOYMENT.md` — Run `deploy_all.sql` in Snowsight (5 min)
3. `docs/03-USAGE.md` — Use the Streamlit app (5 min)
4. `docs/04-TROUBLESHOOTING.md` — Common fixes (reference as needed)

**Total setup time: ~10 minutes**

## Quick Start

1. **Deploy**: Open Snowsight → Worksheets → Paste `deploy_all.sql` → Run All
2. **Use**: Open Snowsight → Streamlit → `REPLICATION_CALCULATOR`
3. **Done**: Pick source/destination regions and review replication/DR costs

**That's it!** Everything runs inside Snowflake. No files to upload, no local tools needed.

## What This Delivers
- Snowflake-only Streamlit app for replication/DR cost estimation using Business Critical pricing.
- Scheduled pricing refresh task that ingests the public Credit Consumption PDF into normalized rates.
- Database metadata view for selecting databases and sizing transfer.
- Architecture diagrams in `diagrams/` (Mermaid source of truth).

## Important Notes

### Cost Disclaimer
**This calculator provides estimates for budgeting purposes only.** Actual costs may vary based on:
- Data compression ratios
- Network conditions and transfer speeds
- Actual change patterns vs. estimated rates
- Regional pricing variations
- Snowflake contract terms and discounts

Always monitor actual consumption using Snowflake's `ACCOUNT_USAGE` views and consult with your account team for production planning.

### Pre-Commit Hooks Setup
This project uses pre-commit hooks for code quality. To enable:
```bash
pip install pre-commit
pre-commit install
```

Hooks include:
- Secret detection (detect-secrets, gitleaks)
- SQL linting (sqlfluff)
- Trailing whitespace removal
- YAML validation

### Technical Details
- **Objects**: All under `SNOWFLAKE_EXAMPLE.REPLICATION_CALC` schema
- **Warehouse**: `SFE_REPLICATION_CALC_WH` (XSmall, auto-suspend)
- **Streamlit App**: Auto-deployed from Git repository (no manual uploads)
- **Security**: SYSADMIN owns objects, PUBLIC granted read access
- **Features**: Business Critical edition features/pricing
- **Expiration**: Enforced in `deploy_all.sql` and auto-archive workflow (`.github/workflows/expire-demo.yml`)
- **Pricing**: Automatically refreshed daily from Snowflake's public PDF
