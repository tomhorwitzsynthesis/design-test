"""
Relevancy analysis for construction/real estate companies.
Uses OpenAI to determine if articles are substantively relevant.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

RELEVANCY_PROMPT = """You are an analyst tasked with determining whether news articles are relevant to a specific construction company, real estate developer, or property firm.

Your role is to assess each article and decide whether it contains meaningful, substantive content involving the company in question.

Your goal is to strictly exclude irrelevant or incidental content. Relevance does not require the entire article to focus on the company — but the company must be discussed in some non-trivial, non-incidental way.

Mark Relevant: true only if the article includes substantive information involving the company, even as part of a broader topic (e.g., the company is mentioned in connection with business operations, project developments, expansions, acquisitions, sustainability initiatives, partnerships, awards, market analysis, logistics parks, real estate projects, etc.).

First filter: Sometimes the company name is used in another context, like a person's name or unrelated entity. Be sure to first check if the article is about a construction/real estate company in the first place.

Mark Relevant: false if ANY of the following apply (be STRICT):
- The only mention is incidental (e.g., a location reference, address, or directory listing with no substantive discussion).
- The article is a listings/aggregator page of headlines or many stories.
- The article is a job posting, real estate listing, or non-news advertisement.
- The company appears only in a list of attendees, sponsors, or similar without substantive discussion.

Edge-case guidance:
- If the company is only in an address, venue list, or store directory → Relevant: false.
- If the company is the subject of a notable business development, project, or decision discussed in the article → Relevant: true.
- If ambiguous, prefer Relevant: false unless the text clearly discusses the company.

STRICT OUTPUT REQUIREMENTS:
- You MUST return a single-line JSON object with EXACT keys and types:
  {"relevant": boolean, "reason": string}
- Do not include any other text before or after the JSON.
- "relevant" must be a true JSON boolean (true or false), not a string.
- "reason" must be a brief justification (≤ 25 words), plain text."""


@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
def _analyze_relevancy(content: str, company_name: str, client: OpenAI) -> dict:
    if not content or not str(content).strip():
        return {"relevant": False, "reason": "No content provided"}
    content = str(content)[:3000]
    if len(str(content)) > 3000:
        content = content + "..."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": RELEVANCY_PROMPT},
            {"role": "user", "content": f"Company: {company_name}\n\nArticle content:\n{content}"},
        ],
        temperature=0.2,
        max_tokens=200,
    )
    output = (response.choices[0].message.content or "").strip()
    try:
        result = json.loads(output)
        relevant = result.get("relevant", False)
        if isinstance(relevant, str):
            relevant = relevant.lower() in ["true", "1", "yes"]
        reason = str(result.get("reason", "No reason"))
        return {"relevant": bool(relevant), "reason": reason}
    except json.JSONDecodeError:
        return {"relevant": "true" in output.lower(), "reason": "Parsed from text (JSON failed)"}


def run_relevancy_analysis(df: pd.DataFrame, max_workers: int = 8) -> pd.DataFrame:
    """
    Run relevancy analysis on rows that have content (or Snippet as fallback).
    Updates df with relevancy and relevancy_reason columns.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not set. Skipping relevancy analysis.")
        if "relevancy" not in df.columns:
            df["relevancy"] = None
        if "relevancy_reason" not in df.columns:
            df["relevancy_reason"] = "Skipped (no API key)"
        return df

    client = OpenAI(api_key=api_key)

    if "relevancy" not in df.columns:
        df["relevancy"] = None
    if "relevancy_reason" not in df.columns:
        df["relevancy_reason"] = None

    # Use content if available, else Snippet
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
        # Skip rows that already have relevancy assigned
        r = row.get("relevancy")
        if pd.notna(r) and r is not None and str(r).lower() in ("true", "false"):
            continue
        text = get_text(row)
        brand = row.get("brand", "")
        if text and brand:
            to_analyze.append((idx, text, str(brand)))

    if not to_analyze:
        return df

    def process_batch(batch):
        return [(idx, _analyze_relevancy(text, brand, client)) for idx, text, brand in batch]

    batch_size = max(1, len(to_analyze) // max_workers)
    batches = [to_analyze[i : i + batch_size] for i in range(0, len(to_analyze), batch_size)]

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_batch, b) for b in batches]
        for future in as_completed(futures):
            for idx, result in future.result():
                df.at[idx, "relevancy"] = result["relevant"]
                df.at[idx, "relevancy_reason"] = result["reason"]

    print(f"Relevancy: analyzed {len(to_analyze)} articles")
    return df
