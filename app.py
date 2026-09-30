import streamlit as st
import pandas as pd
import numpy as np
import os
import re
import io

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Nassau Candy Factory Optimization",
    page_icon="🏭",
    layout="wide"
)

# ============================================================
# TITLE
# ============================================================

st.title("🏭 Nassau Candy Factory Reallocation & Shipping Optimization")

st.subheader("Decision Intelligence Dashboard")

st.write(
    "Analyze shipping performance, factory utilization, profitability, "
    "and product-factory reallocation opportunities."
)

# ============================================================
# FILE LOCATION
# ============================================================

DATA_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data"
)

DATA_FILE = os.path.join(
    DATA_FOLDER,
    "nassau_candy_data.xlsx"
)

# ============================================================
# FUNCTION 1: READ NORMAL EXCEL FILE
# ============================================================

def read_excel_file(file_path):

    try:
        df = pd.read_excel(
            file_path,
            engine="openpyxl"
        )

        return df

    except Exception:
        return None


# ============================================================
# FUNCTION 2: READ YOUR CURRENT TEXT-BASED DATA
# ============================================================

def read_text_based_data(file_path):

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as file:

            text = file.read()

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if len(lines) < 2:
            return None

        rows = []

        # ----------------------------------------------------
        # Expected structure:
        #
        # Order_ID
        # Product_Name
        # Factory
        # Customer_Region
        # Product_Weight_kg
        # Shipping_Distance_km
        # Lead_Time_days
        # Shipping_Cost
        # Product_Price
        # Profit
        # Demand
        # Factory_Capacity
        # ----------------------------------------------------

        for line in lines[1:]:

            # Ignore accidental non-data lines
            if not line.startswith("ORD"):
                continue

            parts = line.split()

            if len(parts) < 12:
                continue

            order_id = parts[0]

            # Product name contains two words
            product_name = parts[1] + " " + parts[2]

            factory = parts[3]

            customer_region = parts[4]

            product_weight = float(parts[5])

            shipping_distance = float(parts[6])

            lead_time = float(parts[7])

            shipping_cost = float(parts[8])

            product_price = float(parts[9])

            profit = float(parts[10])

            demand = float(parts[11])

            # Factory capacity is not available in some
            # recovered versions of the file.
            # We calculate it later if necessary.

            rows.append([
                order_id,
                product_name,
                factory,
                customer_region,
                product_weight,
                shipping_distance,
                lead_time,
                shipping_cost,
                product_price,
                profit,
                demand
            ])

        if not rows:
            return None

        columns = [
            "Order_ID",
            "Product_Name",
            "Factory",
            "Customer_Region",
            "Product_Weight_kg",
            "Shipping_Distance_km",
            "Lead_Time_days",
            "Shipping_Cost",
            "Product_Price",
            "Profit",
            "Demand"
        ]

        df = pd.DataFrame(
            rows,
            columns=columns
        )

        return df

    except Exception as e:

        st.error(
            f"Error while reading recovered data: {e}"
        )

        return None


# ============================================================
# FUNCTION 3: LOAD DATA
# ============================================================

def load_data():

    # First try proper Excel
    if os.path.exists(DATA_FILE):

        df = read_excel_file(DATA_FILE)

        if df is not None and not df.empty:
            return df

        # If Excel fails, try the recovered text file
        df = read_text_based_data(DATA_FILE)

        if df is not None and not df.empty:
            return df

    return None


# ============================================================
# LOAD DATA
# ============================================================

df = load_data()


# ============================================================
# IF DATA CANNOT BE LOADED
# ============================================================

if df is None:

    st.error("❌ Unable to load the Nassau Candy dataset.")

    st.info(
        "The current data file appears to be a recovered text-based "
        "file rather than a standard Excel workbook."
    )

    st.write("Expected file:")

    st.code(DATA_FILE)

    st.stop()


# ============================================================
# DATA CLEANING
# ============================================================

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)

# Convert numeric columns

numeric_columns = [
    "Product_Weight_kg",
    "Shipping_Distance_km",
    "Lead_Time_days",
    "Shipping_Cost",
    "Product_Price",
    "Profit",
    "Demand"
]

for column in numeric_columns:

    if column in df.columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


# ============================================================
# CALCULATED METRICS
# ============================================================

# Revenue

if "Product_Price" in df.columns and "Demand" in df.columns:

    df["Revenue"] = (
        df["Product_Price"] *
        df["Demand"]
    )

else:

    df["Revenue"] = 0


# Total shipping cost

if "Shipping_Cost" in df.columns and "Demand" in df.columns:

    df["Total_Shipping_Cost"] = (
        df["Shipping_Cost"] *
        df["Demand"]
    )

else:

    df["Total_Shipping_Cost"] = 0


# Total profit

if "Profit" in df.columns and "Demand" in df.columns:

    df["Total_Profit"] = (
        df["Profit"] *
        df["Demand"]
    )

else:

    df["Total_Profit"] = 0


# Profit margin

df["Profit_Margin_%"] = np.where(
    df["Product_Price"] != 0,
    (df["Profit"] / df["Product_Price"]) * 100,
    0
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Dashboard Filters")

# Factory filter

factories = sorted(
    df["Factory"].dropna().unique().tolist()
)

selected_factories = st.sidebar.multiselect(
    "Select Factory",
    factories,
    default=factories
)


# Region filter

regions = sorted(
    df["Customer_Region"].dropna().unique().tolist()
)

selected_regions = st.sidebar.multiselect(
    "Select Customer Region",
    regions,
    default=regions
)


# Product filter

products = sorted(
    df["Product_Name"].dropna().unique().tolist()
)

selected_products = st.sidebar.multiselect(
    "Select Product",
    products,
    default=products
)


# ============================================================
# FILTER DATA
# ============================================================

filtered_df = df[
    df["Factory"].isin(selected_factories)
    &
    df["Customer_Region"].isin(selected_regions)
    &
    df["Product_Name"].isin(selected_products)
].copy()


# ============================================================
# MAIN DASHBOARD
# ============================================================

st.markdown("---")

st.header("📊 Key Performance Indicators")


# KPI calculations

total_orders = len(filtered_df)

total_demand = filtered_df["Demand"].sum()

average_distance = filtered_df[
    "Shipping_Distance_km"
].mean()

average_lead_time = filtered_df[
    "Lead_Time_days"
].mean()

total_shipping_cost = filtered_df[
    "Total_Shipping_Cost"
].sum()

total_profit = filtered_df[
    "Total_Profit"
].sum()


# ============================================================
# KPI DISPLAY
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "📦 Total Orders",
        f"{total_orders:,}"
    )

with col2:

    st.metric(
        "📈 Total Demand",
        f"{total_demand:,.0f}"
    )

with col3:

    st.metric(
        "🚚 Avg Distance",
        f"{average_distance:,.1f} km"
    )

with col4:

    st.metric(
        "⏱ Avg Lead Time",
        f"{average_lead_time:,.1f} days"
    )


col5, col6, col7 = st.columns(3)

with col5:

    st.metric(
        "💰 Shipping Cost",
        f"${total_shipping_cost:,.0f}"
    )

with col6:

    st.metric(
        "💵 Total Profit",
        f"${total_profit:,.0f}"
    )

with col7:

    avg_margin = filtered_df[
        "Profit_Margin_%"
    ].mean()

    st.metric(
        "📊 Avg Profit Margin",
        f"{avg_margin:,.1f}%"
    )


# ============================================================
# FACTORY PERFORMANCE
# ============================================================

st.markdown("---")

st.header("🏭 Factory Performance")

factory_summary = (
    filtered_df
    .groupby("Factory")
    .agg(
        Orders=("Order_ID", "count"),
        Demand=("Demand", "sum"),
        Avg_Distance=("Shipping_Distance_km", "mean"),
        Avg_Lead_Time=("Lead_Time_days", "mean"),
        Shipping_Cost=("Total_Shipping_Cost", "sum"),
        Profit=("Total_Profit", "sum")
    )
    .reset_index()
)


st.dataframe(
    factory_summary,
    use_container_width=True
)


# ============================================================
# FACTORY CHARTS
# ============================================================

chart_col1, chart_col2 = st.columns(2)


with chart_col1:

    st.subheader("🚚 Average Shipping Distance")

    distance_chart = factory_summary.set_index(
        "Factory"
    )["Avg_Distance"]

    st.bar_chart(distance_chart)


with chart_col2:

    st.subheader("💰 Factory Profit")

    profit_chart = factory_summary.set_index(
        "Factory"
    )["Profit"]

    st.bar_chart(profit_chart)


# ============================================================
# PRODUCT PERFORMANCE
# ============================================================

st.markdown("---")

st.header("🍬 Product Performance")

product_summary = (
    filtered_df
    .groupby("Product_Name")
    .agg(
        Orders=("Order_ID", "count"),
        Demand=("Demand", "sum"),
        Avg_Distance=("Shipping_Distance_km", "mean"),
        Avg_Lead_Time=("Lead_Time_days", "mean"),
        Shipping_Cost=("Total_Shipping_Cost", "sum"),
        Profit=("Total_Profit", "sum")
    )
    .reset_index()
)


st.dataframe(
    product_summary,
    use_container_width=True
)


# ============================================================
# PRODUCT PROFIT CHART
# ============================================================

st.subheader("💵 Profit by Product")

product_profit_chart = (
    product_summary
    .set_index("Product_Name")["Profit"]
)

st.bar_chart(product_profit_chart)


# ============================================================
# REGION PERFORMANCE
# ============================================================

st.markdown("---")

st.header("🌎 Customer Region Analysis")

region_summary = (
    filtered_df
    .groupby("Customer_Region")
    .agg(
        Orders=("Order_ID", "count"),
        Demand=("Demand", "sum"),
        Avg_Distance=("Shipping_Distance_km", "mean"),
        Avg_Lead_Time=("Lead_Time_days", "mean"),
        Shipping_Cost=("Total_Shipping_Cost", "sum"),
        Profit=("Total_Profit", "sum")
    )
    .reset_index()
)


st.dataframe(
    region_summary,
    use_container_width=True
)


# ============================================================
# SHIPPING ANALYSIS
# ============================================================

st.markdown("---")

st.header("🚚 Shipping Analysis")

shipping_col1, shipping_col2 = st.columns(2)


with shipping_col1:

    st.subheader("Shipping Distance by Region")

    region_distance = (
        region_summary
        .set_index("Customer_Region")
        ["Avg_Distance"]
    )

    st.bar_chart(region_distance)


with shipping_col2:

    st.subheader("Lead Time by Region")

    region_lead_time = (
        region_summary
        .set_index("Customer_Region")
        ["Avg_Lead_Time"]
    )

    st.bar_chart(region_lead_time)


# ============================================================
# HIGH SHIPPING COST ORDERS
# ============================================================

st.markdown("---")

st.header("⚠️ High Shipping Cost Orders")

high_cost = filtered_df.sort_values(
    "Shipping_Cost",
    ascending=False
).head(10)


st.dataframe(
    high_cost[
        [
            "Order_ID",
            "Product_Name",
            "Factory",
            "Customer_Region",
            "Shipping_Distance_km",
            "Lead_Time_days",
            "Shipping_Cost"
        ]
    ],
    use_container_width=True
)


# ============================================================
# REALLOCATION ANALYSIS
# ============================================================

st.markdown("---")

st.header("🔄 Factory Reallocation Recommendations")

st.write(
    "The system compares the current factory assignment with "
    "alternative factories using shipping distance and shipping cost."
)


# Factory coordinates

factory_coordinates = {

    "Factory_A": (40.7128, -74.0060),

    "Factory_B": (41.8781, -87.6298),

    "Factory_C": (34.0522, -118.2437)
}


# Region coordinates

region_coordinates = {

    "East": (40.7128, -74.0060),

    "West": (34.0522, -118.2437),

    "South": (29.7604, -95.3698),

    "North": (41.8781, -87.6298)
}


def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371

    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)

    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        np.sin(dlat / 2) ** 2
        +
        np.cos(lat1)
        *
        np.cos(lat2)
        *
        np.sin(dlon / 2) ** 2
    )

    c = 2 * np.arcsin(
        np.sqrt(a)
    )

    return R * c


# ============================================================
# CREATE REALLOCATION TABLE
# ============================================================

recommendations = []


for _, row in filtered_df.iterrows():

    current_factory = row["Factory"]

    region = row["Customer_Region"]

    if (
        current_factory not in factory_coordinates
        or region not in region_coordinates
    ):
        continue

    region_lat, region_lon = region_coordinates[
        region
    ]

    current_lat, current_lon = factory_coordinates[
        current_factory
    ]

    current_distance = calculate_distance(
        current_lat,
        current_lon,
        region_lat,
        region_lon
    )

    best_factory = current_factory

    best_distance = current_distance

    for factory, coordinates in factory_coordinates.items():

        factory_lat, factory_lon = coordinates

        distance = calculate_distance(
            factory_lat,
            factory_lon,
            region_lat,
            region_lon
        )

        if distance < best_distance:

            best_distance = distance

            best_factory = factory


    distance_saving = (
        current_distance - best_distance
    )


    if best_factory != current_factory:

        recommendation = "Consider Reallocation"

    else:

        recommendation = "Keep Current Factory"


    recommendations.append({

        "Order_ID": row["Order_ID"],

        "Product_Name": row["Product_Name"],

        "Current_Factory": current_factory,

        "Recommended_Factory": best_factory,

        "Customer_Region": region,

        "Current_Distance_km": round(
            current_distance,
            2
        ),

        "Recommended_Distance_km": round(
            best_distance,
            2
        ),

        "Distance_Saving_km": round(
            distance_saving,
            2
        ),

        "Recommendation": recommendation

    })


recommendation_df = pd.DataFrame(
    recommendations
)


# ============================================================
# DISPLAY RECOMMENDATIONS
# ============================================================

if not recommendation_df.empty:

    st.dataframe(
        recommendation_df,
        use_container_width=True
    )

else:

    st.info(
        "No reallocation recommendation could be generated "
        "for the selected filters."
    )


# ============================================================
# TOP REALLOCATION OPPORTUNITIES
# ============================================================

if not recommendation_df.empty:

    st.subheader(
        "🎯 Top Reallocation Opportunities"
    )

    top_reallocation = (
        recommendation_df[
            recommendation_df[
                "Distance_Saving_km"
            ] > 0
        ]
        .sort_values(
            "Distance_Saving_km",
            ascending=False
        )
        .head(10)
    )

    if not top_reallocation.empty:

        st.dataframe(
            top_reallocation,
            use_container_width=True
        )

    else:

        st.success(
            "No significant distance-saving "
            "reallocation opportunities found."
        )


# ============================================================
# OPTIMIZATION SUMMARY
# ============================================================

st.markdown("---")

st.header("📌 Optimization Summary")


if not recommendation_df.empty:

    total_saving = (
        recommendation_df[
            "Distance_Saving_km"
        ]
        .clip(lower=0)
        .sum()
    )

    possible_reallocations = (
        recommendation_df[
            "Recommendation"
        ]
        .eq("Consider Reallocation")
        .sum()
    )

else:

    total_saving = 0

    possible_reallocations = 0


summary_col1, summary_col2, summary_col3 = st.columns(3)


with summary_col1:

    st.metric(
        "Potential Distance Saving",
        f"{total_saving:,.1f} km"
    )


with summary_col2:

    st.metric(
        "Potential Reallocations",
        f"{possible_reallocations}"
    )


with summary_col3:

    st.metric(
        "Factories Analyzed",
        f"{len(selected_factories)}"
    )


# ============================================================
# DOWNLOAD FILTERED DATA
# ============================================================

st.markdown("---")

st.header("📥 Export Results")

csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇️ Download Filtered Dataset",
    data=csv_data,
    file_name="nassau_candy_filtered_data.csv",
    mime="text/csv"
)


if not recommendation_df.empty:

    recommendation_csv = (
        recommendation_df
        .to_csv(index=False)
        .encode("utf-8")
    )

    st.download_button(
        label="⬇️ Download Reallocation Recommendations",
        data=recommendation_csv,
        file_name="factory_reallocation_recommendations.csv",
        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "Nassau Candy Factory Reallocation & Shipping Optimization "
    "Decision Intelligence Dashboard"
)