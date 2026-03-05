import os
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

from typing import Optional
from universal.config.config import CONFIG, MEDIA_TYPES
from universal.utils.folders import get_dashboard_data_path


logger = logging.getLogger(__name__)
client = OpenAI(
    api_key=CONFIG.llm.openai_api_key) if CONFIG.llm.openai_api_key else None

RELEVANCY_PROMPT = """You are an analyst tasked with determining whether news articles are relevant to a specific bank.

Your role is to assess each article and decide whether it contains meaningful, substantive content involving the bank in question.

Your goal is to strictly exclude irrelevant or incidental content. Relevance does not require the entire article to focus on the bank — but the bank must be discussed in some non-trivial, non-incidental way.

Mark Relevant: true only if the article includes substantive information involving the bank, even as part of a broader topic (e.g., the bank is mentioned in connection with business operations, expansions, closures, regulations, management actions, sales events, saf  ety incidents, legal disputes, discounts etc.).

First filter: Sometimes the name of the bank is used in another context, like the name of a person or other entity. Be sure to first check if the article is about a bank in the first place.

Mark Relevant: false if ANY of the following apply (be STRICT):
- The only mention is incidental (e.g., a location reference in a crime/police report where nothing actually happened in the bank, weather update, transit notice, travel directions).
- The article is a listings/aggregator page of headlines or many stories.
- The article is an apartment listing, or non-news advertisement.

Edge-case guidance:
- If the bank is only in an address, venue list, or store directory → Relevant: false.
- If the bank is the site of a notable incident/crime or business decision discussed in the article → Relevant: true.
- If ambiguous, prefer Relevant: false unless the text clearly discusses the bank.

STRICT OUTPUT REQUIREMENTS:
- You MUST return a single-line JSON object with EXACT keys and types:
  {"relevant": boolean, "reason": string}
- Do not include any other text before or after the JSON.
- "relevant" must be a true JSON boolean (true or false), not a string.
- "reason" must be a brief justification (≤ 25 words), plain text."""


@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(5))
def _analyze_article_relevancy(content: str, company_name: str) -> dict:
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    if not content or not content.strip():
        return {"relevant": False, "reason": "No content provided"}
    max_chars = 3000
    if len(content) > max_chars:
        content = content[:max_chars] + "..."
    user_message = f"Company: {company_name}\n\nArticle content:\n{content}"
    response = client.chat.completions.create(
        model=CONFIG.llm.default_model,
        messages=[{"role": "system", "content": RELEVANCY_PROMPT},
                  {"role": "user", "content": user_message}],
        temperature=0.2,
        max_tokens=200,
    )
    output = (response.choices[0].message.content or "").strip()
    try:
        result = json.loads(output)
        if not isinstance(result, dict):
            raise ValueError("Response is not a dictionary")
        if "relevant" not in result or "reason" not in result:
            raise ValueError("Missing required fields in response")
        relevant = result["relevant"]
        if isinstance(relevant, str):
            relevant = relevant.lower() in ["true", "1", "yes"]
        elif not isinstance(relevant, bool):
            relevant = bool(relevant)
        reason = str(result["reason"]) if result.get(
            "reason") else "No reason provided"
        return {"relevant": relevant, "reason": reason}
    except json.JSONDecodeError:
        if "true" in output.lower():
            return {"relevant": True, "reason": "Parsed from text (JSON failed)"}
        return {"relevant": False, "reason": "Parsed from text (JSON failed)"}


def analyze_relevancy_for_month(year: int, month: int, output_folder: Optional[str] = None) -> Optional[str]:
    logger.info(f"Starting PR relevancy analysis for {year}-{month:02d}")
    pr_dir = get_dashboard_data_path(year, month, "pr")
    master_file = os.path.join(pr_dir, "pr_master_data.xlsx")
    if not os.path.exists(master_file):
        logger.error(f"Master PR file not found: {master_file}")
        return None
    try:
        excel_file = pd.ExcelFile(master_file)
        available_sheets = excel_file.sheet_names
        sheet_name = "Master Data" if "Master Data" in available_sheets else available_sheets[
            0]
        df = pd.read_excel(master_file, sheet_name=sheet_name)
        if "relevancy" in df.columns and "relevancy_reason" in df.columns:
            logger.info(
                "Relevancy analysis already exists. Skipping analysis.")
            return master_file
        text_column = MEDIA_TYPES["pr"]["text_column"]
        brand_column = MEDIA_TYPES["pr"]["brand_column"]
        if text_column not in df.columns or brand_column not in df.columns:
            logger.error("PR data missing required columns.")
            return None
        articles_to_analyze = []
        for index, row in df.iterrows():
            content = row[text_column]
            company = row[brand_column]
            if pd.isna(content) or not str(content).strip():
                continue
            articles_to_analyze.append((index, str(content), str(company)))
        logger.info(
            f"Analyzing relevancy for {len(articles_to_analyze)} articles")
        if not articles_to_analyze:
            logger.warning("No articles to analyze")
            return master_file
        df["relevancy"] = False
        df["relevancy_reason"] = "Not analyzed"
        max_workers = CONFIG.llm.max_workers
        batch_size = max(1, len(articles_to_analyze) // max_workers)
        batches = [articles_to_analyze[i:i + batch_size]
                   for i in range(0, len(articles_to_analyze), batch_size)]
        all_results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(lambda b: [(idx, _analyze_article_relevancy(
                c, comp)) for idx, c, comp in b], batch): i for i, batch in enumerate(batches)}
            for future in as_completed(futures):
                all_results.extend(future.result())
        for index, result in all_results:
            df.at[index, "relevancy"] = result["relevant"]
            df.at[index, "relevancy_reason"] = result["reason"]
        with pd.ExcelWriter(master_file, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        logger.info(
            f"Updated master PR file with relevancy analysis: {master_file}")
        return master_file
    except Exception as e:
        logger.error(f"Error in relevancy analysis: {e}")
        return None
