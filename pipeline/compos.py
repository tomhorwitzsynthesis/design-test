"""
Compos / brand archetype assignment.
Uses OpenAI to assign one of 16 archetypes to each article based on archetype_pr.txt.
"""

import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt

# Archetypes from archetype_pr.txt
ARCHETYPES = [
    "The Futurist",
    "The Eco Warrior",
    "The Technologist",
    "The Mentor",
    "The Collaborator",
    "The People's Champion",
    "The Nurturer",
    "The Simplifier",
    "The Expert",
    "The Value-Seeker",
    "The Personalizer",
    "The Accelerator",
    "The Guardian",
    "The Principled",
    "The Jet-Setter",
    "The Optimizer",
]

COMPOS_PROMPT = """As a senior Public Relations and Branding Communication expert you are interested in how companies are positioned by their social media posts.
Your task will be to analyze social media posts and assign the best-fitting archetype to each article, based on the following framework:

1. The Futurist (innovative, disruptive, pioneering, visionary)
2. The Eco Warrior (ecological, sustainable, environmental, renewable)
3. The Technologist (technological, automated, smart, integrated)
4. The Mentor (guiding, insightful, informative, supportive)
5. The Collaborator (community, collaborative, teamwork, partner)
6. The People's Champion (democratic, inclusive, empowering, friendly)
7. The Nurturer (caring, understanding, nurturing, encouraging)
8. The Simplifier (simple, easy, simplifying, effortless)
9. The Expert (intelligent, expert, specialized, scientific)
10. The Value-Seeker (cost-effective, affordable, economical, low-cost)
11. The Personalizer (adaptive, tailored, personalized, customized)
12. The Accelerator (agile, instant, fast, enabling)
13. The Guardian (safe, secure, dependable, encrypted)
14. The Principled (honest, transparent, fair, responsible)
15. The Jet-Setter (global, international, largest, leading)
16. The Optimizer (efficient, optimized, streamlined, frictionless)

Based on the article content, choose the ONE archetype that best reflects how the company is portrayed or the values communicated.

Please make sure to always respond in the following format:

Top Archetype: [Top Archetype]

Use the exact archetype name from the list above (e.g. "The Futurist", "The Eco Warrior")."""


def _parse_archetype_response(output: str) -> str:
    """Parse 'Top Archetype: The Futurist' format from LLM response."""
    output = (output or "").strip()
    # Match "Top Archetype: ..." pattern
    m = re.search(r"Top\s+Archetype\s*:\s*(.+)", output, re.IGNORECASE)
    if m:
        arch = m.group(1).strip()
        for a in ARCHETYPES:
            if a.lower() == arch.lower():
                return a
        return arch  # Return as-is if not in list (might be variant)
    # Fallback: check if any archetype appears in output
    for a in ARCHETYPES:
        if a.lower() in output.lower():
            return a
    return ""


@retry(wait=wait_exponential(multiplier=1, min=1, max=30), stop=stop_after_attempt(3))
def _assign_archetype(content: str, client: OpenAI) -> str:
    if not content or not str(content).strip():
        return ""
    content = str(content)[:2500]
    if len(str(content)) > 2500:
        content = content + "..."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": COMPOS_PROMPT},
            {"role": "user", "content": f"Article:\n{content}"},
        ],
        temperature=0.2,
        max_tokens=80,
    )
    output = (response.choices[0].message.content or "").strip()
    return _parse_archetype_response(output)


def run_compos_analysis(df: pd.DataFrame, max_workers: int = 8) -> pd.DataFrame:
    """
    Assign Top Archetype to each row based on article content.
    Uses content column; falls back to Snippet if content empty.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not set. Skipping compos/archetype analysis.")
        if "Top Archetype" not in df.columns:
            df["Top Archetype"] = ""
        return df

    client = OpenAI(api_key=api_key)

    if "Top Archetype" not in df.columns:
        df["Top Archetype"] = ""

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
        # Skip rows that already have Top Archetype assigned
        arch = row.get("Top Archetype")
        if pd.notna(arch) and str(arch).strip():
            continue
        text = get_text(row)
        if text:
            to_analyze.append((idx, text))

    if not to_analyze:
        return df

    def process_one(args):
        idx, text = args
        arch = _assign_archetype(text, client)
        return idx, arch

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one, t): t for t in to_analyze}
        for future in as_completed(futures):
            try:
                idx, arch = future.result()
                df.at[idx, "Top Archetype"] = arch
            except Exception:
                idx = futures[future][0]
                df.at[idx, "Top Archetype"] = ""

    assigned = (df["Top Archetype"] != "").sum()
    print(f"Compos: assigned archetypes to {assigned}/{len(to_analyze)} articles")
    return df
