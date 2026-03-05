"""
Sentiment Analysis Module for SIRIN Monitoring Dashboard
Handles sentiment distribution analysis and visualization across companies
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from config import SENTIMENT_COLORS, COUNTRY_CODES
from utils import get_company_data, filter_data_by_date_range

def analyze_sentiment_by_company(keys_data, data_folder, start_date, end_date):
    """
    Analyze sentiment distribution for each company within the date range
    
    Args:
        keys_data (dict): Company mappings from keys file
        data_folder (str): Path to data folder
        start_date (datetime): Start date for filtering
        end_date (datetime): End date for filtering
        
    Returns:
        dict: Sentiment summary for each company
    """
    sentiment_summary = {}
    
    for company, filename in keys_data.items():
        company_lower = company.lower()
        df = get_company_data(data_folder, company)
        
        if not df.empty and "Sentiment" in df.columns:
            # Filter by date range
            df_filtered = filter_data_by_date_range(df, start_date, end_date)
            
            if not df_filtered.empty:
                if company.upper() == "SIRIN":
                    # SIRIN Total
                    sentiment_counts = df_filtered["Sentiment"].value_counts(normalize=True) * 100
                    label = f"{company} ({len(df_filtered)})"
                    sentiment_summary[label] = {
                        "Positive": sentiment_counts.get("Positive", 0),
                        "Neutral": sentiment_counts.get("Neutral", 0),
                        "Negative": sentiment_counts.get("Negative", 0)
                    }
                    
                    # SIRIN per country
                    for country, code in COUNTRY_CODES.items():
                        if "Country" in df_filtered.columns:
                            df_country = df_filtered[df_filtered["Country"] == country]
                            if not df_country.empty:
                                sentiment_counts = df_country["Sentiment"].value_counts(normalize=True) * 100
                                label = f"SIRIN {code} ({len(df_country)})"
                                sentiment_summary[label] = {
                                    "Positive": sentiment_counts.get("Positive", 0),
                                    "Neutral": sentiment_counts.get("Neutral", 0),
                                    "Negative": sentiment_counts.get("Negative", 0)
                                }
                else:
                    # Other companies
                    sentiment_counts = df_filtered["Sentiment"].value_counts(normalize=True) * 100
                    label = f"{company} ({len(df_filtered)})"
                    sentiment_summary[label] = {
                        "Positive": sentiment_counts.get("Positive", 0),
                        "Neutral": sentiment_counts.get("Neutral", 0),
                        "Negative": sentiment_counts.get("Negative", 0)
                    }
    
    return sentiment_summary

def create_sentiment_chart(sentiment_summary):
    """
    Create stacked bar chart for sentiment distribution
    
    Args:
        sentiment_summary (dict): Sentiment data for each company
        
    Returns:
        plotly.Figure: Sentiment distribution chart
    """
    if not sentiment_summary:
        return None
    
    # Convert to DataFrame for plotting
    sentiment_df = pd.DataFrame.from_dict(sentiment_summary, orient="index").reset_index()
    sentiment_df = sentiment_df.melt(id_vars=["index"], var_name="Sentiment", value_name="Percentage")
    sentiment_df.columns = ["Company", "Sentiment", "Percentage"]
    
    # Create stacked bar chart
    fig = px.bar(
        sentiment_df,
        x="Company",
        y="Percentage",
        color="Sentiment",
        text="Percentage",
        title="Sentiment Distribution Per Company (Brackets show the number of articles for the selected period)",
        color_discrete_map=SENTIMENT_COLORS,
    )
    
    # Update traces and layout
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside')
    fig.update_layout(
        barmode="stack", 
        xaxis_title="Company", 
        yaxis_title="Percentage"
    )
    
    return fig

def render_sentiment_section(keys_data, data_folder, start_date, end_date):
    """
    Render the complete sentiment analysis section
    
    Args:
        keys_data (dict): Company mappings from keys file
        data_folder (str): Path to data folder
        start_date (datetime): Start date for filtering
        end_date (datetime): End date for filtering
    """
    st.subheader("📊 Sentiment Distribution Across Companies")
    
    st.markdown("""Sentiment scores showcase positive, negative and neutral context for company mentions. 
    Take note that AI engine also more broadly classifies negative mentions as ones including a more negative context as well as negative news related to the company itself. 
    """)
    
    # Analyze sentiment
    sentiment_summary = analyze_sentiment_by_company(keys_data, data_folder, start_date, end_date)
    
    if sentiment_summary:
        # Create and display sentiment chart
        fig_sentiment = create_sentiment_chart(sentiment_summary)
        if fig_sentiment:
            st.plotly_chart(fig_sentiment, use_container_width=True)
    else:
        st.warning("No sentiment data available in the selected date range.")

