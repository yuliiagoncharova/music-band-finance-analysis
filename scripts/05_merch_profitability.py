import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"])


# Load merch data from PostgreSQL

merchandise_enriched = (
    pd.read_sql("merchandise_enriched", engine)
)

merch_production_cost_processed = (
    pd.read_sql("merch_production_cost_processed", engine)
)


# Calculate total revenue by merch type

merch_revenue_per_type = (
    merchandise_enriched
    .groupby(
        "item_type",
        as_index=False
    )["purchase_total_eur"]
    .sum()
)


# Calculate revenue by year and merch type

merchandise_enriched["year"] = merchandise_enriched["purchase_date"].dt.year

merch_revenue_per_type_by_year = (
    merchandise_enriched
    .groupby(
        ["item_type", "year"], as_index=False
    )["purchase_total_eur"]
    .sum()
)


# Calculate quantity sold by year and merch type

merch_quantity_by_year_and_type = (
    merchandise_enriched
    .groupby(
        ["item_type", "year"], as_index=False
    )["quantity"]
    .sum(min_count=1)
)


# Add average production cost per unit by year and merch type

merch_cost_by_year_and_type = (
    merch_quantity_by_year_and_type
    .merge(
        merch_production_cost_processed,
        how="left",
        left_on=["item_type", "year"],
        right_on=["item_type", "cost_year"]
    )
)


# Calculate total production cost by year and merch type

merch_cost_by_year_and_type["production_cost_eur"] = (
    merch_cost_by_year_and_type["quantity"]
    * merch_cost_by_year_and_type["avg_production_cost_eur"]
)


# Calculate total production cost over the full period by merch type

total_production_cost_by_type = (
    merch_cost_by_year_and_type
    .groupby(
        "item_type",
        as_index=False,
    )["production_cost_eur"]
    .sum(min_count=1)
)


# Combine revenue and production cost by merch type

merch_profitability_by_type = (
    merch_revenue_per_type
    .merge(
        total_production_cost_by_type,
        how="left",
        on="item_type",
        validate="one_to_one"
    )
)


# Calculate gross profit by merch type

merch_profitability_by_type["gross_profit_eur"] = (
    merch_profitability_by_type["purchase_total_eur"]
    - merch_profitability_by_type["production_cost_eur"]
)


# Calculate gross margin by merch type

merch_profitability_by_type["gross_margin_pct"] = (
    merch_profitability_by_type["gross_profit_eur"]
    / merch_profitability_by_type["purchase_total_eur"]
    * 100
)


# Calculate share of total gross profit by merch type

merch_profitability_by_type["gross_profit_share_pct"] = (
    merch_profitability_by_type["gross_profit_eur"]
    / merch_profitability_by_type["gross_profit_eur"].sum()
    * 100
)


merch_profitability_by_type = (
    merch_profitability_by_type
    .sort_values(
        "gross_margin_pct",
        ascending=True
    )
)

# Visualize gross margin by merch type

bars = plt.barh(
    merch_profitability_by_type["item_type"],
    merch_profitability_by_type["gross_margin_pct"],
    color="#0B4653"
)

plt.bar_label(
    bars,
    fmt="%.1f%%",
    padding=3,
    color="#0B4653"
)

plt.gca().invert_yaxis()
plt.xlabel("Gross Margin (%)")
plt.ylabel("Merch Type")
plt.title("Gross Margin by Merch Type")

plt.show()


# Visualize gross profit by merch type

merch_profitability_by_profit = (
    merch_profitability_by_type
    .sort_values(
        "gross_profit_eur",
        ascending=True
    )
)

bars = plt.barh(
    merch_profitability_by_profit["item_type"],
    merch_profitability_by_profit["gross_profit_eur"],
    color="#0B4653"
)

labels = [
    f"€{profit:.0f} ({share:.1f}%)"
    for profit, share in zip(
        merch_profitability_by_profit["gross_profit_eur"],
        merch_profitability_by_profit["gross_profit_share_pct"]
    )
]

plt.bar_label(
    bars,
    labels=labels,
    padding=3,
    color="#0B4653"
)

plt.gca().invert_yaxis()
plt.margins(x=0.15)
plt.xlabel("Gross Profit (€)")
plt.ylabel("Merch Type")
plt.title("Gross Profit by Merch Type")

plt.show()