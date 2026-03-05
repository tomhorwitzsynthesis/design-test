import pandas as pd
import requests
import os
from newsplease import NewsPlease
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
from universal.utils.folders import get_dashboard_data_path


def _get_maintext_from_link(row):
    """
    Extract maintext, publication date, and title from a URL.
    This function runs in a ProcessPoolExecutor worker, so we call NewsPlease directly.
    The ProcessPoolExecutor handles parallelization and timeout at a higher level.
    """
    idx, url = row

    try:
        # Quick check if URL is accessible
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print(f"[{idx}] Skipping (status {response.status_code})")
            return idx, url, None, None, None

        # Call NewsPlease directly - ProcessPoolExecutor already handles parallelization
        # The timeout in _gather_maintext will catch if this takes too long
        article = NewsPlease.from_url(url)
        
        if article is None:
            print(f"[{idx}] NewsPlease returned None ❌")
            return idx, url, None, None, None

        print(f"[{idx}] Success ✅")
        return idx, url, article.maintext, article.date_publish, article.title

    except requests.exceptions.Timeout:
        print(f"[{idx}] Request timeout ⚠️ Skipping")
        return idx, url, None, None, None

    except Exception as e:
        print(f"[{idx}] NewsPlease error ❌: {type(e).__name__} - {e}")
        return idx, url, None, None, None



def save_maintext(label="", year: int = None, month: int = None, num_processes: int = 1, timeout: int = 15):

    if year is None or month is None:
        raise ValueError("Year and month are required")

    output_dir = get_dashboard_data_path(year, month, "pr")
    master_file_path = os.path.join(output_dir, "pr_master_data.xlsx")

    if not os.path.exists(master_file_path):
        raise FileNotFoundError(f"Master PR file not found: {master_file_path}")
    
    master_file = pd.read_excel(master_file_path)

    results = _gather_maintext(master_file, num_processes, timeout)
    
    if not results:
        print(f"[{label}] No results to save.")
        return

    merged_rows = []
    for idx, url, maintext, pub_date, full_title in results:
        row_original = master_file.iloc[[idx]].reset_index(drop=True)
        row_extracted = pd.DataFrame(
            [[maintext, pub_date, full_title]],
            columns=['content', 'Publication_Date', 'Full_Title']
        )
        row_merged = pd.concat([row_original, row_extracted], axis=1)
        merged_rows.append(row_merged)

    df_final = pd.concat(merged_rows, ignore_index=True)

    print(f"Final dataframe: {df_final}")

    # Remove all rows where content is None
    # Length before row removal
    length_before = len(df_final)
    print(f"Length before row removal: {len(df_final)}")
    df_final = df_final[df_final['content'].notna()]
    print(f"Length after row removal: {len(df_final)}")
    length_after = len(df_final)
    print(f"Maintext retrieval percentage: {(length_after - length_before) / length_before * 100:.2f}%")

    # Save to Excel
    df_final.to_excel(master_file_path, index=False)

    # Print success rate
    total = len(df_final)
    success = df_final['content'].notnull().sum()
    percent = (success / total) * 100
    print(f"[{label}] {success}/{total} rows succeeded ({percent:.1f}%)")


def _gather_maintext(df_subset, num_processes=4, timeout=15):
    results = []
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        futures = {
            executor.submit(_get_maintext_from_link, (idx, row['URL'])): idx
            for idx, row in df_subset.iterrows()
        }
        for future in as_completed(futures):
            try:
                results.append(future.result(timeout=timeout))
                # Print URL of the result
                print(f"Result Success: {results[-1][1]}")
            except TimeoutError:
                idx = futures[future]
                url = df_subset.loc[idx, 'URL']
                print(f"Timeout: {url}")
                results.append((idx, url, None, None, None))
            except Exception as e:
                idx = futures[future]
                url = df_subset.loc[idx, 'URL']
                print(f"Error: {e}")
                results.append((idx, url, None, None, None))

    return results