import math
import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import functions as F

session = get_active_session()


def load_pricing():
    df = session.table("SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_CURRENT")
    rows = df.collect()
    if not rows:
        return [], None
    refreshed_at = max(r.REFRESHED_AT for r in rows)
    return rows, refreshed_at


def load_db_metadata():
    df = session.table("SNOWFLAKE_EXAMPLE.REPLICATION_CALC.DB_METADATA")
    return df.collect()


def run_pricing_refresh():
    return session.sql(
        "CALL SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REFRESH_PRICING_FROM_PDF()"
    ).collect()


def cost_lookup(pricing_rows, service_type, cloud, region):
    for r in pricing_rows:
        if (
            r.SERVICE_TYPE == service_type
            and r.CLOUD.upper() == cloud.upper()
            and r.REGION.upper() == region.upper()
        ):
            return r.RATE, r.UNIT, r.IS_ESTIMATE
    return None, None, True


def main():
    st.title("Replication / DR Cost Calculator (Business Critical)")
    st.caption(
        "Business Critical pricing; rates sourced from Credit Consumption Table (estimates when parsing unavailable)."
    )

    pricing_rows, refreshed_at = load_pricing()
    if refreshed_at:
        st.success(f"Pricing refreshed at {refreshed_at}")
    else:
        st.warning("No pricing data found. Run a manual refresh.")

    if st.button("Refresh pricing now"):
        with st.spinner("Refreshing pricing from PDF..."):
            res = run_pricing_refresh()
        st.info(res[0][0] if res else "Refresh invoked.")
        pricing_rows, refreshed_at = load_pricing()

    db_rows = load_db_metadata()
    db_options = {r.DATABASE_NAME: r for r in db_rows}
    selected_dbs = st.multiselect("Select databases", db_options.keys())

    source_region = session.sql("SELECT CURRENT_REGION()").collect()[0][0]
    source_cloud = source_region.split(':')[0] if ':' in source_region else source_region.split('-')[0]

    dest_regions = sorted({r.REGION for r in pricing_rows})
    dest_region = st.selectbox("Destination region", dest_regions) if dest_regions else None
    dest_cloud = dest_region.split('-')[0] if dest_region else source_cloud

    daily_change_pct = st.slider("Daily change rate (%)", 0.0, 20.0, 5.0, 0.5)
    refresh_per_day = st.slider("Refreshes per day", 0.0, 24.0, 1.0, 0.5)

    total_size_tb = sum(db_options[n].SIZE_TB for n in selected_dbs) if selected_dbs else 0
    change_tb_per_refresh = total_size_tb * (daily_change_pct / 100.0)
    daily_transfer_tb = change_tb_per_refresh * refresh_per_day

    transfer_rate, _, transfer_est = cost_lookup(pricing_rows, "DATA_TRANSFER", source_cloud, source_region)
    compute_rate, _, compute_est = cost_lookup(pricing_rows, "REPLICATION_COMPUTE", source_cloud, source_region)
    storage_rate, _, storage_est = cost_lookup(pricing_rows, "STORAGE_TB_MONTH", dest_cloud, dest_region) if dest_region else (None, None, True)
    serverless_rate, _, serverless_est = cost_lookup(pricing_rows, "SERVERLESS_MAINT", dest_cloud, dest_region) if dest_region else (None, None, True)

    transfer_cost = (daily_transfer_tb * (transfer_rate or 0.0))
    compute_cost = (daily_transfer_tb * (compute_rate or 0.0))
    storage_cost = (total_size_tb * (storage_rate or 0.0))
    serverless_cost = (total_size_tb * (serverless_rate or 0.0))
    total_cost = transfer_cost + compute_cost + storage_cost + serverless_cost

    st.subheader("Assumptions")
    st.write(
        f"Source cloud/region: {source_cloud} / {source_region} | Destination: {dest_cloud or '-'} / {dest_region or '-'}"
    )
    st.write(
        f"Daily change: {daily_change_pct}% | Refreshes/day: {refresh_per_day} | Selected DB size: {total_size_tb:.3f} TB"
    )

    st.subheader("Cost Estimate (credits)")
    st.table(
        [
            {"Component": "Data Transfer", "Credits": transfer_cost, "Estimate": transfer_est},
            {"Component": "Replication Compute", "Credits": compute_cost, "Estimate": compute_est},
            {"Component": "Storage (secondary, monthly)", "Credits": storage_cost, "Estimate": storage_est},
            {"Component": "Serverless Maintenance (monthly)", "Credits": serverless_cost, "Estimate": serverless_est},
            {"Component": "Total (mix of daily/monthly)", "Credits": total_cost, "Estimate": any([transfer_est, compute_est, storage_est, serverless_est])},
        ]
    )

    st.subheader("Details")
    st.write("Rates are credits per unit. Data transfer/compute use per-TB of change data; storage/serverless use TB-month.")
    st.write("Values marked as estimates rely on fallback rates when PDF parsing is unavailable.")

    st.download_button(
        label="Download estimate as CSV",
        data="component,credits\n"
        + "\n".join(
            [
                f"Data Transfer,{transfer_cost}",
                f"Replication Compute,{compute_cost}",
                f"Storage (monthly),{storage_cost}",
                f"Serverless Maintenance (monthly),{serverless_cost}",
                f"Total,{total_cost}",
            ]
        ),
        file_name="replication_cost_estimate.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
