"""Entry point: python main.py"""
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from python import extract, transform, load

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
    log.info("Starting %s", name)
    start = time.time()
    result = func(*args)
    log.info("Finished %s in %.1fs", name, time.time() - start)
    return result


def main():
    log.info("Pipeline run started")
    try:
        raw = run_stage("extract", extract.run)
        cleaned = run_stage("transform", transform.run, raw)
        run_stage("load", load.run, cleaned)
    except Exception:
        log.exception("Pipeline failed")
        sys.exit(1)
    log.info("Pipeline run succeeded")


if __name__ == "__main__":
    main()
