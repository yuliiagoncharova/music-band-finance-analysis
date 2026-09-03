import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"])


# Load income data from Postgres

profit_per_month_processed = pd.read_sql("profit_per_month_processed", engine)


# Calculate overall financial results

total_gross_revenue = (
    profit_per_month_processed["gross_revenue_eur"]
    .sum()
)
total_gross_profit = (
    profit_per_month_processed["gross_profit_eur"]
    .sum()
)
overall_gross_margin = (
    total_gross_profit / total_gross_revenue * 100
)

print(f"Total gross revenue, EUR: {total_gross_revenue.round(2)}")
print(f"Total gross profit, EUR: {total_gross_profit.round(2)}")
print(f"Overall gross margin, %: {overall_gross_margin.round(2)}")


# Calculate descriptive statistics for monthly revenue, profit, and margin

monthly_gross_revenue_stats = (
    profit_per_month_processed["gross_revenue_eur"]
    .describe()
)
monthly_gross_profit_stats = (
    profit_per_month_processed["gross_profit_eur"]
    .describe()
)
monthly_gross_margin_stats = (
    profit_per_month_processed["gross_margin_pct"]
    .describe()
)

print(
    "\nMonthly gross revenue statistics:"
    f"\n{monthly_gross_revenue_stats.round(2)}"
)
print(
    "\nMonthly gross profit statistics:"
    f"\n{monthly_gross_profit_stats.round(2)}"
)
print(
    "\nMonthly gross margin statistics:"
    f"\n{monthly_gross_margin_stats.round(2)}"
)


# Calculate annual financial results

profit_per_month_processed["year"] = (
    profit_per_month_processed["report_month"].dt.year
)

financial_data_by_year = (
    profit_per_month_processed
    .groupby("year")
)

annual_gross_revenue = (
    financial_data_by_year["gross_revenue_eur"]
    .sum()
)
annual_gross_profit = (
    financial_data_by_year["gross_profit_eur"]
    .sum()
)
annual_gross_margin = (
    annual_gross_profit / annual_gross_revenue * 100
)

print(
    "\nAnnual gross revenue, EUR:"
    f"\n{annual_gross_revenue.round(2)}"
)
print(
    "\nAnnual gross profit, EUR:"
    f"\n{annual_gross_profit.round(2)}"
)
print(
    "\nAnnual gross margin, %:"
    f"\n{annual_gross_margin.round(2)}"
)


# Calculate annual descriptive statistics for monthly revenue, profit, and margin

annual_monthly_gross_revenue_stats = (
    financial_data_by_year["gross_revenue_eur"]
    .describe()
)
annual_monthly_gross_profit_stats = (
    financial_data_by_year["gross_profit_eur"]
    .describe()
)
annual_monthly_gross_margin_stats = (
    financial_data_by_year["gross_margin_pct"]
    .describe()
)

print(
    "\nMonthly gross revenue statistics by year:"
    f"\n{annual_monthly_gross_revenue_stats.round(2)}"
)
print(
    "\nMonthly gross profit statistics by year:"
    f"\n{annual_monthly_gross_profit_stats.round(2)}"
)
print(
    "\nMonthly gross margin statistics by year:"
    f"\n{annual_monthly_gross_margin_stats.round(2)}"
)


# Plot monthly gross revenue and profit over time

plt.plot(
    profit_per_month_processed["report_month"],
    profit_per_month_processed["gross_revenue_eur"],
    label="Gross Revenue",
    color="#0B4653",
)

plt.plot(
    profit_per_month_processed["report_month"],
    profit_per_month_processed["gross_profit_eur"],
    label="Gross Profit",
    color="#A7C957",
)

plt.title("Monthly Gross Revenue and Profit")
plt.xlabel("Month")
plt.ylabel("EUR")
plt.legend()

plt.show()


# Plot monthly gross margin over time

plt.plot(
    profit_per_month_processed["report_month"],
    profit_per_month_processed["gross_margin_pct"],
    color="#0B4653",
)

plt.title("Monthly Gross Margin")
plt.xlabel("Month")
plt.ylabel("Gross Margin (%)")
plt.show()


# Plot a histogram of monthly gross revenue

plt.hist(
    profit_per_month_processed["gross_revenue_eur"],
    bins="auto",
    color="#0B4653",
)

plt.title("Distribution of Monthly Gross Revenue")
plt.xlabel("Monthly Gross Revenue (EUR)")
plt.ylabel("Number of Months")
plt.show()


# Plot a histogram of monthly gross profit

plt.hist(
    profit_per_month_processed["gross_profit_eur"],
    bins="auto",
    color="#0B4653",
)

plt.title("Distribution of Monthly Gross Profit")
plt.xlabel("Monthly Gross Profit (EUR)")
plt.ylabel("Number of Months")
plt.show()


