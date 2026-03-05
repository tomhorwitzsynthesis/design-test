"""
Trends Analysis Module for SIRIN Monitoring Dashboard
Handles monthly trends for media mentions and volume analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from config import COUNTRY_CODES, TRENDS_MONTHS, CHART_CONFIG
from utils import get_company_data, extract_date

def prepare_trends_data(keys_data, data_folder):
    """
    Prepare time series data for trends analysis
    
    Args:
        keys_data (dict): Company mappings from keys file
        data_folder (str): Path to data folder
        
    Returns:
        dict: Time series data for each company
    """
    # Get the current month and year
    now = pd.Timestamp.now()
    previous_month = now.month - 1 if now.month > 1 else 12
    previous_year = now.year if now.month > 1 else now.year - 1
    
    # Define the past months for trends
    date_range = pd.date_range(
        end=pd.Timestamp(previous_year, previous_month, 1), 
        periods=TRENDS_MONTHS, 
        freq='MS'
    )
    month_labels = [date.strftime('%b %Y') for date in date_range]
    
    # Dictionary to store time-series data
    time_series_data = {}
    
    for company, filename in keys_data.items():
        company_lower = company.lower()
        df = get_company_data(data_folder, company)
        
        if not df.empty:
            # Create "Published Date" if it's missing
            if "Published Date" not in df.columns:
                df["Published Date"] = df["Snippet"].apply(
                    lambda x: extract_date(x) if isinstance(x, str) else None
                )
            
            if "Published Date" in df.columns:
                df["Published Date"] = pd.to_datetime(df["Published Date"], format="%m/%d/%Y", errors="coerce")
                df["Month"] = df["Published Date"].dt.to_period("M")
                df["MonthStr"] = df["Month"].dt.strftime('%b %Y')
                
                if company.upper() == "SIRIN":
                    # SIRIN Total
                    for month in date_range:
                        month_str = month.strftime('%b %Y')
                        volume = df[df["Month"] == month.to_period("M")].shape[0]
                        time_series_data.setdefault("SIRIN Total", {"Month": [], "Volume": []})
                        time_series_data["SIRIN Total"]["Month"].append(month_str)
                        time_series_data["SIRIN Total"]["Volume"].append(volume)
                    
                    # SIRIN per country
                    for country, code in COUNTRY_CODES.items():
                        if "Country" in df.columns:
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
                    # Other companies
                    for month in date_range:
                        month_str = month.strftime('%b %Y')
                        month_period = month.to_period("M")
                        volume = df[df["Month"] == month_period].shape[0]
                        time_series_data.setdefault(company, {"Month": [], "Volume": []})
                        time_series_data[company]["Month"].append(month_str)
                        time_series_data[company]["Volume"].append(volume)
    
    # Ensure all companies have data for all months
    for company in time_series_data.keys():
        if len(time_series_data[company]["Month"]) == 0:
            time_series_data[company]["Month"] = [month.strftime('%b %Y') for month in date_range]
            time_series_data[company]["Volume"] = [0] * len(date_range)
    
    return time_series_data, month_labels

def create_trends_chart(time_series_data, month_labels):
    """
    Create line chart for monthly trends
    
    Args:
        time_series_data (dict): Time series data for each company
        month_labels (list): Month labels for x-axis
        
    Returns:
        plotly.Figure: Line chart figure
    """
    # Convert to DataFrame
    time_series_df = pd.concat([
        pd.DataFrame({
            "Company": company, 
            "Month": data["Month"], 
            "Volume": data["Volume"]
        })
        for company, data in time_series_data.items()
    ], ignore_index=True)
    
    # Create line chart
    fig_volume = px.line(
        time_series_df,
        x="Month",
        y="Volume",
        color="Company",
        markers=CHART_CONFIG["line_markers"],
        title="Monthly Media Mentions Volume Trend per Company",
    )
    
    # Update layout
    fig_volume.update_layout(
        xaxis_title="Month",
        yaxis_title="Media Mentions Volume (Articles)",
        xaxis=dict(categoryorder="array", categoryarray=month_labels)
    )
    
    return fig_volume

def render_trends_section(keys_data, data_folder):
    """
    Render the complete trends analysis section
    
    Args:
        keys_data (dict): Company mappings from keys file
        data_folder (str): Path to data folder
    """
    st.subheader("📈 Monthly Trends for Media Mentions & Online Reputation Volume")
    
    st.markdown("Media mentions shows overall number of company mentions for a given period.")
    
    # Prepare trends data
    time_series_data, month_labels = prepare_trends_data(keys_data, data_folder)
    
    if time_series_data:
        # Create and display trends chart
        fig_volume = create_trends_chart(time_series_data, month_labels)
        st.plotly_chart(fig_volume, use_container_width=True)
    else:
        st.warning("No trends data available.")

