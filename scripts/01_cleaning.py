import os
from decimal import Decimal, InvalidOperation
import hmac
import hashlib

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.types import Numeric, Date, Text, Integer


load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"])


# Load tables from Postgres

expenses_raw = pd.read_sql("expenses_raw", engine)
live_shows_raw = pd.read_sql("live_shows_raw", engine)
merchandise_raw = pd.read_sql("merchandise_raw", engine)
profit_per_month_raw = pd.read_sql("profit_per_month_raw", engine)
releases_raw = pd.read_sql("releases_raw", engine)
merch_production_cost_raw = pd.read_sql("merch_production_cost_raw", engine)
merch_drops_raw = pd.read_sql("merch_drops_raw", engine)
merch_promotions_raw = pd.read_sql("merch_promotions_raw", engine)


# Rename some columns with undescriptive names so they're easier to navigate

expenses_raw = (
    expenses_raw
    .rename(columns={"date": "expense_date",
                     "total_spent": "total_spent_eur"})
)

profit_per_month_raw = (
    profit_per_month_raw
    .rename(columns={"month": "report_month",
                     "gross_margin": "gross_margin_pct",
                     "gross_revenue": "gross_revenue_eur",
                     "gross_profit": "gross_profit_eur"})
)

merchandise_raw = (
    merchandise_raw
    .rename(columns={"total": "purchase_total_eur",
                     "buyer": "sales_reference"})
)

merch_production_cost_raw = (
    merch_production_cost_raw
    .rename(columns={"price": "avg_production_cost_eur"})
)


# Define reusable cleaning functions

def replace_blank_cells_with_NA(df):
    """Replace empty and whitespace-only cells with pd.NA."""
    df = df.replace(r"^\s*$", pd.NA, regex=True)
    return df


def convert_date_column(df, column, date_format="%d.%m.%Y"):
    """Convert a text column with date to datetime."""
    df[column] = pd.to_datetime(df[column], format=date_format, errors="coerce")
    return df


def clean_money_column(df, column):
    """Clean text money values."""
    df[column] = (
        df[column]
        .str.replace("€", "", regex=False)
        .str.replace("\xa0", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return df


def normalize_text_column(df, column):
    """Trim extra whitespace and convert text to lowercase."""
    df[column] = (
        df[column]
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.lower()
    )
    return df


def convert_column_to_decimal(df, column):
    """Convert values to Decimal."""
    def value_to_decimal(value):
        if pd.isna(value) or value == "":
            return pd.NA
        try:
            return Decimal(value)
        except InvalidOperation:
            return pd.NA

    df[column] = df[column].apply(value_to_decimal)
    return df


def pseudonymize(value):
    """Return a pseudonym, preserving missing values."""
    if pd.isna(value):
        return pd.NA
    msg = str(value).encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()[:16]


# Normalize expenses_raw table

expenses_processed = (
    expenses_raw
    .pipe(replace_blank_cells_with_NA)
    .pipe(convert_date_column, "expense_date")
    .pipe(clean_money_column, "total_spent_eur")
    .pipe(normalize_text_column, "expense_description")
    .pipe(convert_column_to_decimal, "total_spent_eur")
)


# Normalize live_shows_raw table

live_shows_processed = (
    live_shows_raw
    .pipe(replace_blank_cells_with_NA)
    .pipe(convert_date_column, "show_date")
)


# Normalize merchandise_raw table

merchandise_processed = (
    merchandise_raw
   .pipe(replace_blank_cells_with_NA)
   .pipe(convert_date_column, "purchase_date")
   .pipe(clean_money_column, "purchase_total_eur")
   .pipe(normalize_text_column, "item")
   .pipe(normalize_text_column, "sales_reference")
   .pipe(convert_column_to_decimal, "purchase_total_eur")
)


# Normalize profit_per_month_raw table

profit_per_month_raw["gross_margin_pct"] = (
    profit_per_month_raw["gross_margin_pct"]
    .str.replace("%", "", regex=False)
    .str.replace(",", ".", regex=False)
)

profit_per_month_processed = (
    profit_per_month_raw
    .pipe(replace_blank_cells_with_NA)
    .pipe(convert_date_column, "report_month", date_format="%m.%Y")
    .pipe(clean_money_column, "gross_revenue_eur")
    .pipe(clean_money_column, "gross_profit_eur")
    .pipe(convert_column_to_decimal, "gross_revenue_eur")
    .pipe(convert_column_to_decimal, "gross_profit_eur")
    .pipe(convert_column_to_decimal, "gross_margin_pct")
)


# Normalize releases_raw table

releases_processed = (
    releases_raw
    .pipe(replace_blank_cells_with_NA)
    .pipe(convert_date_column, "release_date")
)


# Normalize merch_production_cost_raw table

merch_production_cost_processed = (
    merch_production_cost_raw
    .pipe(replace_blank_cells_with_NA)
    .pipe(clean_money_column, "avg_production_cost_eur")
    .pipe(normalize_text_column, "item_type")
    .pipe(convert_column_to_decimal, "avg_production_cost_eur")
)

merch_production_cost_processed["item_type"] = (
    merch_production_cost_processed["item_type"]
    .replace({"t-shirt": "t_shirt",
              "cassette tape": "cassette_tape",
              "tote bag": "tote_bag",
              "long-sleeve tee": "long_sleeve_tee",
              "guitar pick": "guitar_pick"})
)


# Normalize merch_drops_raw table

merch_drops_processed = (
    merch_drops_raw
    .pipe(replace_blank_cells_with_NA)
    .pipe(convert_date_column, "drop_date")
    .pipe(normalize_text_column, "item_type")
)


# Normalize merch_promotions_raw table

merch_promotions_processed = (
    merch_promotions_raw
    .pipe(replace_blank_cells_with_NA)
    .pipe(convert_date_column, "promotion_date")
    .pipe(normalize_text_column, "promotion_type")
)


# Pseudonymize sales references that may contain personal data

anon_salt = os.getenv("ANON_SALT")
if not anon_salt:
    raise RuntimeError("ANON_SALT is missing. Add it to .env")

key = anon_salt.encode("utf-8")

merchandise_processed["sales_reference"] = (
    merchandise_processed["sales_reference"]
    .apply(pseudonymize)
)


# Upload processed tables to Postgres

expenses_processed.to_sql(
    name="expenses_processed",
    con=engine,
    index=False,
    if_exists="replace",
    dtype={
        "expense_date": Date(),
        "expense_description": Text(),
        "total_spent_eur": Numeric(12,2)
    }
)

live_shows_processed.to_sql(
    name="live_shows_processed",
    con=engine,
    index=False,
    if_exists="replace",
    dtype={
        "show_date": Date()
    }
)

merchandise_processed.to_sql(
    name="merchandise_processed",
    con=engine,
    index=False,
    if_exists="replace",
    dtype={
        "purchase_date": Date(),
        "sales_reference": Text(),
        "item": Text(),
        "quantity": Integer(),
        "purchase_total_eur": Numeric(12,2)
    }
)

profit_per_month_processed.to_sql(
    name="profit_per_month_processed",
    con=engine,
    index=False,
    if_exists="replace",
    dtype={
        "report_month": Date(),
        "gross_revenue_eur": Numeric(12,2),
        "gross_profit_eur": Numeric(12,2),
        "gross_margin_pct": Numeric(12,2)
    }
)

releases_processed.to_sql(
    name="releases_processed",
    con=engine,
    index=False,
    if_exists="replace",
    dtype={
        "release_date": Date(),
        "release_type": Text()
    }
)

merch_production_cost_processed.to_sql(
    name="merch_production_cost_processed",
    con=engine,
    index=False,
    if_exists="replace",
    dtype={
        "item_type": Text(),
        "avg_production_cost_eur": Numeric(12,2),
        "cost_year": Integer()
    }
)

merch_drops_processed.to_sql(
    name="merch_drops_processed",
    con=engine,
    index=False,
    if_exists="replace",
    dtype={
        "drop_date": Date(),
        "item_type": Text(),
        "new_designs_count": Integer()
    }
)

merch_promotions_processed.to_sql(
    name="merch_promotions_processed",
    con=engine,
    index=False,
    if_exists="replace",
    dtype={
        "promotion_date": Date(),
        "promotion_type": Text()
    }
)