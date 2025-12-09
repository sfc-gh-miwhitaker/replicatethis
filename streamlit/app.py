import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.exceptions import SnowparkSQLException

session = get_active_session()


def load_pricing():
    try:
        df = session.table("SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_CURRENT")
        rows = df.collect()
        if not rows:
            return [], None
        refreshed_at = max(r.REFRESHED_AT for r in rows)
        return rows, refreshed_at
    except SnowparkSQLException as e:
        st.error(f"Failed to load pricing data: {str(e)}. Ensure deploy_all.sql was executed successfully.")
        return [], None
    except Exception as e:
        st.error(f"Unexpected error loading pricing: {str(e)}")
        return [], None


def load_db_metadata():
    try:
        df = session.table("SNOWFLAKE_EXAMPLE.REPLICATION_CALC.DB_METADATA")
        return df.collect()
    except SnowparkSQLException as e:
        st.error(f"Failed to load database metadata: {str(e)}. Check ACCOUNT_USAGE access.")
        return []
    except Exception as e:
        st.error(f"Unexpected error loading database metadata: {str(e)}")
        return []


def run_pricing_refresh():
    try:
        return session.sql(
            "CALL SNOWFLAKE_EXAMPLE.REPLICATION_CALC.REFRESH_PRICING_FROM_PDF()"
        ).collect()
    except SnowparkSQLException as e:
        st.error(f"Pricing refresh failed: {str(e)}. Check network access to Snowflake PDF URL.")
        return None
    except Exception as e:
        st.error(f"Unexpected error during pricing refresh: {str(e)}")
        return None


def get_cloud_and_region():
    try:
        # Get region name (format: cloud.region_name)
        region_result = session.sql("SELECT CURRENT_REGION()").collect()
        region_full = region_result[0][0] if region_result else "AWS_US_EAST_1"

        # Parse cloud from region string (e.g., "AWS_US_EAST_1" -> "AWS", "us-east-1")
        if region_full:
            parts = region_full.split("_", 1)
            if len(parts) >= 2:
                cloud = parts[0]  # AWS, AZURE, or GCP
                region = parts[1].lower().replace("_", "-")  # us-east-1
            else:
                cloud = "AWS"
                region = region_full.lower()
        else:
            cloud = "AWS"
            region = "us-east-1"

        return cloud, region
    except Exception as e:
        st.warning(f"Could not detect cloud/region: {str(e)}. Using defaults.")
        return "AWS", "us-east-1"


def cost_lookup(pricing_rows, service_type, cloud, region):
    for r in pricing_rows:
        if (
            r.SERVICE_TYPE == service_type
            and r.CLOUD.upper() == cloud.upper()
            and r.REGION.upper() == region.upper()
        ):
            # Convert Decimal to float for calculations
            rate = float(r.RATE) if r.RATE is not None else None
            return rate, r.UNIT, r.IS_ESTIMATE
    return None, None, True


def find_lowest_cost_regions(pricing_rows, service_types):
    region_costs = {}

    for r in pricing_rows:
        if r.SERVICE_TYPE in service_types:
            key = f"{r.CLOUD}:{r.REGION}"
            if key not in region_costs:
                region_costs[key] = 0
            region_costs[key] += r.RATE

    if not region_costs:
        return []

    sorted_regions = sorted(region_costs.items(), key=lambda x: x[1])
    return sorted_regions[:3]


def calculate_monthly_projection(daily_transfer_cost, daily_compute_cost, storage_cost, serverless_cost):
    days_per_month = 30
    monthly_transfer = daily_transfer_cost * days_per_month
    monthly_compute = daily_compute_cost * days_per_month
    monthly_total = monthly_transfer + monthly_compute + storage_cost + serverless_cost
    annual_total = monthly_total * 12

    return {
        "monthly_transfer": monthly_transfer,
        "monthly_compute": monthly_compute,
        "monthly_storage": storage_cost,
        "monthly_serverless": serverless_cost,
        "monthly_total": monthly_total,
        "annual_total": annual_total
    }


def generate_enhanced_csv(assumptions, costs, projections):
    csv_lines = ["# Snowflake Replication Cost Estimate"]
    csv_lines.append("")
    csv_lines.append("# Assumptions")
    csv_lines.append(f"Source Cloud,{assumptions['source_cloud']}")
    csv_lines.append(f"Source Region,{assumptions['source_region']}")
    csv_lines.append(f"Destination Cloud,{assumptions['dest_cloud']}")
    csv_lines.append(f"Destination Region,{assumptions['dest_region']}")
    csv_lines.append(f"Total Database Size (TB),{assumptions['total_size_tb']:.3f}")
    csv_lines.append(f"Daily Change Rate (%),{assumptions['daily_change_pct']:.1f}")
    csv_lines.append(f"Refreshes Per Day,{assumptions['refresh_per_day']:.1f}")
    csv_lines.append(f"Selected Databases,\"{assumptions['selected_dbs']}\"")
    csv_lines.append("")
    csv_lines.append("# Daily Costs (Credits)")
    csv_lines.append("Component,Credits,Is Estimate")
    csv_lines.append(f"Data Transfer,{costs['transfer_cost']:.2f},{costs['transfer_est']}")
    csv_lines.append(f"Replication Compute,{costs['compute_cost']:.2f},{costs['compute_est']}")
    csv_lines.append("")
    csv_lines.append("# Monthly Costs (Credits)")
    csv_lines.append("Component,Credits")
    csv_lines.append(f"Data Transfer (30 days),{projections['monthly_transfer']:.2f}")
    csv_lines.append(f"Replication Compute (30 days),{projections['monthly_compute']:.2f}")
    csv_lines.append(f"Storage,{projections['monthly_storage']:.2f}")
    csv_lines.append(f"Serverless Maintenance,{projections['monthly_serverless']:.2f}")
    csv_lines.append(f"Monthly Total,{projections['monthly_total']:.2f}")
    csv_lines.append("")
    csv_lines.append(f"# Annual Projection (Credits): {projections['annual_total']:.2f}")

    return "\n".join(csv_lines)


def main():
    st.title("Replication / DR Cost Calculator (Business Critical)")

    st.info(
        "**Disclaimer:** This calculator provides cost estimates for budgeting purposes only. "
        "Actual costs may vary based on usage patterns, data compression, and other factors. "
        "Always monitor actual consumption via Snowflake's usage views."
    )

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
        if res:
            st.info(res[0][0])
            pricing_rows, refreshed_at = load_pricing()

    db_rows = load_db_metadata()
    db_options = {r.DATABASE_NAME: r for r in db_rows}

    selected_dbs = st.multiselect("Select databases", sorted(db_options.keys()))

    if not selected_dbs and st.session_state.get('calculation_attempted'):
        st.warning("Please select at least one database to calculate costs.")

    source_cloud, source_region = get_cloud_and_region()

    dest_regions = sorted({r.REGION for r in pricing_rows})
    dest_region = st.selectbox("Destination region", dest_regions, index=0 if dest_regions else None) if dest_regions else None

    if dest_region:
        for r in pricing_rows:
            if r.REGION == dest_region:
                dest_cloud = r.CLOUD
                break
        else:
            dest_cloud = dest_region.split('-')[0]
    else:
        dest_cloud = source_cloud

    daily_change_pct = st.slider("Daily change rate (%)", 0.0, 20.0, 5.0, 0.5,
                                   help="Percentage of total data that changes each day")
    refresh_per_day = st.slider("Refreshes per day", 0.0, 24.0, 1.0, 0.5,
                                  help="Number of replication refresh operations per day")

    # Convert Decimal to float for calculations
    total_size_tb = float(sum(db_options[n].SIZE_TB for n in selected_dbs)) if selected_dbs else 0.0
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

    projections = calculate_monthly_projection(transfer_cost, compute_cost, storage_cost, serverless_cost)

    st.subheader("Assumptions")
    st.write(
        f"Source cloud/region: {source_cloud} / {source_region} | Destination: {dest_cloud or '-'} / {dest_region or '-'}"
    )
    st.write(
        f"Daily change: {daily_change_pct}% | Refreshes/day: {refresh_per_day} | Selected DB size: {total_size_tb:.3f} TB"
    )

    if selected_dbs:
        with st.expander("Selected databases detail"):
            for db_name in selected_dbs:
                db_info = db_options[db_name]
                age_indicator = ""
                if hasattr(db_info, 'AS_OF'):
                    age_indicator = f" (as of {db_info.AS_OF})"
                st.write(f"- {db_name}: {float(db_info.SIZE_TB):.3f} TB{age_indicator}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Daily Costs (Credits)")
        st.table(
            [
                {"Component": "Data Transfer", "Credits": f"{transfer_cost:.2f}", "Estimate": transfer_est},
                {"Component": "Replication Compute", "Credits": f"{compute_cost:.2f}", "Estimate": compute_est},
            ]
        )

    with col2:
        st.subheader("Monthly Costs (Credits)")
        st.table(
            [
                {"Component": "Transfer (30d)", "Credits": f"{projections['monthly_transfer']:.2f}"},
                {"Component": "Compute (30d)", "Credits": f"{projections['monthly_compute']:.2f}"},
                {"Component": "Storage", "Credits": f"{storage_cost:.2f}", "Estimate": storage_est},
                {"Component": "Serverless Maint", "Credits": f"{serverless_cost:.2f}", "Estimate": serverless_est},
            ]
        )

    st.metric("Monthly Total", f"{projections['monthly_total']:.2f} credits")
    st.metric("Annual Projection", f"{projections['annual_total']:.2f} credits")

    if pricing_rows:
        st.subheader("Cost Optimization")
        lowest_regions = find_lowest_cost_regions(pricing_rows, ["DATA_TRANSFER", "REPLICATION_COMPUTE", "STORAGE_TB_MONTH"])
        if lowest_regions:
            st.write("**Lowest cost destination regions:**")
            for region, cost in lowest_regions:
                st.write(f"- {region}: {cost:.2f} credits per TB (combined)")

    st.subheader("Details")
    st.write("Data transfer and compute costs shown as daily values based on change rate.")
    st.write("Storage and serverless maintenance are monthly costs based on total database size.")
    st.write("Values marked as estimates rely on fallback rates when PDF parsing is unavailable.")

    assumptions = {
        'source_cloud': source_cloud,
        'source_region': source_region,
        'dest_cloud': dest_cloud or 'N/A',
        'dest_region': dest_region or 'N/A',
        'total_size_tb': total_size_tb,
        'daily_change_pct': daily_change_pct,
        'refresh_per_day': refresh_per_day,
        'selected_dbs': ', '.join(selected_dbs) if selected_dbs else 'None'
    }

    costs = {
        'transfer_cost': transfer_cost,
        'compute_cost': compute_cost,
        'transfer_est': transfer_est,
        'compute_est': compute_est
    }

    csv_data = generate_enhanced_csv(assumptions, costs, projections)

    st.download_button(
        label="Download detailed estimate (CSV)",
        data=csv_data,
        file_name="replication_cost_estimate.csv",
        mime="text/csv",
    )

    st.session_state['calculation_attempted'] = True


if __name__ == "__main__":
    main()
