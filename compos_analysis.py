import os
import logging
import pandas as pd
import sys

# Ensure repo root is on sys.path so 'universal' package is importable under Streamlit
REPO_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from typing import Optional
from universal.config.config import MEDIA_TYPES
from universal.utils.folders import get_dashboard_data_path
from universal.analysis.pr.news_compos_pipeline import compos_analysis


logger = logging.getLogger(__name__)


def analyze_compos_for_month(year: int, month: int, output_folder: str) -> Optional[str]:

    pr_master = os.path.join(get_dashboard_data_path(
        year, month, "pr"), "pr_master_data.xlsx")
    if not os.path.exists(pr_master):
        logger.error(f"PR master not found: {pr_master}")
        print(f"PR master not found: {pr_master}")
        return None

    try:
        df = pd.read_excel(pr_master)
    except Exception as e:
        logger.error(f"Failed to read PR master: {e}")
        print(f"Failed to read PR master: {e}")
        return None
    
    # Get text and brand columns
    text_col = MEDIA_TYPES["pr"]["text_column"]
    brand_col = MEDIA_TYPES["pr"]["brand_column"]
    if text_col not in df.columns or brand_col not in df.columns:
        logger.error("PR master missing required columns.")
        print(f"PR master missing required columns: {text_col} or {brand_col}")
        return None

    if df.empty:
        logger.warning("No PR items to analyze.")
        print(f"No PR items to analyze.")
        return None

    os.makedirs(output_folder, exist_ok=True)
    # Run pipeline 
    compos_analysis(df, output_folder, model="gpt-4o-mini", max_workers=50)

if __name__ == "__main__":
    analyze_compos_for_month(2025, 12, "data/dashboard_data/one_shot/pr/analysis/compos")
