"""
News Analysis Module for SIRIN Monitoring Dashboard
Handles company performance overview, archetype analysis, and scatter plot generation
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from config import CHART_CONFIG, DISPLAY_NAME_MAP
from utils import get_company_data

def analyze_company_performance(keys_data, data_folder):
    """
    Analyze company performance and extract Volume, Quality, and Archetypes
    
    Args:
        keys_data (dict): Company mappings from keys file
        data_folder (str): Path to data folder
        
    Returns:
        dict: Company summary with Volume, Quality, and Archetypes
    """
    company_summary = {}
    
    for company, filename in keys_data.items():
        company_lower = company.lower()
        df = get_company_data(data_folder, company)
        
        if not df.empty:
            volume = len(df)  # Number of rows = number of articles
            quality = df["BMQ"].mean() if "BMQ" in df.columns else 0  # Average of BMQ column
            
            # Compute Archetype Percentages
            if "Top Archetype" in df.columns:
                archetype_counts = df["Top Archetype"].value_counts(normalize=True) * 100
                top_3_archetypes = archetype_counts.nlargest(3)
                
                # Format as a vertical list using <br> for new lines
                archetype_text = "<br>".join([
                    f"{archetype} ({percent:.1f}%)" 
                    for archetype, percent in top_3_archetypes.items()
                ])
            else:
                archetype_text = "No Archetype Data"
            
            # Store company metrics
            company_summary[company] = {
                "Volume": volume,
                "Quality": round(quality, 2) if not pd.isna(quality) else 0,
                "Archetypes": archetype_text
            }
    
    return company_summary

def create_performance_scatter_plot(company_summary):
    """
    Create scatter plot showing Volume vs Quality with Archetypes
    
    Args:
        company_summary (dict): Company performance data
        
    Returns:
        plotly.Figure: Scatter plot figure
    """
    # Convert dictionary to DataFrame
    summary_df = pd.DataFrame.from_dict(company_summary, orient="index").reset_index()
    summary_df.columns = ["Company", "Volume", "Quality", "Archetypes"]
    
    # Create Scatter Plot (Volume vs. Quality)
    fig = px.scatter(
        summary_df,
        x="Volume",
        y="Quality",
        text="Company",
        hover_data=["Archetypes"],
        size_max=15,
        title="Company Performance (Volume vs. Quality) with Archetypes",
    )
    
    # Enhance the plot: Position company names correctly
    fig.update_traces(
        textposition="top center",
        marker=dict(
            size=CHART_CONFIG["scatter_size"], 
            color=CHART_CONFIG["scatter_color"]
        )
    )
    
    # Avoid text overlap: Calculate dynamic Y-positions
    y_positions = []
    min_y_distance = 0.03 * summary_df["Quality"].max()
    
    for i, row in summary_df.iterrows():
        y_pos = row["Quality"] - min_y_distance
        
        # If another label is too close, shift the new one further down
        while any(abs(y_pos - prev_y) < min_y_distance for prev_y in y_positions):
            y_pos -= min_y_distance
        
        y_positions.append(y_pos)
        
        fig.add_annotation(
            x=row["Volume"],
            y=y_pos,
            text=f"<b>{row['Company']}</b><br>{row['Archetypes']}",
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
    
    return fig

def render_news_section(keys_data, data_folder):
    """
    Render the complete news section with company performance overview
    
    Args:
        keys_data (dict): Company mappings from keys file
        data_folder (str): Path to data folder
    """
    st.header("News")
    st.subheader("📊 Company Performance Overview")
    
    st.markdown("""
    This matrix showcases **three top brand archetypes** for each market player. The archetypes are determined by analyzing the content of the articles and mentions, and identifying key values that are communicated.

    - **X-axis** represents the **volume of articles** captured since the start of this year.  
    - **Y-axis** shows the **quality of sources**, determined by the authority of the web domain that features the content. The higher the quality, the more authoritative and established the domains or websites are that mention the brands.

    This matrix is based on a larger brand mention sample over an extended period of time to more accurately determine the brand archetypes communicated by brands.

    Read more about brand archetypes here: [Brandtypes](https://www.comp-os.com/brandtypes).
    """)
    
    # Analyze company performance
    company_summary = analyze_company_performance(keys_data, data_folder)
    
    if company_summary:
        # Create and display scatter plot
        fig = create_performance_scatter_plot(company_summary)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No company performance data available.")

