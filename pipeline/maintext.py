"""
Fetch full article text (maintext) from URLs using NewsPlease.
Only processes rows that don't already have content.
"""

import pandas as pd
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
from newsplease import NewsPlease


def _get_maintext_from_link(args):
    """Worker: fetch maintext from URL. Returns (idx, url, maintext, date, title)."""
    idx, url = args
    try:
        if not url or not str(url).strip().startswith("http"):
            return idx, url, None, None, None
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return idx, url, None, None, None
        article = NewsPlease.from_url(url)
        if article is None:
            return idx, url, None, None, None
        return idx, url, article.maintext, article.date_publish, article.title
    except Exception:
        return idx, url, None, None, None


def fetch_maintext_for_missing(df: pd.DataFrame, num_processes: int = 4, timeout: int = 20) -> pd.DataFrame:
    """
    For rows where content is missing/empty, fetch full article text from URL.
    Updates df in place and returns it.
    """
    for col in ["content", "Publication_Date", "Full_Title"]:
        if col not in df.columns:
            df[col] = None
        # Ensure object dtype to avoid FutureWarning when assigning str/datetime
        if df[col].dtype != object:
            df[col] = df[col].astype(object)

    # Find rows needing maintext
    mask = df["content"].isna() | (df["content"].astype(str).str.strip() == "")
    if "URL" not in df.columns:
        return df
    to_fetch = df.loc[mask].copy()
    if to_fetch.empty:
        return df

    indices = to_fetch.index.tolist()
    urls = to_fetch["URL"].tolist()
    tasks = list(zip(indices, urls))

    results = []
    success_count = 0
    total = len(tasks)
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = {executor.submit(_get_maintext_from_link, t): t for t in tasks}
        for future in as_completed(futures):
            try:
                r = future.result(timeout=timeout)
                results.append(r)
                if r[2] is not None:
                    success_count += 1
            except TimeoutError:
                idx, url = futures[future]
                results.append((idx, url, None, None, None))
            except Exception:
                idx, url = futures[future]
                results.append((idx, url, None, None, None))
            print(f"\rMaintext: {success_count}/{len(results)} articles with content", end="", flush=True)

    for idx, url, maintext, pub_date, full_title in results:
        df.at[idx, "content"] = maintext
        df.at[idx, "Publication_Date"] = pub_date
        df.at[idx, "Full_Title"] = full_title

    print(f"\rMaintext: {success_count}/{len(results)} articles with content")

    return df
