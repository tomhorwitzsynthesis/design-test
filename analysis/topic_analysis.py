"""
Topic Analysis Module for SIRIN Monitoring Dashboard
Handles key topics analysis and visualization across companies
"""

import streamlit as st
import pandas as pd
from utils import get_company_data, filter_data_by_date_range

def get_top_topics(dataframes_dict):
    """
    Compute topic counts and return top 5 topics across all companies
    
    Args:
        dataframes_dict (dict): Dictionary of company DataFrames
        
    Returns:
        pd.DataFrame: DataFrame with top topics, counts, and percentages
    """
    topic_counts = {
        "Cluster_Topic1": {},
        "Cluster_Topic2": {},
        "Cluster_Topic3": {}
    }
    
    # Count topics across all companies
    for company, df in dataframes_dict.items():
        if all(col in df.columns for col in topic_counts.keys()):
            for column in topic_counts:
                for topic in df[column].dropna():
                    topic_counts[column][topic] = topic_counts[column].get(topic, 0) + 1
    
    # Combine all topic counts
    all_topic_counts = {}
    for column in topic_counts:
        for topic, count in topic_counts[column].items():
            all_topic_counts[topic] = all_topic_counts.get(topic, 0) + count
    
    # Calculate percentages and get top 5
    total_count = sum(all_topic_counts.values())
    sorted_topics = sorted(all_topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Format results
    topics_data = []
    for topic, count in sorted_topics:
        percentage = (count / total_count) * 100
        topics_data.append({
            "Topic Cluster": topic,
            "Count": count,
            "Percentage": round(percentage, 2)
        })
    
    return pd.DataFrame(topics_data)

def render_topic_tab(tab, topics_df, company_name="Total"):
    """
    Render a single topic tab with topic information
    
    Args:
        tab: Streamlit tab object
        topics_df (pd.DataFrame): Topics data to display
        company_name (str): Name of the company for display
    """
    with tab:
        if topics_df.empty:
            if company_name == "Total":
                st.info("No topics found in this period.")
            else:
                st.info(f"No topics found for {company_name} in the selected date range.")
        else:
            for _, row in topics_df.iterrows():
                st.markdown(
                    f'<div style="display: flex; justify-content: space-between; border: 1px solid #ccc; padding: 5px; border-radius: 5px; margin-bottom: 5px;">'
                    f'<div style="background-color: white; padding: 5px; border-radius: 5px; flex: 1;">{row["Topic Cluster"]}</div>'
                    f'<div style="background-color: lightgray; padding: 5px; border-radius: 5px; margin-left: 10px;">{row["Percentage"]}%</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

def render_topic_section(keys_data, data_folder, start_date, end_date):
    """
    Render the complete topic analysis section
    
    Args:
        keys_data (dict): Company mappings from keys file
        data_folder (str): Path to data folder
        start_date (datetime): Start date for filtering
        end_date (datetime): End date for filtering
    """
    st.subheader("Key Topics")
    
    st.markdown("Key topics reflect main themes across all of the communicating companies, including the number of articles for the company for the given time period.")
    
    # Load and filter data per selected date range
    all_company_data = {}
    for company, filename in keys_data.items():
        df = get_company_data(data_folder, company)
        
        if not df.empty and "Published Date" in df.columns:
            df_filtered = filter_data_by_date_range(df, start_date, end_date)
            if not df_filtered.empty:
                all_company_data[company] = df_filtered
        else:
            st.warning(f"File for {company} not found or missing date column.")
    
    if not all_company_data:
        st.warning("No data found for selected period.")
        return
    
    # Build tab titles with article counts
    tab_titles = ["🌍 Total"]
    for company, df in all_company_data.items():
        article_count = len(df)
        tab_titles.append(f"🏢 {company}: {article_count}")
    
    tabs = st.tabs(tab_titles)
    
    # Render Total tab
    total_df = get_top_topics(all_company_data)
    render_topic_tab(tabs[0], total_df, "Total")
    
    # Render individual company tabs
    for idx, company in enumerate(all_company_data.keys(), start=1):
        company_df = get_top_topics({company: all_company_data[company]})
        render_topic_tab(tabs[idx], company_df, company)

