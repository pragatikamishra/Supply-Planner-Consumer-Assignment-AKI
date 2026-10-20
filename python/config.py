"""Settings for the pipeline: where the data comes from and where it goes."""
from pathlib import Path

# The Google Sheet (the long code after /d/ in the sheet link)
SHEET_ID = "1rGlMBEcpeYVIHC2J1saG0FgZ8NQ7MO6bg0CEF86I5d8"

# Each tab's ID (the number after gid= in the link)
TABS = {
    "sales": 1201932520,
    "product": 498165540,
    "customer": 108361739,
}

# Where files are saved
RAW_DIR = Path("data/raw")
CLEANED_DIR = Path("data/cleaned")
REJECTED_DIR = Path("data/rejected")
DB_PATH = Path("data/sales.db")


def sheet_csv_url(gid):
    """Build the link that downloads one tab as a CSV file."""
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
