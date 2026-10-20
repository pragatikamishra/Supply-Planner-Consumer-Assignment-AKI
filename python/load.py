"""Load: write the clean tables into the SQLite database that Power BI reads."""
import logging
import sqlite3
from pathlib import Path

import pandas as pd

from python.config import CLEANED_DIR, DB_PATH

log = logging.getLogger("load")

SCHEMA = Path("sql/schema.sql")
# Descriptions first, then the facts that point to them
LOAD_ORDER = ["dim_product", "dim_customer", "fact_sales"]


def run(cleaned):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA.read_text())
        with conn:  # one transaction: either every table loads, or nothing changes
            for name in LOAD_ORDER:
                df = cleaned[name].copy()
                if "month" in df:
                    df["month"] = pd.to_datetime(df["month"]).dt.strftime("%Y-%m-%d")
                df.to_sql(name, conn, if_exists="append", index=False)

        # Check: the database holds exactly what we meant to load
        for name in LOAD_ORDER:
            in_db = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            if in_db != len(cleaned[name]):
                raise ValueError(f"{name}: expected {len(cleaned[name])} rows, database has {in_db}")
            log.info("%s: %d rows loaded into %s", name, in_db, DB_PATH)
    finally:
        conn.close()


if __name__ == "__main__":
    # Run on its own: read the files transform already saved
    logging.basicConfig(level=logging.INFO)
    run({name: pd.read_csv(CLEANED_DIR / f"{name}.csv") for name in LOAD_ORDER})