"""
Main SIRIN Monitoring Dashboard
Main entry point that orchestrates all analysis modules and provides the user interface
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from calendar import month_name

# Import configuration and utilities
from config import DATA_FOLDER, AVAILABLE_MONTHS
from utils import load_keys_file, create_month_labels

# Import analysis modules
from analysis.news_analysis import render_news_section
from analysis.sentiment_analysis import render_sentiment_section
from analysis.topic_analysis import render_topic_section
from analysis.media_mentions import render_media_mentions_section
from analysis.trends_analysis import render_trends_section

def setup_sidebar():
    """
    Setup the sidebar with date range selection
    
    Returns:
        tuple: (start_date, end_date, selected_months)
    """
    st.sidebar.markdown("### Select Date Range")
    
    # Create user-facing labels and mapping back to (year, month)
    month_labels, label_to_date = create_month_labels(AVAILABLE_MONTHS)
    
    # Dropdowns for start and end month
    start_label = st.sidebar.selectbox("Start Month", month_labels, index=0)
    end_label = st.sidebar.selectbox("End Month", month_labels, index=len(month_labels) - 1)
    
    start_year, start_month = label_to_date[start_label]
    end_year, end_month = label_to_date[end_label]
    
    # Validate chronological order
    start_idx = AVAILABLE_MONTHS.index((start_year, start_month))
    end_idx = AVAILABLE_MONTHS.index((end_year, end_month))
    
    if start_idx > end_idx:
        st.sidebar.error("Start month must not be after end month.")
        st.stop()
    
    # Compute date range
    start_date = datetime(start_year, start_month, 1)
    if end_month == 12:
        end_date = datetime(end_year + 1, 1, 1)
    else:
        end_date = datetime(end_year, end_month + 1, 1)
    
    # Generate selected_months list for downstream logic
    selected_months = AVAILABLE_MONTHS[start_idx:end_idx + 1]
    
    return start_date, end_date, selected_months

def main():
    """
    Main function to run the dashboard
    """
    st.title("Monitoring Dashboard")
    
    # Setup sidebar and get date range
    start_date, end_date, selected_months = setup_sidebar()
    
    # Load company-file mappings
    keys_data = load_keys_file(DATA_FOLDER)
    
    if not keys_data:
        st.error("Error: keys.txt file is missing or could not be loaded from the data folder!")
        st.stop()
    
    # Render all analysis sections
    try:
        # News section
        render_news_section(keys_data, DATA_FOLDER)
        
        # Sentiment analysis section
        render_sentiment_section(keys_data, DATA_FOLDER, start_date, end_date)
        
        # Topic analysis section
        render_topic_section(keys_data, DATA_FOLDER, start_date, end_date)
        
        # Media mentions section
        render_media_mentions_section(keys_data, DATA_FOLDER, start_date, end_date)
        
        # Trends section
        render_trends_section(keys_data, DATA_FOLDER)
        
    except Exception as e:
        st.error(f"An error occurred while rendering the dashboard: {str(e)}")
        st.exception(e)

if __name__ == "__main__":
    main()
