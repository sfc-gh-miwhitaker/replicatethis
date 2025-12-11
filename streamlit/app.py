import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.exceptions import SnowparkSQLException
import pandas as pd

session = get_active_session()


def load_pricing():
    try:
        df = session.table("SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_CURRENT")
        rows = df.collect()
        if not rows:
            return [], None
        updated_at = max(r.UPDATED_AT for r in rows) if hasattr(rows[0], 'UPDATED_AT') else None
        return rows, updated_at
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


def get_cloud_and_region():
    try:
        region_result = session.sql("SELECT CURRENT_REGION()").collect()
        region_full = region_result[0][0] if region_result else "AWS_US_EAST_1"

        if region_full:
            parts = region_full.split("_", 1)
            if len(parts) >= 2:
                cloud = parts[0]
                region = parts[1].lower().replace("_", "-")
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


def get_current_role():
    try:
        result = session.sql("SELECT CURRENT_ROLE()").collect()
        return result[0][0] if result else None
    except Exception:
        return None


def cost_lookup(pricing_rows, service_type, cloud, region):
    for r in pricing_rows:
        if (
            r.SERVICE_TYPE == service_type
            and r.CLOUD.upper() == cloud.upper()
            and r.REGION.upper() == region.upper()
        ):
            rate = float(r.RATE) if r.RATE is not None else None
            return rate, r.UNIT, False

    for r in pricing_rows:
        if (
            r.SERVICE_TYPE == service_type
            and r.CLOUD.upper() == cloud.upper()
        ):
            rate = float(r.RATE) if r.RATE is not None else None
            return rate, r.UNIT, True

    for r in pricing_rows:
        if r.SERVICE_TYPE == service_type:
            rate = float(r.RATE) if r.RATE is not None else None
            return rate, r.UNIT, True

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


def generate_enhanced_csv(assumptions, costs, projections, price_per_credit):
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
    csv_lines.append(f"Price Per Credit (USD),{price_per_credit:.2f}")
    csv_lines.append("")
    csv_lines.append("# Daily Costs")
    csv_lines.append("Component,Credits,USD,Is Estimate")
    csv_lines.append(
        f"Data Transfer,{costs['transfer_cost']:.2f},"
        f"${costs['transfer_cost'] * price_per_credit:.2f},{costs['transfer_est']}"
    )
    csv_lines.append(
        f"Replication Compute,{costs['compute_cost']:.2f},"
        f"${costs['compute_cost'] * price_per_credit:.2f},{costs['compute_est']}"
    )
    csv_lines.append("")
    csv_lines.append("# Monthly Costs")
    csv_lines.append("Component,Credits,USD")
    csv_lines.append(
        f"Data Transfer (30 days),{projections['monthly_transfer']:.2f},"
        f"${projections['monthly_transfer'] * price_per_credit:.2f}"
    )
    csv_lines.append(
        f"Replication Compute (30 days),{projections['monthly_compute']:.2f},"
        f"${projections['monthly_compute'] * price_per_credit:.2f}"
    )
    csv_lines.append(
        f"Storage,{projections['monthly_storage']:.2f},"
        f"${projections['monthly_storage'] * price_per_credit:.2f}"
    )
    csv_lines.append(
        f"Serverless Maintenance,{projections['monthly_serverless']:.2f},"
        f"${projections['monthly_serverless'] * price_per_credit:.2f}"
    )
    csv_lines.append(
        f"Monthly Total,{projections['monthly_total']:.2f},"
        f"${projections['monthly_total'] * price_per_credit:.2f}"
    )
    csv_lines.append("")
    csv_lines.append("# Annual Projection")
    csv_lines.append(f"Annual Credits,{projections['annual_total']:.2f}")
    csv_lines.append(f"Annual USD,${projections['annual_total'] * price_per_credit:,.2f}")

    return "\n".join(csv_lines)


def admin_panel():
    st.title("Pricing Administration")
    st.info("**Admin access required:** Only SYSADMIN and ACCOUNTADMIN can modify pricing rates.")

    current_role = get_current_role()
    st.write(f"Current role: **{current_role}**")

    if current_role not in ['SYSADMIN', 'ACCOUNTADMIN']:
        st.warning("You must use SYSADMIN or ACCOUNTADMIN role to modify pricing.")
        return

    pricing_rows, updated_at = load_pricing()

    if updated_at:
        st.success(f"Pricing last updated: {updated_at}")

    df = pd.DataFrame([{
        'SERVICE_TYPE': r.SERVICE_TYPE,
        'CLOUD': r.CLOUD,
        'REGION': r.REGION,
        'UNIT': r.UNIT,
        'RATE': float(r.RATE),
        'CURRENCY': r.CURRENCY
    } for r in pricing_rows])

    st.subheader("Current Pricing Rates")
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "RATE": st.column_config.NumberColumn("Rate", min_value=0, format="%.4f"),
        }
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Save Changes", type="primary"):
            try:
                session.sql("TRUNCATE TABLE SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_CURRENT").collect()

                for _, row in edited_df.iterrows():
                    insert_sql = f"""
                        INSERT INTO SNOWFLAKE_EXAMPLE.REPLICATION_CALC.PRICING_CURRENT
                        (SERVICE_TYPE, CLOUD, REGION, UNIT, RATE, CURRENCY)
                        VALUES ('{row['SERVICE_TYPE']}', '{row['CLOUD']}', '{row['REGION']}',
                                '{row['UNIT']}', {row['RATE']}, '{row['CURRENCY']}')
                    """
                    session.sql(insert_sql).collect()

                st.success(f"✅ Pricing updated successfully! {len(edited_df)} rates saved.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update pricing: {str(e)}")

    with col2:
        if st.button("Reset to Defaults"):
            st.warning("This will reset all pricing to default values. Confirm in SQL worksheet.")


def main():
    st.set_page_config(page_title="Replication Cost Calculator", layout="wide")

    pages = {
        "Cost Calculator": "calculator",
        "Admin: Manage Pricing": "admin"
    }

    st.sidebar.title("Navigation")
    selected_page = st.sidebar.radio("Go to", list(pages.keys()))

    if pages[selected_page] == "admin":
        admin_panel()
        return

    st.title("Replication / DR Cost Calculator (Business Critical)")

    st.info(
        "**Disclaimer:** This calculator provides cost estimates for budgeting purposes only. "
        "Actual costs may vary based on usage patterns, data compression, and other factors. "
        "Always monitor actual consumption via Snowflake's usage views."
    )

    st.caption("Business Critical pricing; rates managed by admins via Pricing Administration page.")

    st.sidebar.header("💰 Pricing Configuration")
    price_per_credit = st.sidebar.number_input(
        "Price per credit (USD)",
        min_value=0.50,
        max_value=10.00,
        value=4.00,
        step=0.10,
        help="Enter your contract price per credit. Standard list price is ~$2-4 depending on edition and region."
    )
    st.sidebar.caption(f"All USD costs calculated at ${price_per_credit:.2f}/credit")

    pricing_rows, updated_at = load_pricing()

    if not pricing_rows:
        st.error("No pricing data found. Please contact an administrator to configure pricing rates.")
        return

    if updated_at:
        st.caption(f"📊 Pricing data last updated: {updated_at}")

    db_rows = load_db_metadata()
    db_options = {r.DATABASE_NAME: r for r in db_rows}

    selected_dbs = st.multiselect("Select databases", sorted(db_options.keys()))

    if not selected_dbs and st.session_state.get('calculation_attempted'):
        st.warning("Please select at least one database to calculate costs.")

    source_cloud, source_region = get_cloud_and_region()

    st.subheader("Destination Selection")

    available_clouds = sorted({r.CLOUD for r in pricing_rows})
    dest_cloud = st.selectbox(
        "Destination cloud provider",
        available_clouds,
        index=available_clouds.index(source_cloud) if source_cloud in available_clouds else 0,
        help="Select the destination cloud provider for replication"
    )

    cloud_regions = sorted({r.REGION for r in pricing_rows if r.CLOUD == dest_cloud})
    dest_region = st.selectbox(
        "Destination region",
        cloud_regions,
        index=0 if cloud_regions else None,
        help=f"Select the destination region in {dest_cloud}"
    ) if cloud_regions else None

    st.subheader("Replication Parameters")
    daily_change_pct = st.slider("Daily change rate (%)", 0.0, 20.0, 5.0, 0.5,
                                   help="Percentage of total data that changes each day")
    refresh_per_day = st.slider("Refreshes per day", 0.0, 24.0, 1.0, 0.5,
                                  help="Number of replication refresh operations per day")

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

    st.subheader("Cost Summary")

    col1, col2 = st.columns(2)
    with col1:
        st.write("**Source (detected):**")
        st.write(f"Cloud: {source_cloud}")
        st.write(f"Region: {source_region}")
        if transfer_rate:
            st.caption(f"Transfer rate: {transfer_rate} credits/TB")
        else:
            st.caption("⚠️ No exact rate found - using fallback")
    with col2:
        st.write("**Destination:**")
        st.write(f"Cloud: {dest_cloud or '-'}")
        st.write(f"Region: {dest_region or '-'}")

    st.write(f"**Selected DB size:** {total_size_tb:.6f} TB ({total_size_tb * 1024:.3f} GB)")
    st.write(f"**Daily change:** {daily_change_pct}% = {daily_transfer_tb:.6f} TB/day")
    st.write(f"**Refreshes/day:** {refresh_per_day}")

    if total_size_tb > 0 and total_size_tb < 0.01:
        st.warning(
            f"⚠️ Selected databases are very small ({total_size_tb * 1024 * 1024:.1f} MB). "
            "Costs may appear as $0.00. This is expected for small datasets."
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
        st.subheader("Daily Costs")
        st.table(
            [
                {
                    "Component": "Data Transfer",
                    "Credits": f"{transfer_cost:.4f}",
                    "USD": f"${transfer_cost * price_per_credit:.4f}",
                    "Estimate": transfer_est
                },
                {
                    "Component": "Replication Compute",
                    "Credits": f"{compute_cost:.4f}",
                    "USD": f"${compute_cost * price_per_credit:.4f}",
                    "Estimate": compute_est
                },
            ]
        )

    with col2:
        st.subheader("Monthly Costs")
        st.table(
            [
                {
                    "Component": "Transfer (30d)",
                    "Credits": f"{projections['monthly_transfer']:.4f}",
                    "USD": f"${projections['monthly_transfer'] * price_per_credit:.4f}"
                },
                {
                    "Component": "Compute (30d)",
                    "Credits": f"{projections['monthly_compute']:.4f}",
                    "USD": f"${projections['monthly_compute'] * price_per_credit:.4f}"
                },
                {
                    "Component": "Storage",
                    "Credits": f"{storage_cost:.4f}",
                    "USD": f"${storage_cost * price_per_credit:.4f}",
                    "Estimate": storage_est
                },
                {
                    "Component": "Serverless Maint",
                    "Credits": f"{serverless_cost:.4f}",
                    "USD": f"${serverless_cost * price_per_credit:.4f}",
                    "Estimate": serverless_est
                },
            ]
        )

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Monthly Total", f"{projections['monthly_total']:.2f} credits")
        st.metric("Annual Credits", f"{projections['annual_total']:.2f} credits")
    with col_m2:
        monthly_usd = projections['monthly_total'] * price_per_credit
        annual_usd = projections['annual_total'] * price_per_credit
        st.metric("Monthly Total (USD)", f"${monthly_usd:,.2f}")
        st.metric("Annual Projection (USD)", f"${annual_usd:,.2f}")

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
    st.write("Values marked as estimates rely on fallback rates when exact region match is unavailable.")

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

    csv_data = generate_enhanced_csv(assumptions, costs, projections, price_per_credit)

    st.download_button(
        label="Download detailed estimate (CSV)",
        data=csv_data,
        file_name="replication_cost_estimate.csv",
        mime="text/csv",
    )

    st.session_state['calculation_attempted'] = True


if __name__ == "__main__":
    main()
