import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.types import Text, Date, Numeric, Integer

load_dotenv()

engine = create_engine(os.environ["DATABASE_URL"])


# Load tables from Postgres

expenses_processed = pd.read_sql("expenses_processed", engine)
merchandise_processed = pd.read_sql("merchandise_processed", engine)


# Expense categorization

def build_expense_rulebook():
    """Return ordered regex rules for expense categorization."""
    return [
        {
            "pattern": r"\b(?:member payouts?|band member|on-set crew payment)\b",
            "expense_type": "member_payouts"
        },
        {
            "pattern": r"\b(?:shipping|packaging materials)\b",
            "expense_type": "merch_shipping"
        },
        {
            "pattern": (
                r"\b(?:merch design|merch production|merch purchase)\b"
                r"|t-?shirts? production"
                r"|poster printing"
                r"|\bprinting\b"
                r"|\bprint\b"
                r"|merch intake / receiving"
            ),
            "expense_type": "merch_production"
        },
        {
            "pattern": r"\bmixing(?: \(deposit\))?\b|\brecording(?: \(vocals\))?\b",
            "expense_type": "music_production"
        },
        {
            "pattern": (
                r"animation"
                r"|artwork / cover"
                r"|digital placement / listing"
                r"|photo shoot"
                r"|release advertising / promo"
                r"|media review / feature"
                r"|\breview\b"
                r"|video production(?: \(playthrough\))?"
                r"|visual assets / collages"
            ),
            "expense_type": "marketing"
        },
        {
            "pattern": (
                r"\btax(?:es)?\b"
                r"|social fund tax(?: / contribution)?"
                r"|banking fees?"
                r"|card processing fee"
                r"|business compliance & hardware"
            ),
            "expense_type": "taxes_fees_admin"
        },
        {
            "pattern": (
                r"accommodation"
                r"|event tickets"
                r"|travel tickets"
                r"|gig travel"
                r"|food\s*&\s*taxi"
                r"|\btaxi\b"
                r"|\blunch\b"
                r"|\bsuitcase\b"
                r"|\brehearsal\b"
            ),
            "expense_type": "tour_related_expenses"
        },
        {
            "pattern": (
                r"audio/video gear"
                r"|music gear \(unspecified\)"
                r"|guitar"
                r"|drum"
                r"|strings"
                r"|cables"
                r"|pedalboard"
                r"|playback device"
                r"|power supply"
                r"|wireless system"
                r"|headphones"
                r"|hard case / flight case"
                r"|instrument maintenance"
                r"|cymbal"
            ),
            "expense_type": "gear"
        },
    ]


def categorize_expenses(df, description_col="expense_description"):
    """Assign expense_type to expenses based on expense_description."""

    categorized_expenses = df.copy()

    categorized_expenses["expense_type"] = pd.Series(
        pd.NA,
        index=categorized_expenses.index,
        dtype="string"
    )

    for rule in build_expense_rulebook():
        rule_mask = (
            categorized_expenses["expense_type"].isna()
            & categorized_expenses[description_col].str.contains(
                rule["pattern"],
                regex=True,
                na=False
            )
        )

        categorized_expenses.loc[rule_mask, "expense_type"] = rule["expense_type"]

    categorized_expenses["expense_type"] = categorized_expenses["expense_type"].fillna(
        "other_one_off_expenses"
    )

    return categorized_expenses


# Merchandise categorization

def build_merch_rulebook():
    """Return ordered regex rules for merchandise categorization."""
    return [
        {
            "pattern": r"^(?:\d+\s+)?t-shirts?$",
            "item_type": "t_shirt"
        },
        {
            "pattern": r"^(?:\d+\s+)?long[-\s]sleeve[-\s]tee$",
            "item_type": "long_sleeve_tee"
        },
        {
            "pattern": r"^(?:\d+\s+)?hoodies?$",
            "item_type": "hoodie"
        },
        {
            "pattern": r"^(?:\d+\s+)?socks$",
            "item_type": "socks"
        },
        {
            "pattern": r"^(?:\d+\s+)?caps?$",
            "item_type": "cap"
        },
        {
            "pattern": r"^(?:\d+\s+)?beanies?$",
            "item_type": "beanie"
        },
        {
            "pattern": r"^(?:\d+\s+)?cassette[-\s]tapes?$",
            "item_type": "cassette_tape"
        },
        {
            "pattern": r"^(?:\d+\s+)?vinyls?$",
            "item_type": "vinyl"
        },
        {
            "pattern": r"^(?:\d+\s+)?pins?$",
            "item_type": "pin"
        },
        {
            "pattern": r"^(?:\d+\s+)?patch(?:es)?$",
            "item_type": "patch"
        },
        {
            "pattern": r"^(?:\d+\s+)?wrist[-\s]?bands?$",
            "item_type": "wristband"
        },
        {
            "pattern": r"^(?:\d+\s+)?guitar[-\s]picks?$",
            "item_type": "guitar_pick"
        },
        {
            "pattern": r"^(?:\d+\s+)?tote[-\s]bags?$",
            "item_type": "tote_bag"
        },
        {
            "pattern": r"^(?:\d+\s+)?mugs?$",
            "item_type": "mug"
        }
    ]


def categorize_merch(df, item_col="item"):
    """Assign item_type to merchandise rows based on item."""
    categorized_items = df.copy()
    categorized_items["item_type"] = pd.Series(
        pd.NA,
        index=categorized_items.index,
        dtype="string"
    )
    for rule in build_merch_rulebook():
        rule_mask = (
            categorized_items["item_type"].isna()
            & categorized_items[item_col].str.contains(
                rule["pattern"],
                regex=True,
                na=False
            )
        )

        categorized_items.loc[rule_mask, "item_type"] = rule["item_type"]

    categorized_items["item_type"] = categorized_items["item_type"].fillna(
        "other"
    )
    return categorized_items


# Apply categorization

expenses_enriched = categorize_expenses(expenses_processed)
merchandise_enriched = categorize_merch(merchandise_processed)


# Write enriched tables to Postgres

expenses_enriched.to_sql(
    name="expenses_enriched",
    con=engine,
    index=False,
    if_exists="replace",
    dtype={
        "expense_date": Date(),
        "expense_description": Text(),
        "expense_type": Text(),
        "total_spent_eur": Numeric(12, 2)
    }
)

merchandise_enriched.to_sql(
    name="merchandise_enriched",
    con=engine,
    index=False,
    if_exists="replace",
    dtype={
        "purchase_date": Date(),
        "sales_reference": Text(),
        "item": Text(),
        "item_type": Text(),
        "quantity": Integer(),
        "purchase_total_eur": Numeric(12, 2)
    }
)