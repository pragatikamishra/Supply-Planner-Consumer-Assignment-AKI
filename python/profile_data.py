"""Profile the raw data: a health check of every table before we clean it."""
from pathlib import Path

import pandas as pd

from python.config import RAW_DIR, TABS

REPORT = Path("docs/data_profile.md")


def profile_column(s):
    """Summarise one column: gaps, variety, and what kind of values it holds."""
    values = s.dropna().str.strip()
    values = values[values != ""]
    row = {
        "missing": len(s) - len(values),
        "unique": values.nunique(),
        "type": "text",
        "range": "",
        "examples": ", ".join(values.unique()[:3]),
    }
    if values.empty:
        return row

    numbers = pd.to_numeric(values.str.replace(r"[,$\s]", "", regex=True), errors="coerce")
    if numbers.notna().mean() > 0.9:
        row["type"] = f"number ({numbers.notna().mean():.0%})"
        row["range"] = f"{numbers.min():,.2f} to {numbers.max():,.2f}"
        return row

    sample = values.sample(min(len(values), 2000), random_state=0)
    dates = pd.to_datetime(sample, errors="coerce", format="mixed")
    if dates.notna().mean() > 0.9:
        row["type"] = f"date ({dates.notna().mean():.0%})"
        row["range"] = f"{dates.min():%Y-%m-%d} to {dates.max():%Y-%m-%d}"
    return row


def profile_table(name, df, out):
    out.append(f"## {name}")
    out.append(f"Rows: {len(df):,} | Columns: {len(df.columns)} | "
               f"Fully duplicated rows: {df.duplicated().sum():,}")
    out.append("")
    out.append("| column | missing | unique | type | range | examples |")
    out.append("|---|---|---|---|---|---|")
    for col in df.columns:
        r = profile_column(df[col])
        out.append(f"| {col} | {r['missing']:,} | {r['unique']:,} | {r['type']} | "
                   f"{r['range']} | {r['examples']} |")
    out.append("")


def check_links(tables, out):
    """Columns with the same name in two tables are probably how they connect.
    Count values in one table that have no match in the other."""
    out.append("## Links between tables")
    found = False
    names = list(tables)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            for col in set(tables[a].columns) & set(tables[b].columns):
                found = True
                in_a = set(tables[a][col].dropna().str.strip())
                in_b = set(tables[b][col].dropna().str.strip())
                out.append(f"- `{col}` is in both {a} and {b}: "
                           f"{len(in_a - in_b):,} values in {a} missing from {b}, "
                           f"{len(in_b - in_a):,} values in {b} missing from {a}")
    if not found:
        out.append("- No column names are shared. Look at the tables and decide "
                   "which columns link them.")
    out.append("")


def run():
    tables = {name: pd.read_csv(RAW_DIR / f"{name}.csv", dtype=str) for name in TABS}
    out = ["# Raw data profile", ""]
    for name, df in tables.items():
        profile_table(name, df, out)
    check_links(tables, out)

    report = "\n".join(out)
    print(report)
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(f"\nSaved to {REPORT}")


if __name__ == "__main__":
    run()