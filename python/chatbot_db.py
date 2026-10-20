"""Database helper for the chatbot: describes the tables and runs read-only SQL."""
import sqlite3

import pandas as pd

from python.config import DB_PATH

MAX_ROWS = 50          # never send more than 50 rows to the AI
MAX_LIST_VALUES = 15   # list a text column's values if it has this many or fewer


def connect_read_only():
    """Open sales.db in read-only mode, so nothing can change or delete data."""
    uri = DB_PATH.resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def get_schema():
    """Return a text description of every table, its columns and example values."""
    lines = []
    with connect_read_only() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
        for (table,) in tables:
            lines.append(f"Table {table}:")
            for column in conn.execute(f"PRAGMA table_info({table})").fetchall():
                name, col_type = column[1], column[2]
                line = f"  - {name} ({col_type})"
                if col_type == "TEXT":
                    values = conn.execute(
                        f"SELECT DISTINCT {name} FROM {table} LIMIT {MAX_LIST_VALUES + 1}"
                    ).fetchall()
                    if len(values) <= MAX_LIST_VALUES:
                        line += " values: " + ", ".join(str(v[0]) for v in values)
                lines.append(line)
    return "\n".join(lines)


def run_query(sql):
    """Run one SELECT query and return the result as a table (max 50 rows)."""
    sql = sql.strip().rstrip(";")
    if not sql.lower().startswith(("select", "with")):
        raise ValueError("Only SELECT queries are allowed.")
    conn = connect_read_only()
    try:
        result = pd.read_sql_query(sql, conn)
    finally:
        conn.close()
    return result.head(MAX_ROWS)


if __name__ == "__main__":
    print(get_schema())
    print()
    print(run_query(
        "SELECT transaction_type, ROUND(SUM(net_sales_aed), 2) AS sales_aed "
        "FROM fact_sales GROUP BY transaction_type"
    ))