"""
SIRIN PR Pipeline: Muck Rack → data.xlsx

Run this script to process new Muck Rack exports from the "new data" folder,
run the full analysis pipeline, and append results to data.xlsx in "data sirin".

Usage: python run_pipeline.py
"""

import os
import sys
import logging
from pathlib import Path

# Suppress verbose logging (HTTP requests, etc.)
logging.basicConfig(level=logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# Load .env for API keys
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# Folders
NEW_DATA_DIR = PROJECT_ROOT / "new data"
DATA_SIRIN_DIR = PROJECT_ROOT / "data sirin"
DATA_FILE = DATA_SIRIN_DIR / "data.xlsx"


def main():
    # Ensure folders exist
    NEW_DATA_DIR.mkdir(exist_ok=True)
    DATA_SIRIN_DIR.mkdir(exist_ok=True)

    # Step 1: Transform Muck Rack files and merge into single DataFrame
    from pipeline.transform import transform_and_merge_new_data

    df = transform_and_merge_new_data(NEW_DATA_DIR)
    if df is None or df.empty:
        print("No new data to process. Exiting.")
        return

    # Step 2: Load existing data (if any) and append new rows
    from pipeline.merge import merge_with_existing

    df = merge_with_existing(df, DATA_FILE)

    # Step 3: Maintext retrieval (for rows without content)
    from pipeline.maintext import fetch_maintext_for_missing

    df = fetch_maintext_for_missing(df)

    # Step 4: Relevancy filtering
    from pipeline.relevancy import run_relevancy_analysis

    df = run_relevancy_analysis(df)

    # Step 5: Sentiment analysis (Positive, Negative, Neutral)
    from pipeline.sentiment import run_sentiment_analysis

    df = run_sentiment_analysis(df)

    # Step 6: BMQ calculations (requires content)
    from pipeline.bmq import run_bmq_calculations

    df = run_bmq_calculations(df)

    # Step 7: Compos / archetype assignment
    from pipeline.compos import run_compos_analysis

    df = run_compos_analysis(df)

    # Step 8: Save to data.xlsx
    df.to_excel(DATA_FILE, index=False, sheet_name="Data")
    print(f"Saved {len(df)} rows to {DATA_FILE}")


if __name__ == "__main__":
    main()
