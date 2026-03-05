"""
Merge new data with existing data.xlsx.
Deduplicates by URL + brand.
"""

from pathlib import Path
from typing import Optional

import pandas as pd


def merge_with_existing(new_df: pd.DataFrame, data_path: Path) -> pd.DataFrame:
    """
    Load existing data.xlsx if it exists, concatenate with new_df,
    deduplicate by (URL, brand), and return combined DataFrame.
    """
    if not data_path.exists():
        # Ensure content column exists for downstream steps
        if "content" not in new_df.columns:
            new_df["content"] = None
        if "relevancy" not in new_df.columns:
            new_df["relevancy"] = None
        if "relevancy_reason" not in new_df.columns:
            new_df["relevancy_reason"] = None
        if "BMQ" not in new_df.columns:
            new_df["BMQ"] = None
        if "Top Archetype" not in new_df.columns:
            new_df["Top Archetype"] = None
        return new_df

    try:
        existing = pd.read_excel(data_path, sheet_name=0)
    except Exception:
        existing = pd.DataFrame()

    if existing.empty:
        if "content" not in new_df.columns:
            new_df["content"] = None
        if "relevancy" not in new_df.columns:
            new_df["relevancy"] = None
        if "relevancy_reason" not in new_df.columns:
            new_df["relevancy_reason"] = None
        if "BMQ" not in new_df.columns:
            new_df["BMQ"] = None
        if "Top Archetype" not in new_df.columns:
            new_df["Top Archetype"] = None
        return new_df

    # Align columns: new rows get NaN for columns only in existing
    for col in existing.columns:
        if col not in new_df.columns:
            new_df[col] = None

    for col in new_df.columns:
        if col not in existing.columns:
            existing[col] = None

    # Use same column order (existing first, then any extras from new)
    cols = list(existing.columns) + [c for c in new_df.columns if c not in existing.columns]
    existing = existing[cols]
    new_df = new_df[[c for c in cols if c in new_df.columns]]

    combined = pd.concat([existing, new_df], ignore_index=True)

    # Deduplicate by URL + brand (keep first occurrence = existing wins)
    if "URL" in combined.columns and "brand" in combined.columns:
        before = len(combined)
        combined = combined.drop_duplicates(subset=["URL", "brand"], keep="first")
        if len(combined) < before:
            print(f"Deduplicated: removed {before - len(combined)} duplicate rows")

    return combined
