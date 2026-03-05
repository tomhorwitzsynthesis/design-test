"""
Media Mentions Module for SIRIN Monitoring Dashboard
Handles media mentions coverage share analysis and visualization
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from config import CHART_CONFIG, COUNTRY_CODES
from utils import get_company_data, filter_data_by_date_range

def load_media_mentions_data(keys_data, data_folder, start_date, end_date):
    """
    Load and filter media mentions data for all companies
    
    Args:
        keys_data (dict): Company mappings from keys file
        data_folder (str): Path to data folder
        start_date (datetime): Start date for filtering
        end_date (datetime): End date for filtering
        
    Returns:
        list: List of DataFrames with company data
    """
    non_organic_data = []
    
    for company, filename in keys_data.items():
        company_lower = company.lower()
        df_agility = get_company_data(data_folder, company)
        
        if not df_agility.empty:
            if "Published Date" not in df_agility.columns:
                st.warning(f"{company}: Missing 'Published Date' column. Skipped.")
                continue
            
            # Filter by date range
            df_filtered = filter_data_by_date_range(df_agility, start_date, end_date)
            
            if not df_filtered.empty:
                df_filtered["Company"] = company  # Tag rows with company
                non_organic_data.append(df_filtered)
        else:
            st.warning(f"{company} file not found.")
    
    return non_organic_data

def plot_mention_share(dataframe, title):
    """
    Create pie chart for media mentions share
    
    Args:
        dataframe (pd.DataFrame): Data to plot
        title (str): Chart title
        
    Returns:
        plotly.Figure: Pie chart figure
    """
    if dataframe.empty:
        st.info("No data available for this period.")
        return None
    
    # Count mentions per company
    count_df = dataframe.groupby("Company").size().reset_index(name="Volume")
    total_mentions = count_df["Volume"].sum()
    count_df["Percentage"] = (count_df["Volume"] / total_mentions) * 100
    
    # Create pie chart
    fig_pie = px.pie(
        count_df,
        names="Company",
        values="Volume",
        title=title,
        hover_data=["Percentage"],
        labels={"Percentage": "% of Total"},
        color="Company",
        color_discrete_map=CHART_CONFIG["pie_color_override"]
    )
    
    # Update traces
    fig_pie.update_traces(
        textinfo="label+percent",
        hovertemplate="%{label}: %{value} articles (%{customdata[0]:.1f}%)"
    )
    
    return fig_pie

def render_media_mentions_section(keys_data, data_folder, start_date, end_date):
    """
    Render the complete media mentions section
    
    Args:
        keys_data (dict): Company mappings from keys file
        data_folder (str): Path to data folder
        start_date (datetime): Start date for filtering
        end_date (datetime): End date for filtering
    """
    st.subheader("📰 Media Mentions Coverage Share 2025")
    
    st.markdown("""
    The Media Mentions show all articles that mention the specific brand in news outlets. These can range from smaller local outlets to international ones.
    """)
    
    # Load media mentions data
    non_organic_data = load_media_mentions_data(keys_data, data_folder, start_date, end_date)
    
    if non_organic_data:
        # Combine all data
        full_df = pd.concat(non_organic_data, ignore_index=True)
        
        # Create tabs by region
        tab_total, tab_lt, tab_lv, tab_ee = st.tabs([
            "🌍 Total", "🇱🇹 Lithuania", "🇱🇻 Latvia", "🇪🇪 Estonia"
        ])
        
        # Total tab
        with tab_total:
            fig_total = plot_mention_share(full_df, "Total Share of Media Mentions Coverage")
            if fig_total:
                st.plotly_chart(fig_total, use_container_width=True)
        
        # Lithuania tab
        with tab_lt:
            if "Country" in full_df.columns:
                fig_lt = plot_mention_share(
                    full_df[full_df["Country"] == "Lithuania"], 
                    "Lithuania Media Mentions Coverage"
                )
                if fig_lt:
                    st.plotly_chart(fig_lt, use_container_width=True)
            else:
                st.info("Country information not available.")
        
        # Latvia tab
        with tab_lv:
            if "Country" in full_df.columns:
                fig_lv = plot_mention_share(
                    full_df[full_df["Country"] == "Latvia"], 
                    "Latvia Media Mentions Coverage"
                )
                if fig_lv:
                    st.plotly_chart(fig_lv, use_container_width=True)
            else:
                st.info("Country information not available.")
        
        # Estonia tab
        with tab_ee:
            if "Country" in full_df.columns:
                fig_ee = plot_mention_share(
                    full_df[full_df["Country"] == "Estonia"], 
                    "Estonia Media Mentions Coverage"
                )
                if fig_ee:
                    st.plotly_chart(fig_ee, use_container_width=True)
            else:
                st.info("Country information not available.")
    else:
        st.warning("No data loaded in the selected date range.")

