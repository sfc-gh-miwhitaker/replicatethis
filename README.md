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
Follow these in order:
1. `docs/01-SETUP.md` — Environment & role checks (5 min)
2. `tools/00_master.sh` or `.bat` — Orchestrator (1 min)
3. `docs/02-DEPLOYMENT.md` — Run `deploy_all.sql` in Snowsight (10 min)
4. `docs/03-USAGE.md` — Launch the Streamlit app and refresh pricing (10 min)
5. `docs/04-TROUBLESHOOTING.md` — Common fixes (3 min)
Total setup time: ~29 minutes

## Quick Start
- Open Snowsight ➜ Worksheets ➜ paste `deploy_all.sql` ➜ Run All (template-aligned).
- Upload `streamlit/app.py` to `@SNOWFLAKE_EXAMPLE.REPLICATION_CALC.STREAMLIT_STAGE` and create the Streamlit app.
- Open the app, trigger a pricing refresh from Snowflake’s Credit Consumption PDF, pick source/destination regions, and review the itemized replication/DR costs.

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
- All Snowflake objects live under `SNOWFLAKE_EXAMPLE.REPLICATION_CALC`; warehouse uses `SFE_REPLICATION_CALC_WH` (expires 2026-01-07 in comments).
- Demo uses Business Critical features/pricing. Refresh pricing regularly to stay current.
- Expiration guard enforced in `deploy_all.sql` (expires 2026-01-07) and auto-archive workflow in `.github/workflows/expire-demo.yml`.
- Custom role `SFE_REPLICATION_CALC_ROLE` available for read-only access (use instead of ACCOUNTADMIN in production).
