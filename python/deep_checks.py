"""Deep checks: answer the questions the profile report raised."""
import pandas as pd

from python.config import RAW_DIR

NUMBER_COLS = ["Quantity", "Net sales value (AED)", "Cost of sales (AED)"]
PRODUCT_COLS = ["Brand", "Division", "Category", "Sub-category"]
CUSTOMER_COLS = ["Country", "Customer type"]


def load(name):
    return pd.read_csv(RAW_DIR / f"{name}.csv", dtype=str)


def section(title):
    print(f"\n=== {title} ===")


def main():
    sales, product, customer = load("sales"), load("product"), load("customer")
    for col in NUMBER_COLS:
        sales[col] = pd.to_numeric(sales[col])
    qty, value, cost = (sales[c] for c in NUMBER_COLS)

    section("1. Is Month + Customer + Product code unique in sales?")
    dupes = sales.duplicated(subset=["Month", "Customer", "Product code"], keep=False)
    print(f"Rows sharing the same Month + Customer + Product code: {dupes.sum():,}")

    section("2. Negative and zero values")
    print(f"Quantity < 0:        {(qty < 0).sum():,} rows")
    print(f"Net sales < 0:       {(value < 0).sum():,} rows")
    print(f"Cost < 0:            {(cost < 0).sum():,} rows")
    print(f"Quantity = 0:        {(qty == 0).sum():,} rows")
    print(f"Net sales = 0:       {(value == 0).sum():,} rows")
    print(f"Signs disagree (Quantity and Net sales point in different directions): "
          f"{((qty < 0) & (value > 0) | (qty > 0) & (value < 0)).sum():,} rows")
    print(f"Sold below cost (Cost > Net sales, both positive): "
          f"{((value > 0) & (cost > value)).sum():,} rows")
    print(f"Total Net sales: {value.sum():,.2f} AED, of which returns: "
          f"{value[value < 0].sum():,.2f} AED")

    section("3. Do product details in sales match the product table?")
    merged = sales.merge(product, on="Product code", suffixes=("", "_product"))
    for col in PRODUCT_COLS:
        print(f"{col}: {(merged[col] != merged[col + '_product']).sum():,} rows differ")

    section("4. Do customer details in sales match the customer table?")
    merged = sales.merge(customer, on="Customer", suffixes=("", "_customer"))
    for col in CUSTOMER_COLS:
        print(f"{col}: {(merged[col] != merged[col + '_customer']).sum():,} rows differ")

    section("5. Every Customer type and Sales channel, with how many customers")
    print(customer["Customer type"].value_counts().to_string())
    print()
    print(customer["Sales channel"].value_counts().to_string())


if __name__ == "__main__":
    main()