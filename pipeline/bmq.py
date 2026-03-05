"""
BMQ (Brand Media Quality) calculations.
Requires content column (full article text). Uses PageRank, term occurrence, Quality_Score.
"""

import math
import os
import re
from typing import Optional

import numpy as np
import pandas as pd
import requests

OPEN_PAGE_RANK_API_KEY = os.getenv("OPEN_PAGE_RANK_API_KEY")
TEXT_COLUMN = "content"  # Fallback to Snippet if content empty
TITLE_COLUMN = "Article"


def _truncate_link(link) -> str:
    try:
        m = re.search(r"(?:https?://)?(?:www\.)?([^/]+)", str(link))
        return m.group(1) if m else str(link)
    except Exception:
        return str(link)


def _get_page_rank(domain: str) -> Optional[dict]:
    try:
        r = requests.get(
            "https://openpagerank.com/api/v1.0/getPageRank",
            params={"domains[]": domain},
            headers={"API-OPR": OPEN_PAGE_RANK_API_KEY},
            timeout=10,
        )
        data = r.json()
        if "response" in data and data["response"]:
            return data["response"][0]
    except Exception:
        pass
    return None


def _count_query_occurrences(df: pd.DataFrame, query: str) -> pd.Series:
    q = query.lower()
    occurrences = []
    text_col = TEXT_COLUMN if TEXT_COLUMN in df.columns else "Snippet"
    title_col = TITLE_COLUMN if TITLE_COLUMN in df.columns else "Article"
    for _, row in df.iterrows():
        c = 0
        if pd.notna(row.get(title_col)):
            c += str(row[title_col]).lower().count(q)
        if pd.notna(row.get(text_col)):
            c += str(row[text_col]).lower().count(q)
        occurrences.append(c)
    return pd.Series(occurrences, index=df.index)


def _check_text_presence(df: pd.DataFrame, query: str, n_words: int) -> pd.Series:
    text_col = TEXT_COLUMN if TEXT_COLUMN in df.columns else "Snippet"
    title_col = TITLE_COLUMN if TITLE_COLUMN in df.columns else "Article"
    result = pd.Series(False, index=df.index)
    for idx, row in df.iterrows():
        text = row.get(text_col)
        if pd.notna(text) and str(text).strip():
            truncated = " ".join(str(text).split()[:n_words])
            if query.lower() in truncated.lower():
                result.at[idx] = True
    return result


def _check_title(df: pd.DataFrame, query: str) -> pd.Series:
    title_col = TITLE_COLUMN if TITLE_COLUMN in df.columns else "Article"
    if title_col not in df.columns:
        return pd.Series(False, index=df.index)
    return df[title_col].astype(str).str.contains(re.escape(query), case=False, na=False)


def _calculate_log_score(rank: float, max_rank: float = 100) -> float:
    if rank <= 0:
        return 0
    return round(100 * (1 - (math.log(rank + 1) / math.log(max_rank + 1))), 2)


def _log_scale_clipped_lower_better(v, a, b):
    x = np.clip(v, a, b)
    return 1 - (np.log(x) - np.log(a)) / (np.log(b) - np.log(a))


def _log_scale_clipped_higher_better(v, a, b):
    x = np.clip(v, a, b)
    return (np.log(x) - np.log(a)) / (np.log(b) - np.log(a))


def _linear_scale_clipped(v, a, b):
    x = np.clip(v, a, b)
    return (x - a) / (b - a)


def _calculate_article_score(P, R, n, Q):
    scaled_P = _log_scale_clipped_lower_better(P, 1, 10**8)
    scaled_R = _log_scale_clipped_lower_better(R, 1, 100)
    scaled_n = _log_scale_clipped_higher_better(n, 1, 30)
    scaled_Q = _linear_scale_clipped(Q, 1, 3)
    return 0.25 * scaled_P + 0.25 * scaled_R + 0.25 * scaled_n + 0.25 * scaled_Q


def _calculate_bmq_for_brand(df: pd.DataFrame, brand: str) -> pd.DataFrame:
    """Calculate BMQ for rows of a single brand."""
    df = df.copy()
    query = brand.lower()

    # Term occurrence count
    df["query_occurrences"] = _count_query_occurrences(df, query)

    # Term presence in first 100/200 words and title
    df["term_in_truncated_maintext_100"] = _check_text_presence(df, query, 100)
    df["term_in_truncated_maintext_200"] = _check_text_presence(df, query, 200)
    df["term_in_title"] = _check_title(df, query)

    # PageRank
    ranks = []
    for link in df["URL"]:
        domain = _truncate_link(link)
        pr = _get_page_rank(domain)
        r = pr.get("rank") if pr else None
        ranks.append(int(r) if r is not None else 10_000_000_000)
    df["Rank"] = ranks

    # Log_Rank (position-based: lower index = better)
    df["Log_Rank"] = [_calculate_log_score(i) / 100 for i in df.index]
    if not df.empty:
        df.iloc[0, df.columns.get_loc("Log_Rank")] = df.iloc[0]["Log_Rank"] + 1

    # Quality_Score: 3=title, 2=first 100 words, 1=first 200 words, 0=else
    df["Quality_Score"] = 0
    df.loc[df["term_in_title"], "Quality_Score"] = 3
    df.loc[(df["Quality_Score"] == 0) & df["term_in_truncated_maintext_100"], "Quality_Score"] = 2
    df.loc[(df["Quality_Score"] == 0) & df["term_in_truncated_maintext_200"], "Quality_Score"] = 1

    # BMQ
    bmq = []
    for idx in df.index:
        P = df.at[idx, "Rank"]
        R = df.at[idx, "Log_Rank"]
        n = df.at[idx, "query_occurrences"]
        Q = df.at[idx, "Quality_Score"]
        bmq.append(_calculate_article_score(P, R, max(1, n), max(1, Q)))
    df["BMQ"] = bmq

    return df


def run_bmq_calculations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate BMQ for all rows. Uses brand column for query term.
    Skips rows without content (BMQ set to None).
    """
    if not OPEN_PAGE_RANK_API_KEY:
        print("Warning: OPEN_PAGE_RANK_API_KEY not set. BMQ will use default rank.")

    if "BMQ" not in df.columns:
        df["BMQ"] = None

    # Calculate for rows with content or Snippet (Snippet as fallback)
    has_content = df["content"].notna() & (df["content"].astype(str).str.strip() != "")
    has_snippet = df["Snippet"].notna() & (df["Snippet"].astype(str).str.strip() != "")
    has_text = has_content | has_snippet
    # Only process rows that don't already have BMQ
    needs_bmq = df["BMQ"].isna()
    to_process = has_text & needs_bmq
    if not to_process.any():
        print("BMQ: all rows already have BMQ, skipping")
        return df

    brands = df.loc[to_process, "brand"].dropna().unique()
    for brand in brands:
        mask = to_process & (df["brand"] == brand)
        subset = df.loc[mask].copy()
        if subset.empty:
            continue
        try:
            subset = _calculate_bmq_for_brand(subset, str(brand))
            df.loc[mask, "BMQ"] = subset["BMQ"].values
            print(f"BMQ: {brand} - {len(subset)} new rows, range {subset['BMQ'].min():.4f}-{subset['BMQ'].max():.4f}")
        except Exception as e:
            print(f"BMQ error for {brand}: {e}")

    return df
