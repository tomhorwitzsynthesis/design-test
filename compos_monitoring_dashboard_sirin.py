import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np
import re
from datetime import datetime, timedelta




# Data file (single file with all brands, brand column)
DATA_FOLDER = "data sirin"
DATA_FILE = os.path.join(DATA_FOLDER, "data.xlsx")

# Display name mapping: brand (lowercase in data) -> display name
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

from calendar import month_name

# === 🔧 MANUAL CONFIGURATION: Available Data Months ===
# Format: list of (year, month_number) tuples
available_months = [
    (2025, 1), (2025, 2), (2025, 3), (2025, 4), (2025, 5), (2025, 6), (2025, 7), (2025, 8), (2025, 9), (2025, 10), (2025, 11), (2025, 12),
    (2026, 1), (2026, 2)
]





# # === UI: Month Checkboxes ===
# st.sidebar.markdown("### Select Months to Include")
# selected_months = []

# for year, month in available_months:
#     label = f"{month_name[month]} {year}"
#     if st.sidebar.checkbox(label, value=True):
#         selected_months.append((year, month))

# # === Handle No Selection ===
# if not selected_months:
#     st.sidebar.error("Please select at least one month.")
#     st.stop()

# # === Compute Date Range from Selected Months ===
# selected_months.sort()
# start_year, start_month = selected_months[0]
# end_year, end_month = selected_months[-1]

# start_date = datetime(start_year, start_month, 1)
# # End date is the first day of the month *after* the last selected month
# if end_month == 12:
#     end_date = datetime(end_year + 1, 1, 1)
# else:
#     end_date = datetime(end_year, end_month + 1, 1)

# === UI: Select Start and End Month ===
st.sidebar.markdown("### Select Date Range")

# Create user-facing labels and mapping back to (year, month)
month_labels = [f"{month_name[m]} {y}" for y, m in available_months]
label_to_date = {label: (y, m) for label, (y, m) in zip(month_labels, available_months)}

# Dropdowns for start and end month
start_label = st.sidebar.selectbox("Start Month", month_labels, index=0)
end_label = st.sidebar.selectbox("End Month", month_labels, index=len(month_labels) - 1)

start_year, start_month = label_to_date[start_label]
end_year, end_month = label_to_date[end_label]

# === Validate chronological order ===
start_idx = available_months.index((start_year, start_month))
end_idx = available_months.index((end_year, end_month))

if start_idx > end_idx:
    st.sidebar.error("Start month must not be after end month.")
    st.stop()

# === Compute Date Range ===
start_date = datetime(start_year, start_month, 1)
if end_month == 12:
    end_date = datetime(end_year + 1, 1, 1)
else:
    end_date = datetime(end_year, end_month + 1, 1)

# === Generate selected_months list for downstream logic ===
selected_months = available_months[start_idx:end_idx + 1]

# Load data from data.xlsx
if not os.path.exists(DATA_FILE):
    st.error(f"Error: {DATA_FILE} not found!")
    st.stop()

full_df = pd.read_excel(DATA_FILE, sheet_name=0)

# Filter to relevant articles only (if relevancy column exists)
if "relevancy" in full_df.columns:
    full_df = full_df[full_df["relevancy"] == True].copy()

# Normalize column names for compatibility (data.xlsx uses Published, Media Outlet Country)
if "Published" in full_df.columns and "Published Date" not in full_df.columns:
    full_df["Published Date"] = full_df["Published"]
if "Media Outlet Country" in full_df.columns and "Country" not in full_df.columns:
    full_df["Country"] = full_df["Media Outlet Country"]

# Get brands present in data
brands_in_data = full_df["brand"].dropna().astype(str).str.lower().unique()
# Prefer DISPLAY_NAME_MAP for known brands, else use title case
keys_data = {}
for b in brands_in_data:
    display = DISPLAY_NAME_MAP.get(b, b.replace("_", " ").title())
    keys_data[display] = b

# Create dropdown options with display names, sorted as needed
#dropdown_options = ["Overview"] + [reverse_map[key] for key in keys_data.keys()]

# Sidebar for company selection
#selected_display_name = st.sidebar.selectbox("Select a Company", dropdown_options)

# Get the corresponding internal key (only if not "Overview")
#selected_company = display_name_map.get(selected_display_name, "Overview")

def extract_date(snippet):
    # Simulated "current" date: last day of the previous month
    today = pd.Timestamp.today()
    first_day_this_month = pd.Timestamp(today.year, today.month, 1)
    reference_date = first_day_this_month - pd.Timedelta(days=1)  # Last day of previous month

    # Handle relative dates
    if "day ago" in snippet or "days ago" in snippet:
        match = re.search(r"(\d+)\s+day[s]?\s+ago", snippet)
        if match:
            days_ago = int(match.group(1))
            return (reference_date - timedelta(days=days_ago)).strftime("%m/%d/%Y")

    elif "hour ago" in snippet or "hours ago" in snippet:
        match = re.search(r"(\d+)\s+hour[s]?\s+ago", snippet)
        if match:
            hours_ago = int(match.group(1))
            return (reference_date - timedelta(hours=int(match.group(1)))).strftime("%m/%d/%Y")

    # Handle absolute dates like "Sep 25, 2024"
    match = re.match(r"([A-Za-z]{3} \d{1,2}, \d{4})", snippet)
    if match:
        try:
            extracted_date = pd.to_datetime(match.group(1), format="%b %d, %Y")
            return extracted_date.strftime("%m/%d/%Y")
        except:
            return None

    return None




# Dictionary to store Volume, Quality, and Archetypes for each company
company_summary = {}

############################### NEWS ###############################################################################################################################################

st.title("Monitoring Dashboard")

st.header("News")

st.subheader("📊 Company Performance Overview")

st.markdown("""
This matrix showcases **three top brand archetypes** for each market player. The archetypes are determined by analyzing the content of the articles and mentions, and identifying key values that are communicated.

- **X-axis** represents the **volume of articles** captured since the start of this year.  
- **Y-axis** shows the **quality of sources**, determined by the authority of the web domain that features the content. The higher the quality, the more authoritative and established the domains or websites are that mention the brands.

This matrix is based on a larger brand mention sample over an extended period of time to more accurately determine the brand archetypes communicated by brands.

Read more about brand archetypes here: [Brandtypes](https://www.comp-os.com/brandtypes).
""")



# Extract Volume, Quality, and Archetypes from each brand
for company, brand in keys_data.items():
    df = full_df[full_df["brand"].astype(str).str.lower() == brand].copy()

    if not df.empty:
        volume = len(df)
        quality = df["BMQ"].mean()

        if "Top Archetype" in df.columns:
            archetype_counts = df["Top Archetype"].value_counts(normalize=True) * 100
            top_3_archetypes = archetype_counts.nlargest(3)
            archetype_text = "<br>".join([f"{archetype} ({percent:.1f}%)" for archetype, percent in top_3_archetypes.items()])
        else:
            archetype_text = "No Archetype Data"

        company_summary[company] = {
            "Volume": volume,
            "Quality": round(quality, 2) if not pd.isna(quality) else 0,
            "Archetypes": archetype_text
        }

# Convert dictionary to DataFrame
summary_df = pd.DataFrame.from_dict(company_summary, orient="index").reset_index()
summary_df.columns = ["Company", "Volume", "Quality", "Archetypes"]

# 🎯 Create Scatter Plot (Volume vs. Quality)

fig = px.scatter(
    summary_df,
    x="Volume",
    y="Quality",
    text="Company",  # Company names displayed above points
    hover_data=["Archetypes"],  # Show Archetypes on hover
    size_max=15,
    title="Company Performance (Volume vs. Quality) with Archetypes",
)

# Enhance the plot: Position company names correctly
fig.update_traces(
    textposition="top center",
    marker=dict(size=10, color="blue")
)

# Avoid text overlap: Calculate dynamic Y-positions
y_positions = []
min_y_distance = 0.03 * summary_df["Quality"].max()  # Dynamic adjustment factor

for i, row in summary_df.iterrows():
    y_pos = row["Quality"] - min_y_distance  # Default position (below point)
    
    # If another label is too close, shift the new one further down
    while any(abs(y_pos - prev_y) < min_y_distance for prev_y in y_positions):
        y_pos -= min_y_distance  # Move text further down

    y_positions.append(y_pos)  # Store adjusted position

    fig.add_annotation(
        x=row["Volume"],
        y=y_pos,
        text=f"<b>{row['Company']}</b><br>{row['Archetypes']}",  # ✅ Add company name
        showarrow=False,
        font=dict(size=8, color="black"),
        align="center",
        xanchor="center",
        yanchor="top",
        bordercolor="lightgray",
        borderwidth=1,
        borderpad=2,
        bgcolor="white",
    )


# Improve layout to prevent overlapping text
fig.update_layout(
    xaxis_title="Volume (Number of Articles)",
    yaxis_title="Quality (Avg. BMQ Score)",
    margin=dict(l=40, r=40, t=30, b=40),
    dragmode=False  # Disable zoom to keep positions fixed
)

# Display the scatter plot at the top of the dashboard
st.plotly_chart(fig, use_container_width=True)

# Dictionary to store sentiment counts
sentiment_summary = {}

# 🎭 Sentiment Analysis - Stacked Bar Chart with Date Filter
st.subheader("📊 Sentiment Distribution Across Companies")

st.markdown("""Sentiment scores showcase positive, negative and neutral context for company mentions. 
Take note that AI engine also more broadly classifies negative mentions as ones including a more negative context as well as negative news related to the company itself. 
""")

sentiment_summary = {}

for company, brand in keys_data.items():
    df = full_df[full_df["brand"].astype(str).str.lower() == brand].copy()

    if "Published Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Published Date"], errors='coerce')
        df = df.dropna(subset=["Date"])
        df = df[(df["Date"] >= pd.to_datetime(start_date)) & (df["Date"] <= pd.to_datetime(end_date))]
    else:
        continue

    if not df.empty and "Sentiment" in df.columns:
        if company.upper() == "SIRIN":
            sentiment_counts = df["Sentiment"].value_counts(normalize=True) * 100
            label = f"{company} ({len(df)})"
            sentiment_summary[label] = {
                "Positive": sentiment_counts.get("Positive", 0),
                "Neutral": sentiment_counts.get("Neutral", 0),
                "Negative": sentiment_counts.get("Negative", 0)
            }
            country_codes = {"Lithuania": "LT", "Latvia": "LV", "Estonia": "EE"}
            for country, code in country_codes.items():
                df_country = df[df["Country"] == country]
                sentiment_counts = df_country["Sentiment"].value_counts(normalize=True) * 100
                label = f"SIRIN {code} ({len(df_country)})"
                sentiment_summary[label] = {
                    "Positive": sentiment_counts.get("Positive", 0),
                    "Neutral": sentiment_counts.get("Neutral", 0),
                    "Negative": sentiment_counts.get("Negative", 0)
                }
        else:
            sentiment_counts = df["Sentiment"].value_counts(normalize=True) * 100
            label = f"{company} ({len(df)})"
            sentiment_summary[label] = {
                "Positive": sentiment_counts.get("Positive", 0),
                "Neutral": sentiment_counts.get("Neutral", 0),
                "Negative": sentiment_counts.get("Negative", 0)
            }


if not sentiment_summary:
    st.warning("No sentiment data available in the selected date range.")
else:
    sentiment_df = pd.DataFrame.from_dict(sentiment_summary, orient="index").reset_index()
    sentiment_df = sentiment_df.melt(id_vars=["index"], var_name="Sentiment", value_name="Percentage")
    sentiment_df.columns = ["Company", "Sentiment", "Percentage"]

    fig_sentiment = px.bar(
        sentiment_df,
        x="Company",
        y="Percentage",
        color="Sentiment",
        text="Percentage",
        title="Sentiment Distribution Per Company (Brackets show the number of articles for the selected period)",
        color_discrete_map={"Positive": "green", "Neutral": "grey", "Negative": "red"},
    )

    fig_sentiment.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
    fig_sentiment.update_layout(barmode="stack", xaxis_title="Company", yaxis_title="Percentage")

    st.plotly_chart(fig_sentiment, use_container_width=True)



# === Top 5 Articles by UVM (Insights by Similarweb) ===
st.subheader("📊 Top 5 Articles by UVM (Insights by Similarweb)")

UVM_COL = "UVM (Insights by Similarweb)"
if UVM_COL in full_df.columns:
    company_top5 = {}
    for company, brand in keys_data.items():
        df_brand = full_df[full_df["brand"].astype(str).str.lower() == brand].copy()
        if "Published Date" in df_brand.columns:
            df_brand["Published Date"] = pd.to_datetime(df_brand["Published Date"], errors="coerce")
            df_brand = df_brand.dropna(subset=["Published Date"])
            df_brand = df_brand[
                (df_brand["Published Date"] >= pd.to_datetime(start_date)) &
                (df_brand["Published Date"] <= pd.to_datetime(end_date))
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
        tab_labels = [f"🏢 {c}" for c in company_top5.keys()]
        tabs = st.tabs(tab_labels)
        for tab, (company, top5) in zip(tabs, company_top5.items()):
            with tab:
                for _, row in top5.iterrows():
                    article = row.get("Article", row.get("Title", "—"))
                    url = row.get("URL", row.get("Link", "")) or "#"
                    title = str(article)[:100] + ("..." if len(str(article)) > 100 else "")
                    # Escape HTML for safety
                    title_esc = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
                    url_esc = str(url).replace("&", "&amp;").replace('"', "&quot;")
                    st.markdown(
                        f'<div style="border: 1px solid #ddd; border-radius: 8px; padding: 12px 16px; margin-bottom: 10px; background: #fafafa;">'
                        f'<a href="{url_esc}" target="_blank" rel="noopener" style="color: #1f77b4; text-decoration: none; font-weight: 500;">{title_esc}</a>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
    else:
        st.info("No articles with UVM data for the selected period.")
else:
    st.info("UVM (Insights by Similarweb) column not found in data.")


st.subheader("📰 Media Mentions Coverage Share 2025")

st.markdown("""
The Media Mentions show all articles that mention the specific brand in news outlets. These can range from smaller local outlets to international ones.
""")

non_organic_data = []

for company, brand in keys_data.items():
    df_agility = full_df[full_df["brand"].astype(str).str.lower() == brand].copy()

    if "Published Date" not in df_agility.columns:
        continue

    df_agility["Published Date"] = pd.to_datetime(df_agility["Published Date"], errors="coerce")
    df_agility = df_agility.dropna(subset=["Published Date"])
    df_agility = df_agility[
        (df_agility["Published Date"] >= pd.to_datetime(start_date)) &
        (df_agility["Published Date"] <= pd.to_datetime(end_date))
    ]

    df_agility["Company"] = company
    non_organic_data.append(df_agility)

if non_organic_data:
    mention_df = pd.concat(non_organic_data, ignore_index=True)

    # Tabs by region
    tab_total, tab_lt, tab_lv, tab_ee = st.tabs(["🌍 Total", "🇱🇹 Lithuania", "🇱🇻 Latvia", "🇪🇪 Estonia"])

    def plot_mention_share(dataframe, title):
        if dataframe.empty:
            st.info("No data available for this period.")
            return

        count_df = dataframe.groupby("Company").size().reset_index(name="Volume")
        total_mentions = count_df["Volume"].sum()
        count_df["Percentage"] = (count_df["Volume"] / total_mentions) * 100

        color_map = {"SIRIN": "#00FF00"}  # Optional: override SIRIN color

        fig_pie = px.pie(
            count_df,
            names="Company",
            values="Volume",
            title=title,
            hover_data=["Percentage"],
            labels={"Percentage": "% of Total"},
            color="Company",
            color_discrete_map=color_map
        )

        fig_pie.update_traces(
            textinfo="label+percent",
            hovertemplate="%{label}: %{value} articles (%{customdata[0]:.1f}%)"
        )

        st.plotly_chart(fig_pie, use_container_width=True)

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


# Format hover tooltips
#fig_pie.update_traces(textinfo="label+percent", hovertemplate="%{label}: %{value} articles (%{customdata[0]:.1f}%)")

# Display Pie Chart
#st.plotly_chart(fig_pie, use_container_width=True)

st.subheader("📈 Monthly Trends for Media Mentions & Online Reputation Volume")

st.markdown("""Media mentions shows overall number of company mentions for a given period. 
            """)

# Get the current month and year
now = pd.Timestamp.now()
previous_month = now.month - 1 if now.month > 1 else 12
previous_year = now.year if now.month > 1 else now.year - 1

current_month = previous_month
current_year = previous_year

# Define the past 6 months
date_range = pd.date_range(end=pd.Timestamp(previous_year, previous_month, 1), periods=4, freq='MS')
month_labels = [date.strftime('%b %Y') for date in date_range]

# Dictionary to store time-series data
#time_series_data = {company: {"Month": [], "Volume": [], "NonOrganicVolume": [0] * len(date_range)} for company in keys_data}

# Dictionary to store time-series data
time_series_data = {}

# Define your country codes for display
country_codes = {"Lithuania": "LT", "Latvia": "LV", "Estonia": "EE"}

for company, brand in keys_data.items():
    df = full_df[full_df["brand"].astype(str).str.lower() == brand].copy()

    if "Published Date" not in df.columns and "Snippet" in df.columns:
        df["Published Date"] = df["Snippet"].apply(lambda x: extract_date(x) if isinstance(x, str) else None)

    if not df.empty and "Published Date" in df.columns:
        df["Published Date"] = pd.to_datetime(df["Published Date"], format="%m/%d/%Y", errors="coerce")
        df["Month"] = df["Published Date"].dt.to_period("M")
        df["MonthStr"] = df["Month"].dt.strftime('%b %Y')

        if company.upper() == "SIRIN":
            for month in date_range:
                month_str = month.strftime('%b %Y')
                volume = df[df["Month"] == month.to_period("M")].shape[0]
                time_series_data.setdefault("SIRIN Total", {"Month": [], "Volume": []})
                time_series_data["SIRIN Total"]["Month"].append(month_str)
                time_series_data["SIRIN Total"]["Volume"].append(volume)

            for country, code in country_codes.items():
                df_country = df[df["Country"] == country]
                for month in date_range:
                    month_str = month.strftime('%b %Y')
                    month_period = month.to_period("M")
                    volume = df_country[df_country["Month"] == month_period].shape[0]
                    key = f"SIRIN {code}"
                    time_series_data.setdefault(key, {"Month": [], "Volume": []})
                    time_series_data[key]["Month"].append(month_str)
                    time_series_data[key]["Volume"].append(volume)
        else:
            for month in date_range:
                month_str = month.strftime('%b %Y')
                month_period = month.to_period("M")
                volume = df[df["Month"] == month_period].shape[0]
                time_series_data.setdefault(company, {"Month": [], "Volume": []})
                time_series_data[company]["Month"].append(month_str)
                time_series_data[company]["Volume"].append(volume)


# Ensure non-organic data is zero for companies with no organic data
for company in time_series_data.keys():
    if len(time_series_data[company]["Month"]) == 0:  # No organic data found
        #st.warning(f"⚠️ **{company} has no organic data, setting non-organic volume to 0.**")
        time_series_data[company]["Month"] = [month.strftime('%b %Y') for month in date_range]
        time_series_data[company]["Volume"] = [0] * len(date_range)
        #time_series_data[company]["NonOrganicVolume"] = [0] * len(date_range)  # Ensure all values are zero

# If the error persists, this will reveal which list has a length mismatch
time_series_df = pd.concat(
    [pd.DataFrame({"Company": company, "Month": data["Month"], "Volume": data["Volume"]})
    for company, data in time_series_data.items()], ignore_index=True
)

time_series_df = pd.concat(
    [pd.DataFrame({"Company": company, "Month": data["Month"], "Volume": data["Volume"]})
    for company, data in time_series_data.items()], ignore_index=True
)



fig_volume = px.line(
    time_series_df,
    x="Month",
    y="Volume",
    color="Company",
    markers=True,
    title="Monthly Media Mentions Volume Trend per Company",
)

fig_volume.update_layout(
    xaxis_title="Month",
    yaxis_title="Media Mentions Volume (Articles)",
    xaxis=dict(categoryorder="array", categoryarray=month_labels)
)

st.plotly_chart(fig_volume, use_container_width=True)




