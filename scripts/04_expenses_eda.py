import os

import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"])


# Load expense data from PostgreSQL

expenses_enriched = pd.read_sql("expenses_enriched", engine)


# Calculate overall expenses per category

total_expenses_per_category = (
    expenses_enriched
    .groupby("expense_type")["total_spent_eur"]
    .sum()
)

print(
    "Total expenses per category:"
    f"\n{total_expenses_per_category.round(2)}"
)


# Calculate annual expenses per category

expenses_enriched["year"] = expenses_enriched["expense_date"].dt.year

annual_expenses_per_category = (
    expenses_enriched
    .groupby(["year", "expense_type"])["total_spent_eur"]
    .sum()
)

print(
    "\nAnnual expenses per category:"
    f"\n{annual_expenses_per_category.round(2)}"
)

# Calculate expenses per category for 2025

expenses_2025 = expenses_enriched.loc[
    expenses_enriched["expense_date"].dt.year == 2025
]

expenses_by_category_2025 = (
    expenses_2025
    .groupby("expense_type")["total_spent_eur"]
    .sum()
)


# Plot overall expenses by category

total_expenses_per_category_sorted = (
    total_expenses_per_category
    .sort_values()
)

bars = plt.barh(
    total_expenses_per_category_sorted.index,
    total_expenses_per_category_sorted,
    color="#0B4653",
)

labels = [
    f"€{value:,.0f} ({value / total_expenses_per_category_sorted.sum() * 100:.1f}%)"
    for value in total_expenses_per_category_sorted
]

plt.bar_label(
    bars,
    labels=labels,
    padding=3,
    color="#0B4653",
)

plt.gca().invert_yaxis()
plt.margins(x=0.15)
plt.xlabel("Total Expenses (EUR)")
plt.ylabel("Expense Type")
plt.title("Total Expenses by Category")

plt.show()


# Plot expenses by category for 2025

expenses_by_category_2025_sorted = (
    expenses_by_category_2025
    .sort_values()
)

bars = plt.barh(
    expenses_by_category_2025_sorted.index,
    expenses_by_category_2025_sorted,
    color="#0B4653",
)

labels = [
    f"€{value:,.0f} ({value / expenses_by_category_2025_sorted.sum() * 100:.1f}%)"
    for value in expenses_by_category_2025_sorted
]

plt.bar_label(
    bars,
    labels=labels,
    padding=3,
    color="#0B4653",
)

plt.gca().invert_yaxis()
plt.margins(x=0.15)
plt.xlabel("Total Expenses (EUR)")
plt.ylabel("Expense Type")
plt.title("Expenses by Category 2025")

plt.show()