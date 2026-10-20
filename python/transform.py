"""Transform: turn the raw tables into clean tables ready for the database.

Every rule here comes from a decision in docs/data_checks.md.
"""
import logging

import pandas as pd

from python.config import CLEANED_DIR, RAW_DIR, REJECTED_DIR, TABS

log = logging.getLogger("transform")


def tidy_text(df):
    """Remove spaces at the start and end of every text value."""
    return df.apply(lambda col: col.str.strip())


def clean_product(product):
    product = tidy_text(product)
    return product.rename(columns={
        "Product code": "product_code",
        "Brand": "brand",
        "Division": "division",
        "Category": "category",
        "Sub-category": "sub_category",
    })


def clean_customer(customer):
    """Decision C: fix spacing and capitals, split Customer type in two. No merging."""
    customer = tidy_text(customer)

    # "General Trade-Offline" -> trade type "General Trade", sales mode "Offline".
    # Labels without a suffix (e.g. "Internal") get sales mode "Not specified".
    parts = customer["Customer type"].str.extract(r"^(.*?)\s*-\s*(Offline|Online|D2C)$")
    customer["trade_type"] = parts[0].fillna(customer["Customer type"])
    customer["sales_mode"] = parts[1].fillna("Not specified")
    customer["customer_type"] = customer["trade_type"].where(
        customer["sales_mode"] == "Not specified",
        customer["trade_type"] + " - " + customer["sales_mode"],
    )

    # "PRIVATE" -> "Private"
    customer["sales_channel"] = customer["Sales channel"].str.title()

    return customer.rename(columns={"Customer": "customer", "Country": "country"})[
        ["customer", "country", "customer_type", "trade_type", "sales_mode", "sales_channel"]
    ]


def clean_sales(sales):
    sales = tidy_text(sales)
    sales = sales.rename(columns={
        "Month": "month_text",
        "Customer": "customer",
        "Product code": "product_code",
        "Quantity": "quantity",
        "Net sales value (AED)": "net_sales_aed",
        "Cost of sales (AED)": "cost_of_sales_aed",
    })

    # Text -> real values. Anything that can't be converted becomes empty (NaN/NaT)
    sales["month"] = pd.to_datetime(sales["month_text"], format="%b-%Y", errors="coerce")
    for col in ["quantity", "net_sales_aed", "cost_of_sales_aed"]:
        sales[col] = pd.to_numeric(sales[col], errors="coerce")

    # Decision D: rows that can't be trusted go to data/rejected, each with a reason
    qty, value = sales["quantity"], sales["net_sales_aed"]
    reason = pd.Series("", index=sales.index)
    reason[sales["month"].isna()] = "Month is not a valid date"
    reason[sales[["quantity", "net_sales_aed", "cost_of_sales_aed"]].isna().any(axis=1)] = "Number could not be read"
    reason[((qty < 0) & (value > 0)) | ((qty > 0) & (value < 0))] = "Quantity and value have opposite signs"
    rejected = sales[reason != ""].assign(reject_reason=reason[reason != ""])
    sales = sales[reason == ""].copy()

    # Decision A: keep returns, label every row
    sales["transaction_type"] = "Sale"
    sales.loc[sales["quantity"] < 0, "transaction_type"] = "Return"
    sales.loc[sales["quantity"] == 0, "transaction_type"] = "Adjustment"

    sales["gross_profit_aed"] = sales["net_sales_aed"] - sales["cost_of_sales_aed"]

    # Decision B: details live in the product and customer tables, so keep only the keys
    sales = sales[["month", "customer", "product_code", "transaction_type",
                   "quantity", "net_sales_aed", "cost_of_sales_aed", "gross_profit_aed"]]
    return sales, rejected


def run(raw):
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    sales, rejected = clean_sales(raw["sales"])
    cleaned = {
        "fact_sales": sales,
        "dim_product": clean_product(raw["product"]),
        "dim_customer": clean_customer(raw["customer"]),
    }

    for name, df in cleaned.items():
        df.to_csv(CLEANED_DIR / f"{name}.csv", index=False)
        log.info("%s: %d rows -> %s", name, len(df), CLEANED_DIR / f"{name}.csv")
    rejected.to_csv(REJECTED_DIR / "sales_rejected.csv", index=False)
    log.info("rejected: %d rows -> %s", len(rejected), REJECTED_DIR / "sales_rejected.csv")
    return cleaned


if __name__ == "__main__":
    # Run on its own: read the files extract already saved, no new download
    logging.basicConfig(level=logging.INFO)
    raw = {name: pd.read_csv(RAW_DIR / f"{name}.csv", dtype=str) for name in TABS}
    run(raw)