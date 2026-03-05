"""
Sentiment analysis for news articles about construction/real estate companies.
Uses OpenAI to assign Positive, Negative, or Neutral based on how the article talks about the company.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

SENTIMENT_PROMPT = """You are an analyst assessing the sentiment of news articles about a specific company (construction, real estate, or property firm).

Your task: Determine how the article talks about the company. Assign exactly one of: Positive, Negative, or Neutral.

- Positive: The article portrays the company favorably (e.g., success, growth, awards, positive developments, praise).
- Negative: The article portrays the company unfavorably (e.g., criticism, failures, controversies, negative outcomes).
- Neutral: The article is factual, balanced, or does not clearly lean positive or negative.

STRICT OUTPUT REQUIREMENTS:
- You MUST return a single-line JSON object with EXACT key: {"sentiment": "Positive" | "Negative" | "Neutral"}
- Do not include any other text before or after the JSON.
- Use exactly one of: Positive, Negative, Neutral."""


@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
def _analyze_sentiment(content: str, company_name: str, client: OpenAI) -> str:
    if not content or not str(content).strip():
        return "Neutral"
    content = str(content)[:3000]
    if len(str(content)) > 3000:
        content = content + "..."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SENTIMENT_PROMPT},
            {"role": "user", "content": f"Company: {company_name}\n\nArticle content:\n{content}"},
        ],
        temperature=0.2,
        max_tokens=50,
    )
    output = (response.choices[0].message.content or "").strip()
    try:
        result = json.loads(output)
        s = str(result.get("sentiment", "Neutral")).strip()
        if s in ("Positive", "Negative", "Neutral"):
            return s
        return "Neutral"
    except json.JSONDecodeError:
        out_lower = output.lower()
        if "positive" in out_lower:
            return "Positive"
        if "negative" in out_lower:
            return "Negative"
        return "Neutral"


def run_sentiment_analysis(df: pd.DataFrame, max_workers: int = 8) -> pd.DataFrame:
    """
    Run sentiment analysis on rows that have content (or Snippet as fallback).
    Updates df with sentiment column (Positive, Negative, or Neutral).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not set. Skipping sentiment analysis.")
        if "Sentiment" not in df.columns:
            df["Sentiment"] = "Neutral"
        return df

    client = OpenAI(api_key=api_key)

    if "Sentiment" not in df.columns:
        df["Sentiment"] = None

    def get_text(row):
        c = row.get("content")
        if pd.notna(c) and str(c).strip():
            return str(c)
        s = row.get("Snippet")
        if pd.notna(s) and str(s).strip():
            return str(s)
        return None

    to_analyze = []
    for idx, row in df.iterrows():
        # Skip rows that already have sentiment assigned
        s = row.get("Sentiment")
        if pd.notna(s) and str(s).strip() and str(s).strip() in ("Positive", "Negative", "Neutral"):
            continue
        text = get_text(row)
        brand = row.get("brand", "")
        if text and brand:
            to_analyze.append((idx, text, str(brand)))

    if not to_analyze:
        return df

    def process_batch(batch):
        return [(idx, _analyze_sentiment(text, brand, client)) for idx, text, brand in batch]

    batch_size = max(1, len(to_analyze) // max_workers)
    batches = [to_analyze[i : i + batch_size] for i in range(0, len(to_analyze), batch_size)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_batch, b) for b in batches]
        for future in as_completed(futures):
            for idx, sentiment in future.result():
                df.at[idx, "Sentiment"] = sentiment

    print(f"Sentiment: analyzed {len(to_analyze)} articles")
    return df
