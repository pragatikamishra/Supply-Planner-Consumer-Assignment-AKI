"""Run the whole pipeline: python main.py  (add --no-dashboard to skip opening Power BI)"""
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from python import extract, transform, load

DASHBOARD = Path("powerbi/sales_dashboard.pbix")

# Every run writes its own log file, e.g. logs/pipeline_20241020_0800.log
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"pipeline_{datetime.now():%Y%m%d_%H%M%S}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("main")


def run_stage(name, func, *args):
    """Run one step, timing it and logging when it starts and ends."""
    log.info("Starting %s", name)
    start = time.time()
    result = func(*args)
    log.info("Finished %s in %.1fs", name, time.time() - start)
    return result


def open_dashboard():
    """Open the Power BI report, like double-clicking it (Windows only)."""
    if "--no-dashboard" in sys.argv or os.name != "nt":
        return  # skipped for scheduled runs and on servers without Power BI
    if not DASHBOARD.exists():
        log.warning("Dashboard not found at %s", DASHBOARD)
        return
    log.info("Opening %s", DASHBOARD)
    os.startfile(DASHBOARD.resolve())


def main():
    log.info("Pipeline run started")
    try:
        raw = run_stage("extract", extract.run)
        cleaned = run_stage("transform", transform.run, raw)
        run_stage("load", load.run, cleaned)
    except Exception:
        log.exception("Pipeline failed")
        sys.exit(1)  # an error code, so a scheduler knows the run failed
    log.info("Pipeline run succeeded")
    open_dashboard()


if __name__ == "__main__":
    main()