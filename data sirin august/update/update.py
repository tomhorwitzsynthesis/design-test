import os
import re
import shutil
import logging
import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# ---------------- Logging ----------------
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------- Config ----------------
# Where to look for things
BASE_DIR = Path(__file__).resolve().parent
PARENT_DIR = BASE_DIR.parent

UPDATES_DIRS = [
    BASE_DIR,                  # allow drop-in next to script (legacy)
    BASE_DIR / "updates",      # preferred location for monthly CSV updates
]
COMPOS_DIR = BASE_DIR / "compos"
AGILITY_DIR = PARENT_DIR / "agility"

# File patterns
MAIN_CSV_SUFFIX = "_data.csv"
AGILITY_SUFFIX = "_agility.xlsx"
COMPOS_REGEX = re.compile(r"^(?P<brand>.+?)_compos.*\.xlsx$", re.IGNORECASE)

# Behavior toggles
DROP_DUPLICATES = True     # exact row duplicates after concat
BACKUP_ENABLED = True

# ---------------- Helpers ----------------

def previous_month(reference_date: Optional[dt.date] = None) -> Tuple[int, int]:
    """Return (year, month) for the previous calendar month in Europe/Amsterdam context."""
    if reference_date is None:
        reference_date = dt.datetime.now(dt.timezone.utc).astimezone().date()
    first_of_month = reference_date.replace(day=1)
    prev_last_day = first_of_month - dt.timedelta(days=1)
    return prev_last_day.year, prev_last_day.month

def month_label(year: int, month: int) -> str:
    """e.g. 2025, 8 -> 'August'"""
    return dt.date(year, month, 1).strftime("%B")

def slugify_brand(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")

def normalize_col(col: str) -> str:
    # remove BOM, strip, collapse whitespace, lower
    col = col.replace("\ufeff", "")
    col = " ".join(col.strip().split())
    return col.lower()

def atomic_write_csv(df: pd.DataFrame, path: Path) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    tmp.replace(path)

def atomic_write_excel(sheets: Dict[str, pd.DataFrame], path: Path) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with pd.ExcelWriter(tmp, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    tmp.replace(path)

def backup_file(src: Path, backup_root: Path) -> None:
    backup_root.mkdir(parents=True, exist_ok=True)
    dst = backup_root / src.name
    shutil.copy2(src, dst)

def discover_brands_from_main_and_agility() -> Tuple[Dict[str, Path], Dict[str, Path]]:
    """
    Return:
      main_csvs: {brand_slug: path_to_main_csv}
      agility_xlsx: {brand_slug: path_to_agility_xlsx}
    """
    main_csvs = {}
    for p in sorted(PARENT_DIR.glob(f"*{MAIN_CSV_SUFFIX}")):
        brand = p.name[: -len(MAIN_CSV_SUFFIX)]
        main_csvs[slugify_brand(brand)] = p

    agility_xlsx = {}
    for p in sorted(AGILITY_DIR.glob(f"*{AGILITY_SUFFIX}")):
        brand = p.name[: -len(AGILITY_SUFFIX)]
        agility_xlsx[slugify_brand(brand)] = p

    return main_csvs, agility_xlsx

def expected_update_csv_candidates(brand_raw: str, month_str: str) -> List[str]:
    """
    Plausible update filenames for the brand and month (case-insensitive match used later):
      'Brand - Month.csv'
      'Brand_Month.csv'
      'Brand.csv' (fallback)
    """
    return [
        f"{brand_raw} - {month_str}.csv",
        f"{brand_raw}_{month_str}.csv",
        f"{brand_raw}.csv",
    ]

def find_first_existing_case_insensitive(filename: str, search_dirs: List[Path]) -> Optional[Path]:
    """Case-insensitive filename search across directories. Returns first match."""
    low = filename.lower()
    for d in search_dirs:
        if not d.exists():
            continue
        for p in d.iterdir():
            if p.is_file() and p.name.lower() == low:
                return p
    return None

def find_update_csv_for_brand(brand_raw: str, month_str: str) -> Optional[Path]:
    for candidate in expected_update_csv_candidates(brand_raw, month_str):
        found = find_first_existing_case_insensitive(candidate, UPDATES_DIRS)
        if found:
            return found
    return None

def map_compos_to_agility() -> Dict[str, Tuple[Path, Optional[Path]]]:
    """
    Return mapping {brand_slug: (compos_path, agility_path_or_None)} for all compos files found.
    """
    mapping: Dict[str, Tuple[Path, Optional[Path]]] = {}
    for p in sorted(COMPOS_DIR.glob("*.xlsx")):
        m = COMPOS_REGEX.match(p.name)
        if not m:
            continue
        brand_raw = m.group("brand")
        brand = slugify_brand(brand_raw)
        agility_path = AGILITY_DIR / f"{brand_raw}{AGILITY_SUFFIX}"
        if not agility_path.exists():
            # Try slug-based file too (in case of naming normalization)
            agility_path2 = AGILITY_DIR / f"{brand}{AGILITY_SUFFIX}"
            agility = agility_path2 if agility_path2.exists() else None
        else:
            agility = agility_path
        mapping[brand] = (p, agility)
    return mapping

def read_csv_with_normalized_cols(path: Path) -> Tuple[pd.DataFrame, Dict[str, str]]:
    df = pd.read_csv(path)
    original_cols = list(df.columns)
    normalized = {c: normalize_col(c) for c in original_cols}
    # Deduplicate normalized names by suffixing
    seen = {}
    final_map = {}
    for orig, norm in normalized.items():
        count = seen.get(norm, 0) + 1
        seen[norm] = count
        final = norm if count == 1 else f"{norm}__{count}"
        final_map[orig] = final
    df.columns = [final_map[c] for c in original_cols]
    return df, final_map  # map: original -> normalized

def restore_original_order_cols(base_df: pd.DataFrame, cols_order_source: pd.DataFrame) -> List[str]:
    """
    Return a column order that starts with the columns (by order) from cols_order_source,
    then any extras in alphabetical order at the end.
    """
    source_cols = list(cols_order_source.columns)
    extras = [c for c in base_df.columns if c not in source_cols]
    return source_cols + sorted(extras)

# ---------------- Main CSV updater ----------------

def update_main_csv_files(target_year: int, target_month: int) -> None:
    logger.info("=== Updating main CSV files ===")
    month_str = month_label(target_year, target_month)  # e.g., 'August'

    main_csvs, agility_xlsx = discover_brands_from_main_and_agility()
    all_brand_slugs = set(main_csvs) | set(agility_xlsx)

    if not all_brand_slugs:
        logger.warning("No brands discovered; nothing to do.")
        return

    logger.info("Discovered brands (from main/agility): %s", ", ".join(sorted(all_brand_slugs)))

    backup_root = BASE_DIR / "backups" / dt.datetime.now().strftime("%Y%m%d-%H%M%S")

    for brand in sorted(all_brand_slugs):
        main_path = main_csvs.get(brand)
        if not main_path or not main_path.exists():
            logger.warning("Main CSV for brand '%s' not found; skipping main update for this brand.", brand)
            continue

        # Try to preserve a human-friendly brand name in filenames
        brand_raw = main_path.stem[: -len("_data")] if main_path.name.endswith(MAIN_CSV_SUFFIX) else brand

        update_path = find_update_csv_for_brand(brand_raw, month_str)

        if not update_path:
            logger.info("No update CSV found for brand '%s' for %s; leaving main file unchanged.", brand, month_str)
            continue

        try:
            logger.info("Processing main CSV: %s <- %s", main_path.name, update_path.name)
            main_df_raw = pd.read_csv(main_path)
            update_df_norm, update_map = read_csv_with_normalized_cols(update_path)

            # normalize main columns to align, but keep a copy of original order
            main_df_norm, main_map = read_csv_with_normalized_cols(main_path)

            # Align on intersection of normalized columns
            common = [c for c in main_df_norm.columns if c in update_df_norm.columns]
            if not common:
                logger.error("No common columns between %s and %s; skipping.", main_path.name, update_path.name)
                continue

            main_aligned = main_df_norm[common]
            update_aligned = update_df_norm[common]

            combined = pd.concat([main_aligned, update_aligned], ignore_index=True)

            if DROP_DUPLICATES:
                before = len(combined)
                combined = combined.drop_duplicates()
                logger.info("Dropped %d exact duplicate rows.", before - len(combined))

            # Restore original main column order (based on original main_df_raw)
            # Build map from normalized back to original names where possible
            # Prefer original main column names to preserve headers
            norm_to_main_orig = {v: k for k, v in main_map.items()}
            restored_cols = []
            for c in main_df_norm.columns:
                if c in combined.columns:
                    restored_cols.append(c)
            combined = combined[restored_cols]
            combined.columns = [norm_to_main_orig.get(c, c) for c in combined.columns]

            if BACKUP_ENABLED:
                backup_file(main_path, backup_root)

            atomic_write_csv(combined, main_path)
            logger.info("Updated: %s (rows: %d)", main_path.name, len(combined))

        except Exception as e:
            logger.exception("Error updating main CSV for brand '%s': %s", brand, e)

# ---------------- Agility updater ----------------

def choose_best_sheet_for_agility(compos_path: Path, agility_cols_norm: List[str]) -> Tuple[pd.DataFrame, str, int]:
    """
    Read compos Excel and choose the sheet with the most column overlap with agility columns (normalized).
    """
    sheets = pd.read_excel(compos_path, sheet_name=None)
    best_name, best_df, best_match = None, None, -1
    agility_set = set(agility_cols_norm)
    for name, df in sheets.items():
        if df is None or len(df) == 0:
            continue
        df_norm, _ = _normalize_df(df)
        overlap = len(agility_set.intersection(df_norm.columns))
        logger.info("  Sheet '%s': rows=%d, cols=%d, matching=%d", name, len(df), df.shape[1], overlap)
        if overlap > best_match:
            best_match = overlap
            best_name = name
            best_df = df_norm
    if best_df is None:
        raise ValueError("No non-empty sheets in compos file")
    return best_df, best_name, best_match

def _normalize_df(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    original_cols = list(df.columns)
    normalized = {c: normalize_col(str(c)) for c in original_cols}
    seen = {}
    final_map = {}
    for orig, norm in normalized.items():
        count = seen.get(norm, 0) + 1
        seen[norm] = count
        final = norm if count == 1 else f"{norm}__{count}"
        final_map[orig] = final
    df = df.copy()
    df.columns = [final_map[c] for c in original_cols]
    return df, final_map

def update_agility_files() -> None:
    logger.info("=== Updating agility Excel files ===")

    mapping = map_compos_to_agility()
    if not mapping:
        logger.info("No compos files found; nothing to do for agility.")
        return

    backup_root = BASE_DIR / "backups" / dt.datetime.now().strftime("%Y%m%d-%H%M%S")

    for brand, (compos_path, agility_path) in sorted(mapping.items()):
        if agility_path is None or not agility_path.exists():
            logger.warning("Agility workbook missing for brand '%s'; skipping.", brand)
            continue

        logger.info("Processing agility: %s <- %s", agility_path.name, compos_path.name)

        try:
            # Read agility 'Raw Data'
            try:
                agility_all = pd.read_excel(agility_path, sheet_name=None)
                if "Raw Data" in agility_all:
                    agility_raw = agility_all["Raw Data"]
                else:
                    logger.warning("No 'Raw Data' sheet found in %s; creating one.", agility_path.name)
                    agility_raw = pd.DataFrame()
            except Exception as e:
                logger.warning("Failed reading sheets from %s: %s; proceeding with empty workbook.", agility_path.name, e)
                agility_all = {}
                agility_raw = pd.DataFrame()

            agility_norm, agility_map = _normalize_df(agility_raw)
            agility_cols_norm = list(agility_norm.columns)

            # Choose best compos sheet by overlap
            update_norm, sheet_name, match_count = choose_best_sheet_for_agility(compos_path, agility_cols_norm)
            logger.info("Chosen compos sheet '%s' with %d matching columns.", sheet_name, match_count)

            if agility_norm.empty:
                combined = update_norm
            else:
                common = [c for c in agility_norm.columns if c in update_norm.columns]
                if not common:
                    logger.error("No common columns for agility '%s' with compos '%s'; skipping.", agility_path.name, compos_path.name)
                    continue
                combined = pd.concat([agility_norm[common], update_norm[common]], ignore_index=True)

            if DROP_DUPLICATES:
                before = len(combined)
                combined = combined.drop_duplicates()
                logger.info("Dropped %d exact duplicate rows in agility.", before - len(combined))

            # Restore original column names/order for agility if available
            if agility_norm.shape[1] > 0:
                norm_to_orig = {v: k for k, v in agility_map.items()}
                combined = combined[restore_original_order_cols(combined, agility_norm)]
                combined.columns = [norm_to_orig.get(c, c) for c in combined.columns]

            # Put back into workbook
            agility_all["Raw Data"] = combined

            if BACKUP_ENABLED:
                backup_file(agility_path, backup_root)

            atomic_write_excel(agility_all, agility_path)
            logger.info("Updated agility workbook: %s (Raw Data rows: %d)", agility_path.name, len(combined))

        except Exception as e:
            logger.exception("Error updating agility for brand '%s': %s", brand, e)

# ---------------- Optional: key-based dedup (placeholder) ----------------
# If you later want to deduplicate by business keys instead of exact rows,
# implement a per-brand key map and use .drop_duplicates(subset=keys).

# ---------------- Orchestrator ----------------

def main(target_year: Optional[int] = None, target_month: Optional[int] = None):
    """
    Run both update processes for the target month (default: previous month from 'today').
    """
    if target_year is None or target_month is None:
        y, m = previous_month()
    else:
        y, m = target_year, target_month

    logger.info("Starting file update process for %s %d...", month_label(y, m), y)
    update_main_csv_files(y, m)
    update_agility_files()
    logger.info("File update process completed.")

if __name__ == "__main__":
    main()
