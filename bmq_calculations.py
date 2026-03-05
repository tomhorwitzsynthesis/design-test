import os
import re
import math
import numpy as np
import pandas as pd
import requests
import sys

REPO_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from universal.config.config import CONFIG, MEDIA_TYPES

OPEN_PAGE_RANK_API_KEY = os.getenv("OPEN_PAGE_RANK_API_KEY")


# ============================================================
# SUPPORT FUNCTIONS (SELF-CONTAINED)
# ============================================================

def _load_file(path, sheet):
    if path.endswith(".csv"):
        return pd.read_csv(path)
    if path.endswith(".xlsx"):
        try:
            return pd.read_excel(path, sheet_name=sheet)
        except Exception as e:
            print(f"    Error reading Excel file: {e}")
            print(f"    Available sheets (if any):")
            try:
                xl_file = pd.ExcelFile(path)
                print(f"      {xl_file.sheet_names}")
            except:
                pass
            raise
    raise ValueError(f"Unsupported file format: {path}")


def _count_query_occurrences(df, query):
    occurrences = []
    q = query.lower()
    print(f"Query: {q}")
    for _, row in df.iterrows():
        c = 0
        if pd.notna(row.get("Headline")):
            c += row["Headline"].lower().count(q)
        if pd.notna(row.get(MEDIA_TYPES["pr"]["text_column"])):
            c += row[MEDIA_TYPES["pr"]["text_column"]].lower().count(q)
        else:
            print(f"No text found")
        print(f"Count: {c}")
        occurrences.append(c)
    print(f"Occurrences: {occurrences}")
    return pd.Series(occurrences)


def _check_text_presence_100(df, brand):
    df["term_in_truncated_maintext_100"] = False
    for idx, row in df.iterrows():
        text = row.get(MEDIA_TYPES["pr"]["text_column"])
        if pd.notna(text):
            truncated = " ".join(text.split()[:100])
            if brand.lower() in truncated.lower():
                df.at[idx, "term_in_truncated_maintext_100"] = True
    return df


def _check_text_presence_200(df, brand):
    df["term_in_truncated_maintext_200"] = False
    for idx, row in df.iterrows():
        text = row.get(MEDIA_TYPES["pr"]["text_column"])
        if pd.notna(text):
            truncated = " ".join(text.split()[:200])
            if brand.lower() in truncated.lower():
                df.at[idx, "term_in_truncated_maintext_200"] = True
    return df


def _check_title(df, brand):
    df["term_in_title"] = df["Headline"].str.contains(brand, case=False, na=False)
    return df


def _truncate_link(link):
    try:
        m = re.search(r"(?:https?://)?(?:www\.)?([^/]+)", link)
        if m:
            return m.group(1)
        return link
    except:
        return link


def _get_page_rank(domain):
    try:
        r = requests.get(
            "https://openpagerank.com/api/v1.0/getPageRank",
            params={"domains[]": domain},
            headers={"API-OPR": OPEN_PAGE_RANK_API_KEY},
            timeout=10
        )
        return r.json()["response"][0]
    except:
        return None


def _calculate_log_score(rank, max_rank=100):
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


def _assign_quality_score(df):
    df["Quality_Score"] = 0
    df.loc[df["term_in_title"] == True, "Quality_Score"] = 3
    df.loc[(df["Quality_Score"] == 0) & (df["term_in_truncated_maintext_100"] == True), "Quality_Score"] = 2
    df.loc[(df["Quality_Score"] == 0) & (df["term_in_truncated_maintext_200"] == True), "Quality_Score"] = 1
    return df

# ============================================================
# QUALITY + RANKING PROCESS
# ============================================================

def calculate_bmq(df, brand):

    df.reset_index(drop=True, inplace=True)

    query_name = next((b.query_name for b in CONFIG.brands if b.name == brand), None)
    if query_name is None:
        print(f"Query name not found for brand {brand}")
        return None
    print(f"Query name: {query_name} for brand {brand}")

    print(f"Starting calculate_bmq for {len(df)} rows and brand {brand}")
    df["query_occurrences"] = _count_query_occurrences(df, query_name)
    print(f"Query occurrences: {df['query_occurrences']}")

    # --- Term checks ---
    print(f"    Checking term presence in text (100, 200 words) and title...")
    df = _check_text_presence_100(df, query_name)
    df = _check_text_presence_200(df, query_name)
    df = _check_title(df, query_name)
    print(f"Term in title: {df['term_in_title'].sum()} rows for brand {brand}")
    print(f"Term in first 100 words: {df['term_in_truncated_maintext_100'].sum()} rows for brand {brand}")
    print(f"Term in first 200 words: {df['term_in_truncated_maintext_200'].sum()} rows for brand {brand}")

    df = df.reset_index(drop=True)

    # --- PageRank ---
    print(f"Fetching PageRank for {len(df)} URLs for brand {brand}")
    ranks = []
    for i, link in enumerate(df["URL"], 1):
        if i % 10 == 0 or i == 1:
            print(f"      Progress: {i}/{len(df)} URLs processed...", end='\r')
        domain = _truncate_link(link)
        pr = _get_page_rank(domain)
        r = pr.get("rank") if pr else None
        ranks.append(int(r) if r is not None else 10_000_000_000)
    
    print(f"✓ PageRank complete: {len(ranks)} ranks fetched for brand {brand}")
    print(f"Ranks: {ranks}")
    df["Rank"] = ranks

    # --- Log Rank ---
    print(f"Calculating Log_Rank for brand {brand}")
    df["Log_Rank"] = [_calculate_log_score(i) / 100 for i in df.index]
    if not df.empty:
        df.at[0, "Log_Rank"] += 1
    print(f"Log_Rank: {df['Log_Rank']}")

    df = _assign_quality_score(df)
    print(f"Quality scores assigned: {df['Quality_Score'].value_counts().to_dict()} for brand {brand}")

    # --- BMQ Calculation for A Only ---
    print(f"Calculating BMQ scores for brand {brand}")
    BMQ = []
    for idx in df.index:
        P = df.at[idx, "Rank"]
        R = df.at[idx, "Log_Rank"]
        n = df.at[idx, "query_occurrences"]
        Q = df.at[idx, "Quality_Score"]
        print(f"P: {P}, R: {R}, n: {n}, Q: {Q}")
        BMQ.append(_calculate_article_score(P, R, n, Q))
    print(f"BMQ: {BMQ}")
    df["BMQ"] = BMQ
    print(f"BMQ range: {min(BMQ):.4f} - {max(BMQ):.4f} for brand {brand}")

    return df

if __name__ == "__main__":
    df = pd.read_excel("data/dashboard_data/one_shot/pr/pr_master_data.xlsx")
    df = df[df["company"] == "Swedbank"]
    print(df.head())
    df = calculate_bmq(df, "Swedbank")