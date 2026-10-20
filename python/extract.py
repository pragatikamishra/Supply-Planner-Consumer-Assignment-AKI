"""Extract: download each Google Sheet tab as-is into data/raw."""
import logging
import urllib.request

import pandas as pd

from python.config import RAW_DIR, TABS, sheet_csv_url

log = logging.getLogger("extract")


def run():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw = {}
    for name, gid in TABS.items():
        path = RAW_DIR / f"{name}.csv"
        # 1. Download the tab and save it untouched
        urllib.request.urlretrieve(sheet_csv_url(gid), path)
        # 2. Read it as a table. dtype=str keeps every value as plain text,
        #    because deciding what is a number or a date is the transform step's job
        df = pd.read_csv(path, dtype=str)
        log.info("%s: %d rows, %d columns -> %s", name, len(df), len(df.columns), path)
        raw[name] = df
    return raw


if __name__ == "__main__":
    # Only runs when you start this file directly, not when main.py imports it
    logging.basicConfig(level=logging.INFO)
    run()