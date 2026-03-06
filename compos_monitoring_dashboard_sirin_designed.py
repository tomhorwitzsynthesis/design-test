"""
Monitoring Dashboard — Synthesis Design Reference
Swiss Editorial Precision. Black, white, gray + single green accent (#2FCC6E).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import re
from datetime import datetime, timedelta
from calendar import month_name

# ─── Data Configuration ─────────────────────────────────────────────────────
DATA_FOLDER = "data sirin"
DATA_FILE = os.path.join(DATA_FOLDER, "data.xlsx")

DISPLAY_NAME_MAP = {
    "sirin": "SIRIN",
    "darnu": "Darnu",
    "eika": "Eika",
    "kapitel": "Kapitel",
    "piche": "Piche",
    "restate": "Restate",
    "favorte": "Favorte",
    "park rae": "Park Rae",
    "vgp": "VGP",
}

available_months = [
    (2025, 1), (2025, 2), (2025, 3), (2025, 4), (2025, 5), (2025, 6),
    (2025, 7), (2025, 8), (2025, 9), (2025, 10), (2025, 11), (2025, 12),
    (2026, 1), (2026, 2),
]

# Synthesis Design Reference — Chart Colors
COLOR_BG = "#FFFFFF"
COLOR_SURFACE = "#F7F7F7"
COLOR_BORDER = "#E2E2E2"
COLOR_BORDER_STRONG = "#C0C0C0"
COLOR_TEXT_PRIMARY = "#0A0A0A"
COLOR_TEXT_BODY = "#1A1A1A"
COLOR_TEXT_MUTED = "#888888"
COLOR_ACCENT = "#2FCC6E"
COLOR_DATA_1 = "#0A0A0A"
COLOR_DATA_2 = "#888888"
COLOR_DATA_3 = "#C0C0C0"
COLOR_DATA_4 = "#2FCC6E"
COLOR_DATA_5 = "#E2E2E2"
COLOR_POSITIVE = "#2FCC6E"
COLOR_NEGATIVE = "#0A0A0A"
COLOR_WARNING = "#D4A017"

# Plotly layout template (Synthesis styling)
# Extra top margin to prevent title/legend overlap
PLOTLY_LAYOUT = dict(
    font=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=12, color=COLOR_TEXT_BODY),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=48, r=48, t=72, b=48),
    xaxis=dict(
        gridcolor=COLOR_BORDER,
        gridwidth=1,
        zeroline=False,
        linecolor=COLOR_BORDER_STRONG,
        linewidth=1,
        tickfont=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=11, color=COLOR_TEXT_MUTED),
        title_font=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=11, color=COLOR_TEXT_MUTED),
    ),
    yaxis=dict(
        gridcolor=COLOR_BORDER,
        gridwidth=1,
        zeroline=False,
        linecolor=COLOR_BORDER_STRONG,
        linewidth=1,
        tickfont=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=11, color=COLOR_TEXT_MUTED),
        title_font=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=11, color=COLOR_TEXT_MUTED),
    ),
    showlegend=True,
    legend=dict(
        font=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=11, color=COLOR_TEXT_MUTED),
        orientation="h",
        yanchor="bottom",
        y=1.12,
        xanchor="left",
        x=0,
    ),
    hoverlabel=dict(
        bgcolor=COLOR_BG,
        bordercolor=COLOR_BORDER,
        font=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=12),
    ),
)


def inject_synthesis_css():
    """Inject Synthesis Design Reference CSS."""
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,700;0,9..40,900&display=swap" rel="stylesheet">
        <style>
        :root {
            --color-bg: #FFFFFF;
            --color-surface: #F7F7F7;
            --color-border: #E2E2E2;
            --color-border-strong: #C0C0C0;
            --color-text-primary: #0A0A0A;
            --color-text-body: #1A1A1A;
            --color-text-muted: #888888;
            --color-accent: #2FCC6E;
            --radius-md: 4px;
            --space-2: 8px;
            --space-3: 12px;
            --space-5: 24px;
            --space-6: 32px;
            --space-7: 48px;
            --space-8: 64px;
        }
        .stApp, .stApp *, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] *,
        h1, h2, h3, h4, h5, h6, p, span, div, label, a, input, select, button {
            font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        }
        .stApp { overflow-x: hidden; }
        .synthesis-header-wrapper {
            width: 100vw; max-width: 100vw;
            margin-left: calc(50% - 50vw); margin-right: calc(50% - 50vw);
            background: var(--color-bg);
            border-bottom: 1px solid var(--color-border-strong);
            margin-bottom: 32px; margin-top: 0;
        }
        .synthesis-header-inner {
            max-width: 1440px; margin: 0 auto;
            padding: 24px clamp(24px, 4vw, 64px);
            display: flex; justify-content: space-between; align-items: center;
        }
        .synthesis-dash { max-width: 1440px; margin: 0 auto; padding: 32px clamp(24px, 4vw, 64px); }
        .synthesis-label {
            font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 11px; font-weight: 500; text-transform: uppercase;
            letter-spacing: 0.08em; color: var(--color-text-muted);
        }
        .synthesis-section-header { margin-bottom: 48px; }
        .synthesis-section-meta { margin-bottom: 12px; }
        .synthesis-section-title {
            font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 1.125rem; font-weight: 700;
            color: var(--color-text-primary); line-height: 1.1;
            margin: 0 0 24px 0;
        }
        .synthesis-divider {
            border: none; border-top: 1px solid var(--color-border); margin: 0;
        }
        .synthesis-stat-card {
            background: var(--color-bg); border: 1px solid var(--color-border);
            border-radius: var(--radius-md); padding: 32px 32px 24px;
            display: flex; flex-direction: column; gap: 8px;
        }
        .synthesis-stat-value {
            font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: clamp(2rem, 4vw, 3.5rem); font-weight: 900;
            color: var(--color-text-primary); line-height: 1.0;
            letter-spacing: -0.02em;
        }
        .synthesis-stat-delta { font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 13px; color: var(--color-text-muted); }
        .synthesis-stat-delta.positive { color: var(--color-accent); }
        .synthesis-chart-block {
            background: var(--color-bg); border: 1px solid var(--color-border);
            border-radius: var(--radius-md); padding: 32px;
        }
        .synthesis-chart-caption {
            font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 11px; color: #BBBBBB; margin: 12px 0 0 0; letter-spacing: 0.02em;
        }
        .synthesis-article-card {
            border: 1px solid var(--color-border); border-radius: var(--radius-md);
            padding: 12px 16px; margin-bottom: 8px; background: var(--color-surface);
        }
        .synthesis-article-card a {
            font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: var(--color-text-primary); text-decoration: none; font-weight: 500;
        }
        .synthesis-article-card a:hover { color: var(--color-accent); }
        /* Sidebar — Synthesis styling */
        [data-testid="stSidebar"] {
            background: var(--color-surface);
            border-right: 1px solid var(--color-border);
        }
        [data-testid="stSidebar"] * {
            font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            font-size: 11px !important; font-weight: 500 !important; text-transform: uppercase;
            letter-spacing: 0.08em; color: var(--color-text-muted) !important;
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] label {
            font-size: 11px; font-weight: 500; text-transform: uppercase;
            letter-spacing: 0.06em; color: var(--color-text-muted);
        }
        [data-testid="stSidebar"] [data-testid="stSelectbox"] div {
            border-color: var(--color-border);
            border-radius: 4px;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 24px; padding-left: 24px; padding-right: 24px;
        }
        /* Streamlit markdown / body text */
        [data-testid="stMarkdown"], [data-testid="stMarkdown"] *, [data-testid="stMarkdown"] p, [data-testid="stMarkdown"] li, [data-testid="stMarkdown"] a {
            font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        }
        /* Tabs */
        [data-baseweb="tab-list"] *, [data-baseweb="tab"] * {
            font-family: 'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def section_header(label: str, title: str):
    """Render Synthesis section header."""
    st.markdown(
        f"""
        <div class="synthesis-section-header">
            <div class="synthesis-section-meta">
                <span class="synthesis-label">≡ {label}</span>
            </div>
            <h2 class="synthesis-section-title">{title}</h2>
            <hr class="synthesis-divider">
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_card(label: str, value: str, delta: str = None, positive: bool = False):
    """Render Synthesis stat card."""
    delta_class = " synthesis-stat-delta positive" if positive else ""
    delta_html = f'<div class="synthesis-stat-delta{delta_class}">{delta}</div>' if delta else ""
    st.markdown(
        f"""
        <div class="synthesis-stat-card">
            <span class="synthesis-label">{label}</span>
            <div class="synthesis-stat-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def extract_date(snippet):
    """Extract date from snippet string."""
    today = pd.Timestamp.today()
    first_day_this_month = pd.Timestamp(today.year, today.month, 1)
    reference_date = first_day_this_month - pd.Timedelta(days=1)

    if "day ago" in snippet or "days ago" in snippet:
        match = re.search(r"(\d+)\s+day[s]?\s+ago", snippet)
        if match:
            days_ago = int(match.group(1))
            return (reference_date - timedelta(days=days_ago)).strftime("%m/%d/%Y")
    elif "hour ago" in snippet or "hours ago" in snippet:
        match = re.search(r"(\d+)\s+hour[s]?\s+ago", snippet)
        if match:
            return (reference_date - timedelta(hours=int(match.group(1)))).strftime("%m/%d/%Y")

    match = re.match(r"([A-Za-z]{3} \d{1,2}, \d{4})", snippet)
    if match:
        try:
            extracted_date = pd.to_datetime(match.group(1), format="%b %d, %Y")
            return extracted_date.strftime("%m/%d/%Y")
        except Exception:
            return None
    return None


# ─── Page Config ──────────────────────────────────────────────────────────
st.set_page_config(page_title="Monitoring Dashboard", layout="wide", initial_sidebar_state="expanded")
inject_synthesis_css()

# ─── Sidebar: Date Range ──────────────────────────────────────────────────
st.sidebar.markdown("### Select Date Range")
month_labels = [f"{month_name[m]} {y}" for y, m in available_months]
label_to_date = {label: (y, m) for label, (y, m) in zip(month_labels, available_months)}

start_label = st.sidebar.selectbox("Start Month", month_labels, index=0)
end_label = st.sidebar.selectbox("End Month", month_labels, index=len(month_labels) - 1)

start_year, start_month = label_to_date[start_label]
end_year, end_month = label_to_date[end_label]

start_idx = available_months.index((start_year, start_month))
end_idx = available_months.index((end_year, end_month))

if start_idx > end_idx:
    st.sidebar.error("Start month must not be after end month.")
    st.stop()

start_date = datetime(start_year, start_month, 1)
end_date = datetime(end_year + 1, 1, 1) if end_month == 12 else datetime(end_year, end_month + 1, 1)
selected_months = available_months[start_idx : end_idx + 1]

# ─── Load Data ────────────────────────────────────────────────────────────
if not os.path.exists(DATA_FILE):
    st.error(f"Error: {DATA_FILE} not found.")
    st.stop()

full_df = pd.read_excel(DATA_FILE, sheet_name=0)

if "relevancy" in full_df.columns:
    full_df = full_df[full_df["relevancy"] == True].copy()

if "Published" in full_df.columns and "Published Date" not in full_df.columns:
    full_df["Published Date"] = full_df["Published"]
if "Media Outlet Country" in full_df.columns and "Country" not in full_df.columns:
    full_df["Country"] = full_df["Media Outlet Country"]

brands_in_data = full_df["brand"].dropna().astype(str).str.lower().unique()
keys_data = {}
for b in brands_in_data:
    display = DISPLAY_NAME_MAP.get(b, b.replace("_", " ").title())
    keys_data[display] = b

# ─── Dashboard Header ─────────────────────────────────────────────────────
date_range_str = f"{start_label} – {end_label}"
st.markdown(
    f"""
    <div class="synthesis-header-wrapper">
        <div class="synthesis-header-inner">
            <div class="synthesis-label">≡ SIRIN</div>
            <div class="synthesis-label">REPORT · {date_range_str}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─── Section: Company Performance Overview ─────────────────────────────────
section_header("COMPETITIVE LANDSCAPE", "Company Performance Overview")

st.markdown(
    """
This matrix showcases three top brand archetypes for each market player. The archetypes are determined by analyzing the content of the articles and mentions, and identifying key values that are communicated.

- **X-axis** represents the volume of articles captured since the start of this year.
- **Y-axis** shows the quality of sources, determined by the authority of the web domain that features the content. The higher the quality, the more authoritative and established the domains or websites are that mention the brands.

This matrix is based on a larger brand mention sample over an extended period of time to more accurately determine the brand archetypes communicated by brands.

Read more about brand archetypes here: [Brandtypes](https://www.comp-os.com/brandtypes).
"""
)

company_summary = {}
for company, brand in keys_data.items():
    df = full_df[full_df["brand"].astype(str).str.lower() == brand].copy()
    if not df.empty:
        volume = len(df)
        quality = df["BMQ"].mean()
        if "Top Archetype" in df.columns:
            archetype_counts = df["Top Archetype"].value_counts(normalize=True) * 100
            top_3_archetypes = archetype_counts.nlargest(3)
            archetype_text = "<br>".join([f"{a} ({p:.1f}%)" for a, p in top_3_archetypes.items()])
        else:
            archetype_text = "No Archetype Data"
        company_summary[company] = {"Volume": volume, "Quality": round(quality, 2) if not pd.isna(quality) else 0, "Archetypes": archetype_text}

summary_df = pd.DataFrame.from_dict(company_summary, orient="index").reset_index()
summary_df.columns = ["Company", "Volume", "Quality", "Archetypes"]

# Scatter plot — Synthesis styling: grayscale, SIRIN in green
colors = [COLOR_DATA_4 if c.upper() == "SIRIN" else COLOR_DATA_1 for c in summary_df["Company"]]

fig_scatter = go.Figure()
for i, row in summary_df.iterrows():
    fig_scatter.add_trace(
        go.Scatter(
            x=[row["Volume"]],
            y=[row["Quality"]],
            mode="markers+text",
            marker=dict(size=12, color=colors[i], line=dict(width=2, color=COLOR_BG)),
            text=row["Company"],
            textposition="top center",
            textfont=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=11, color=COLOR_TEXT_PRIMARY),
            customdata=[[row["Archetypes"]]],
            hovertemplate="<b>%{text}</b><br>Volume: %{x}<br>Quality: %{y}<br>%{customdata[0]}<extra></extra>",
            showlegend=False,
        )
    )

fig_scatter.update_layout(
    **PLOTLY_LAYOUT,
    title=dict(text="Volume vs Quality by Company", font=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=16, color=COLOR_TEXT_PRIMARY)),
    xaxis_title="VOLUME (NUMBER OF ARTICLES)",
    yaxis_title="QUALITY (AVG. BMQ SCORE)",
)
st.plotly_chart(fig_scatter, width="stretch")

# ─── Section: Sentiment Distribution ───────────────────────────────────────
section_header("SENTIMENT ANALYSIS", "Sentiment Distribution Across Companies")

st.markdown(
    """
Sentiment scores showcase positive, negative and neutral context for company mentions.
Take note that the AI engine also more broadly classifies negative mentions as ones including a more negative context as well as negative news related to the company itself.
"""
)

sentiment_summary = {}
for company, brand in keys_data.items():
    df = full_df[full_df["brand"].astype(str).str.lower() == brand].copy()
    if "Published Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Published Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]
    else:
        continue

    if not df.empty and "Sentiment" in df.columns:
        sentiment_counts = df["Sentiment"].value_counts(normalize=True) * 100
        label = f"{company} ({len(df)})"
        sentiment_summary[label] = {
            "Positive": sentiment_counts.get("Positive", 0),
            "Neutral": sentiment_counts.get("Neutral", 0),
            "Negative": sentiment_counts.get("Negative", 0),
        }
        if company.upper() == "SIRIN":
            country_codes = {"Lithuania": "LT", "Latvia": "LV", "Estonia": "EE"}
            for country, code in country_codes.items():
                df_country = df[df["Country"] == country]
                sentiment_counts = df_country["Sentiment"].value_counts(normalize=True) * 100
                label = f"SIRIN {code} ({len(df_country)})"
                sentiment_summary[label] = {
                    "Positive": sentiment_counts.get("Positive", 0),
                    "Neutral": sentiment_counts.get("Neutral", 0),
                    "Negative": sentiment_counts.get("Negative", 0),
                }

if not sentiment_summary:
    st.warning("No sentiment data available in the selected date range.")
else:
    sentiment_df = pd.DataFrame.from_dict(sentiment_summary, orient="index").reset_index()
    sentiment_df = sentiment_df.melt(id_vars=["index"], var_name="Sentiment", value_name="Percentage")
    sentiment_df.columns = ["Company", "Sentiment", "Percentage"]

    # Synthesis: Positive=green, Neutral=gray, Negative=black (bold)
    color_map = {"Positive": COLOR_POSITIVE, "Neutral": COLOR_DATA_2, "Negative": COLOR_NEGATIVE}

    fig_sentiment = px.bar(
        sentiment_df,
        x="Company",
        y="Percentage",
        color="Sentiment",
        text="Percentage",
        color_discrete_map=color_map,
    )
    fig_sentiment.update_traces(texttemplate="%{text:.1f}%", textposition="inside")
    sentiment_layout = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("legend", "margin")}
    fig_sentiment.update_layout(
        **sentiment_layout,
        margin=dict(l=48, r=48, t=48, b=80),
        barmode="stack",
        title=dict(text="Sentiment Distribution (brackets show article count for selected period)", font=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=16, color=COLOR_TEXT_PRIMARY)),
        xaxis_title="COMPANY",
        yaxis_title="PERCENTAGE",
        legend=dict(
            font=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=11, color=COLOR_TEXT_MUTED),
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="left",
            x=0,
        ),
    )
    st.plotly_chart(fig_sentiment, width="stretch")

# ─── Section: Top 5 Articles by UVM ─────────────────────────────────────────
section_header("TOP ARTICLES", "Top 5 Articles by UVM (Insights by Similarweb)")

UVM_COL = "UVM (Insights by Similarweb)"
if UVM_COL in full_df.columns:
    company_top5 = {}
    for company, brand in keys_data.items():
        df_brand = full_df[full_df["brand"].astype(str).str.lower() == brand].copy()
        if "Published Date" in df_brand.columns:
            df_brand["Published Date"] = pd.to_datetime(df_brand["Published Date"], errors="coerce")
            df_brand = df_brand.dropna(subset=["Published Date"])
            df_brand = df_brand[
                (df_brand["Published Date"] >= pd.to_datetime(start_date))
                & (df_brand["Published Date"] <= pd.to_datetime(end_date))
            ]
        if df_brand.empty:
            continue
        try:
            df_brand[UVM_COL] = pd.to_numeric(df_brand[UVM_COL], errors="coerce")
        except Exception:
            pass
        top5 = df_brand.nlargest(5, UVM_COL, keep="first")
        if not top5.empty:
            company_top5[company] = top5

    if company_top5:
        tab_labels = [c for c in company_top5.keys()]
        tabs = st.tabs(tab_labels)
        for tab, (company, top5) in zip(tabs, company_top5.items()):
            with tab:
                for _, row in top5.iterrows():
                    article = row.get("Article", row.get("Title", "—"))
                    url = row.get("URL", row.get("Link", "")) or "#"
                    title = str(article)[:100] + ("..." if len(str(article)) > 100 else "")
                    title_esc = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
                    url_esc = str(url).replace("&", "&amp;").replace('"', "&quot;")
                    st.markdown(
                        f'<div class="synthesis-article-card">'
                        f'<a href="{url_esc}" target="_blank" rel="noopener">{title_esc}</a>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )
    else:
        st.info("No articles with UVM data for the selected period.")
else:
    st.info("UVM (Insights by Similarweb) column not found in data.")

# ─── Section: Media Mentions Coverage Share ─────────────────────────────────
section_header("COVERAGE SHARE", "Media Mentions Coverage Share")

st.markdown(
    """
The Media Mentions show all articles that mention the specific brand in news outlets. These can range from smaller local outlets to international ones.
"""
)

non_organic_data = []
for company, brand in keys_data.items():
    df_agility = full_df[full_df["brand"].astype(str).str.lower() == brand].copy()
    if "Published Date" not in df_agility.columns:
        continue
    df_agility["Published Date"] = pd.to_datetime(df_agility["Published Date"], errors="coerce")
    df_agility = df_agility.dropna(subset=["Published Date"])
    df_agility = df_agility[
        (df_agility["Published Date"] >= pd.to_datetime(start_date))
        & (df_agility["Published Date"] <= pd.to_datetime(end_date))
    ]
    df_agility["Company"] = company
    non_organic_data.append(df_agility)

if non_organic_data:
    mention_df = pd.concat(non_organic_data, ignore_index=True)

    def plot_mention_share(dataframe, title):
        if dataframe.empty:
            st.info("No data available for this period.")
            return
        count_df = dataframe.groupby("Company").size().reset_index(name="Volume")
        total_mentions = count_df["Volume"].sum()
        count_df["Percentage"] = (count_df["Volume"] / total_mentions) * 100

        # Synthesis: grayscale + SIRIN in green
        grayscale = [COLOR_DATA_1, COLOR_DATA_2, COLOR_DATA_3]
        pie_colors = [
            COLOR_DATA_4 if c.upper() == "SIRIN" else grayscale[i % 3]
            for i, c in enumerate(count_df["Company"])
        ]

        fig_pie = go.Figure(
            data=[
                go.Pie(
                    labels=count_df["Company"],
                    values=count_df["Volume"],
                    marker=dict(
                        colors=pie_colors,
                        line=dict(width=1, color=COLOR_BG),
                    ),
                    textinfo="label+percent",
                    hovertemplate="%{label}: %{value} articles<extra></extra>",
                )
            ]
        )
        pie_layout = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("showlegend", "margin")}
        fig_pie.update_layout(
            **pie_layout,
            title=dict(text=title, font=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=16, color=COLOR_TEXT_PRIMARY)),
            showlegend=False,
            margin=dict(t=48, b=24, l=24, r=24),
        )
        st.plotly_chart(fig_pie, width="stretch")

    tab_total, tab_lt, tab_lv, tab_ee = st.tabs(["Total", "Lithuania", "Latvia", "Estonia"])
    with tab_total:
        plot_mention_share(mention_df, "Total Share of Media Mentions Coverage")
    with tab_lt:
        plot_mention_share(mention_df[mention_df["Country"] == "Lithuania"], "Lithuania Media Mentions Coverage")
    with tab_lv:
        plot_mention_share(mention_df[mention_df["Country"] == "Latvia"], "Latvia Media Mentions Coverage")
    with tab_ee:
        plot_mention_share(mention_df[mention_df["Country"] == "Estonia"], "Estonia Media Mentions Coverage")
else:
    st.warning("No data loaded in the selected date range.")

# ─── Section: Monthly Trends ───────────────────────────────────────────────
section_header("TREND ANALYSIS", "Monthly Media Mentions Volume")

st.markdown("Media mentions shows overall number of company mentions for a given period.")

now = pd.Timestamp.now()
previous_month = now.month - 1 if now.month > 1 else 12
previous_year = now.year if now.month > 1 else now.year - 1
date_range = pd.date_range(end=pd.Timestamp(previous_year, previous_month, 1), periods=4, freq="MS")
month_labels_ts = [date.strftime("%b %Y") for date in date_range]
country_codes = {"Lithuania": "LT", "Latvia": "LV", "Estonia": "EE"}

time_series_data = {}
for company, brand in keys_data.items():
    df = full_df[full_df["brand"].astype(str).str.lower() == brand].copy()
    if "Published Date" not in df.columns and "Snippet" in df.columns:
        df["Published Date"] = df["Snippet"].apply(lambda x: extract_date(x) if isinstance(x, str) else None)
    if not df.empty and "Published Date" in df.columns:
        df["Published Date"] = pd.to_datetime(df["Published Date"], format="%m/%d/%Y", errors="coerce")
        df["Month"] = df["Published Date"].dt.to_period("M")

        if company.upper() == "SIRIN":
            for month in date_range:
                month_str = month.strftime("%b %Y")
                volume = df[df["Month"] == month.to_period("M")].shape[0]
                time_series_data.setdefault("SIRIN Total", {"Month": [], "Volume": []})
                time_series_data["SIRIN Total"]["Month"].append(month_str)
                time_series_data["SIRIN Total"]["Volume"].append(volume)
            for country, code in country_codes.items():
                df_country = df[df["Country"] == country]
                for month in date_range:
                    month_str = month.strftime("%b %Y")
                    month_period = month.to_period("M")
                    volume = df_country[df_country["Month"] == month_period].shape[0]
                    key = f"SIRIN {code}"
                    time_series_data.setdefault(key, {"Month": [], "Volume": []})
                    time_series_data[key]["Month"].append(month_str)
                    time_series_data[key]["Volume"].append(volume)
        else:
            for month in date_range:
                month_str = month.strftime("%b %Y")
                month_period = month.to_period("M")
                volume = df[df["Month"] == month_period].shape[0]
                time_series_data.setdefault(company, {"Month": [], "Volume": []})
                time_series_data[company]["Month"].append(month_str)
                time_series_data[company]["Volume"].append(volume)

for company in time_series_data.keys():
    if len(time_series_data[company]["Month"]) == 0:
        time_series_data[company]["Month"] = [m.strftime("%b %Y") for m in date_range]
        time_series_data[company]["Volume"] = [0] * len(date_range)

time_series_df = pd.concat(
    [
        pd.DataFrame({"Company": company, "Month": data["Month"], "Volume": data["Volume"]})
        for company, data in time_series_data.items()
    ],
    ignore_index=True,
)

# Line chart — Synthesis: SIRIN Total in green, others grayscale
fig_volume = px.line(
    time_series_df,
    x="Month",
    y="Volume",
    color="Company",
    markers=True,
)

# Apply Synthesis colors to traces
for i, trace in enumerate(fig_volume.data):
    trace.line.color = COLOR_DATA_4 if "SIRIN" in trace.name else (COLOR_DATA_1 if i % 3 == 0 else COLOR_DATA_2 if i % 3 == 1 else COLOR_DATA_3)
    trace.line.width = 2 if "SIRIN" in trace.name else 1.5
    trace.marker.size = 4

vol_layout = {k: v for k, v in PLOTLY_LAYOUT.items() if k not in ("xaxis", "legend", "margin")}
xaxis_merged = {**PLOTLY_LAYOUT.get("xaxis", {}), "categoryorder": "array", "categoryarray": month_labels_ts}
fig_volume.update_layout(
    **vol_layout,
    title=dict(text="Monthly Media Mentions Volume Trend per Company", font=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=16, color=COLOR_TEXT_PRIMARY)),
    xaxis_title="MONTH",
    yaxis_title="MEDIA MENTIONS VOLUME (ARTICLES)",
    xaxis=xaxis_merged,
    legend=dict(
        font=dict(family="'DM Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif", size=11, color=COLOR_TEXT_MUTED),
        orientation="h",
        yanchor="top",
        y=-0.18,
        xanchor="left",
        x=0,
    ),
    margin=dict(l=48, r=48, t=48, b=80),
)
st.plotly_chart(fig_volume, width="stretch")

st.markdown('<p class="synthesis-chart-caption">Source: Internal analytics. Figures represent unique sessions.</p>', unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
