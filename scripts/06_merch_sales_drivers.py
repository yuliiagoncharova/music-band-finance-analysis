import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"])


# Load data from Postgres

merchandise_enriched = (
    pd.read_sql("merchandise_enriched", engine)
)

live_shows_processed = (
    pd.read_sql("live_shows_processed", engine)
)

releases_processed = (
    pd.read_sql("releases_processed", engine)
)

merch_drops_processed = (
    pd.read_sql("merch_drops_processed", engine)
)


# Add month column and calculate merch revenue per month

merchandise_enriched["month"] = (
    merchandise_enriched["purchase_date"]
    .dt.to_period("M")
)

merch_revenue_per_month = (
    merchandise_enriched
    .groupby(
        "month",
        as_index=False,
    )["purchase_total_eur"]
    .sum()
    .rename(
        columns={
            "purchase_total_eur": "merch_revenue_eur"
        }
    )
)


# Create a complete monthly range

all_months = pd.DataFrame(
    {
        "month": pd.period_range(
            start=merchandise_enriched["month"].min(),
            end=merchandise_enriched["month"].max(),
            freq="M",
        )
    }
)


# Add months with no recorded merch sales

merch_revenue_per_month = (
    all_months
    .merge(
        merch_revenue_per_month,
        how="left",
        on="month",
        validate="one_to_one",
    )
)

merch_revenue_per_month["merch_revenue_eur"] = (
    merch_revenue_per_month["merch_revenue_eur"]
    .fillna(0)
)


# Add month columns to live shows, releases, and merch drops

live_shows_processed["show_month"] = (
    live_shows_processed["show_date"]
    .dt.to_period("M")
)

releases_processed["release_month"] = (
    releases_processed["release_date"]
    .dt.to_period("M")
)

merch_drops_processed["drop_month"] = (
    merch_drops_processed["drop_date"]
    .dt.to_period("M")
)


# Calculate live show count per month

live_shows_per_month = (
    live_shows_processed
    .groupby(
        "show_month",
        as_index=False,
    )
    .agg(
        show_count=("show_date", "count")
    )
    .rename(
        columns={
            "show_month": "month"
        }
    )
)


# Calculate release count per month

releases_per_month = (
    releases_processed
    .groupby(
        "release_month",
        as_index=False,
    )
    .agg(
        release_count=("release_date", "count")
    )
    .rename(
        columns={
            "release_month": "month"
        }
    )
)


# Calculate merch drop and new design counts per month

merch_drops_per_month = (
    merch_drops_processed
    .groupby(
        "drop_month",
        as_index=False,
    )
    .agg(
        drop_count=("drop_date", "nunique"),
        new_designs_count=("new_designs_count", "sum"),
    )
    .rename(
        columns={
            "drop_month": "month"
        }
    )
)


# Combine merch revenue with monthly factors

merch_sales_drivers = (
    merch_revenue_per_month
    .merge(
        live_shows_per_month,
        how="left",
        on="month",
        validate="one_to_one",
    )
    .merge(
        releases_per_month,
        how="left",
        on="month",
        validate="one_to_one",
    )
    .merge(
        merch_drops_per_month,
        how="left",
        on="month",
        validate="one_to_one",
    )
)


# Replace missing event counts with 0

factor_columns = [
    "show_count",
    "release_count",
    "drop_count",
    "new_designs_count",
]

merch_sales_drivers[factor_columns] = (
    merch_sales_drivers[factor_columns]
    .fillna(0)
)


# Compare merch revenue in months with and without live shows

merch_sales_drivers["has_live_show"] = (
    merch_sales_drivers["show_count"] > 0
)

merch_revenue_by_show_presence = (
    merch_sales_drivers
    .groupby("has_live_show")
    .agg(
        month_count=("month", "count"),
        median_merch_revenue_eur=("merch_revenue_eur", "median")
    )
    .rename(
        index={
            False: "no_live_shows",
            True: "live_shows",
        }
    )
)

print(
    "\nMerch revenue in months with vs without live shows:"
    f"\n{merch_revenue_by_show_presence.round(2)}"
)

merch_sales_drivers = (
    merch_sales_drivers
    .drop(columns="has_live_show")
)


# Calculate Pearson correlation matrix

correlation_matrix_pearson = (
    merch_sales_drivers.corr(numeric_only=True)
)

correlation_cmap = LinearSegmentedColormap.from_list(
    "correlation",
    [
        "#0B4653",
        "#FFFFFF",
        "#FF6B4A",
    ],
)

sns.heatmap(
    correlation_matrix_pearson,
    cmap=correlation_cmap,
    vmin=-1,
    vmax=1,
    center=0,
    annot=True,
    fmt=".2f"
)

plt.title("Pearson Correlation")

plt.show()


# Calculate Pearson correlation matrix for months without live shows 

merch_sales_drivers_no_shows = (
    merch_sales_drivers[
        merch_sales_drivers["show_count"] == 0
    ]
)

correlation_matrix_no_shows_pearson = (
    merch_sales_drivers_no_shows.corr(numeric_only=True)
)

sns.heatmap(
    correlation_matrix_no_shows_pearson,
    cmap=correlation_cmap,
    vmin=-1,
    vmax=1,
    center=0,
    annot=True,
    fmt=".2f"
)

plt.title("Pearson Correlation (Only Months Without Live Shows)")

plt.show()


# Calculate Spearman correlation matrix

correlation_matrix_spearman = (
    merch_sales_drivers.corr(
        numeric_only=True,
        method="spearman"
        )
)

sns.heatmap(
    correlation_matrix_spearman,
    cmap=correlation_cmap,
    vmin=-1,
    vmax=1,
    center=0,
    annot=True,
    fmt=".2f"
)

plt.title("Spearman Correlation")

plt.show()


# Calculate Spearman correlation matrix for months without live shows

correlation_matrix_no_shows_spearman = (
    merch_sales_drivers_no_shows.corr(
        numeric_only=True,
        method="spearman"
        )
)

sns.heatmap(
    correlation_matrix_no_shows_spearman,
    cmap=correlation_cmap,
    vmin=-1,
    vmax=1,
    center=0,
    annot=True,
    fmt=".2f"
)

plt.title("Spearman Correlation (Only Months Without Live Shows)")

plt.show()


# Calculate and visualize correlation between live shows and merch revenue

sns.regplot(
    data=merch_sales_drivers,
    x="show_count",
    y="merch_revenue_eur",
    color="#0B4653",
)

plt.title("Live Shows vs Monthly Merchandise Revenue")
plt.xlabel("Number of Live Shows")
plt.ylabel("Monthly Merchandise Revenue (EUR)")

plt.show()

correlation = (
    merch_sales_drivers[
        ["show_count", "merch_revenue_eur"]
    ]
    .corr()
    .iloc[0, 1]
)

print(correlation)