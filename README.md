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
2. `docs/02-DEPLOYMENT.md` — Run `deploy_all.sql` in Snowsight (10 min)
3. `docs/03-USAGE.md` — Launch the Streamlit app and refresh pricing (10 min)
4. `docs/04-TROUBLESHOOTING.md` — Common fixes (3 min)
Total setup time: ~28 minutes

## Quick Start
- Open Snowsight ➜ Worksheets ➜ paste `deploy_all.sql` ➜ Run All.
- Upload `streamlit/app.py` to the created stage (see `docs/02-DEPLOYMENT.md`) and create the Streamlit app.
- Open the app, trigger a pricing refresh from Snowflake’s Credit Consumption PDF, pick source/destination regions, and review the itemized replication/DR costs.

## What This Delivers
- Snowflake-only Streamlit app for replication/DR cost estimation using Business Critical pricing.
- Scheduled pricing refresh task that ingests the public Credit Consumption PDF into normalized rates.
- Database metadata view for selecting databases and sizing transfer.
- Architecture diagrams in `diagrams/` (Mermaid source of truth).

## Notes
- All Snowflake objects live under `SNOWFLAKE_EXAMPLE.REPLICATION_CALC`; warehouse uses `SFE_REPLICATION_CALC_WH`.
- Demo uses Business Critical features/pricing. Refresh pricing regularly to stay current.
- Expiration guard enforced in `deploy_all.sql` (fails after 2026-01-07).
