import os
import logging
from typing import List, Optional
import pandas as pd

from universal.config.config import CONFIG
from universal.utils.folders import get_dashboard_data_path


logger = logging.getLogger(__name__)


def _pr_dir() -> str:
    return os.path.join(CONFIG.paths.new_data, "pr", "transformed")


def _list_pr_files() -> List[str]:
    pr_dir = _pr_dir()
    if not os.path.exists(pr_dir):
        logger.error(f"PR directory not found: {pr_dir}")
        return []
    excel_files = []
    for file in os.listdir(pr_dir):
        if file.endswith(".xlsx") and not file.startswith("~$"):
            excel_files.append(os.path.join(pr_dir, file))
    logger.info(f"Found {len(excel_files)} PR Excel files")
    return excel_files


def _read_pr_file(file_path: str) -> Optional[pd.DataFrame]:
    try:
        excel_file = pd.ExcelFile(file_path)
        sheet = "Raw Data" if "Raw Data" in excel_file.sheet_names else excel_file.sheet_names[
            0]
        df = pd.read_excel(file_path, sheet_name=sheet)
        df["source_file"] = os.path.basename(file_path)
        logger.info(
            f"Loaded {len(df)} rows from {os.path.basename(file_path)}")
        return df
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None


def analyze_pr_for_month(year: int, month: int, output_folder: Optional[str] = None) -> Optional[str]:
    logger.info(f"Starting PR analysis for {year}-{month:02d}")
    print(f"Starting PR analysis for {year}-{month:02d}")
    files = _list_pr_files()
    print(f"Found {len(files)} PR files")
    print(f"Files: {files}")
    if not files:
        print("No PR files found to merge")
        logger.error("No PR files found to merge")
        return None
    dataframes = []
    for path in files:
        df = _read_pr_file(path)
        if df is not None and not df.empty:
            dataframes.append(df)
    if not dataframes:
        print("No valid data found in PR files")
        logger.error("No valid data found in PR files")
        return None
    try:
        merged_df = pd.concat(dataframes, ignore_index=True)
        if "content" in merged_df.columns:
            merged_df = merged_df.drop_duplicates(
                subset=["content"], keep="first")
    except Exception as e:
        print(f"Error merging PR data: {e}")
        logger.error(f"Error merging PR data: {e}")
        return None
    output_dir = get_dashboard_data_path(year, month, "pr")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "pr_master_data.xlsx")
    try:
        with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
            merged_df.to_excel(writer, sheet_name="Master Data", index=False)
        logger.info(f"Created master PR file: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error creating master PR file: {e}")
        logger.error(f"Error creating master PR file: {e}")
        return None
