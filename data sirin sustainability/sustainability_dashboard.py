import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import os

# Configuration
DATA_ROOT = ""  # Default to current directory, can be overridden with environment variable
DATA_FILE = 'Full_Sustainability_Data_Labeled_Scored_Themed.xlsx'

# Set page config
st.set_page_config(
    page_title="SIRIN vs Darnu Sustainability Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
@st.cache_data
def load_data():
    try:
        data_path = os.path.join(DATA_ROOT, DATA_FILE)
        df = pd.read_excel(data_path)
        # Convert Published Date to datetime
        df['Published Date'] = pd.to_datetime(df['Published Date'], format='%m/%d/%Y')
        return df
    except Exception as e:
        st.error(f"Error loading data from {data_path}: {e}")
        return None

# Load the data
df = load_data()

if df is not None:
    # Title
    st.title("🌱 SIRIN vs Darnu Sustainability Dashboard")
    st.markdown("---")
    
    # Filter data for 2025/01 to 2025/09/18
    start_date = pd.to_datetime('2025-01-01')
    end_date = pd.to_datetime('2025-09-18')
    df_filtered = df[(df['Published Date'] >= start_date) & (df['Published Date'] <= end_date)]
    
    # Main Statistics Cards
    st.header("📊 Key Statistics")
    
    # Calculate metrics for each company
    sirin_data = df_filtered[df_filtered['company'] == 'SIRIN']
    darnu_data = df_filtered[df_filtered['company'] == 'Darnu']
    
    # Create 8 cards (4 metrics x 2 companies)
    # Row 1: Articles
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="📰 SIRIN - Total Articles",
            value=f"{len(sirin_data):,}"
        )
    
    with col2:
        st.metric(
            label="📰 Darnu - Total Articles",
            value=f"{len(darnu_data):,}"
        )
    
    # Row 2: Impressions
    col3, col4 = st.columns(2)
    
    with col3:
        sirin_impressions = sirin_data['Impressions'].sum()
        st.metric(
            label="👁️ SIRIN - Total Impressions",
            value=f"{sirin_impressions:,.0f}"
        )
    
    with col4:
        darnu_impressions = darnu_data['Impressions'].sum()
        st.metric(
            label="👁️ Darnu - Total Impressions",
            value=f"{darnu_impressions:,.0f}"
        )
    
    # Row 3: BMQ
    col5, col6 = st.columns(2)
    
    with col5:
        sirin_bmq = sirin_data['BMQ'].mean()
        st.metric(
            label="⭐ SIRIN - Average BMQ",
            value=f"{sirin_bmq:.2f}"
        )
    
    with col6:
        darnu_bmq = darnu_data['BMQ'].mean()
        st.metric(
            label="⭐ Darnu - Average BMQ",
            value=f"{darnu_bmq:.2f}"
        )
    
    # Row 4: Sustainability Score
    col7, col8 = st.columns(2)
    
    with col7:
        sirin_sustainability = sirin_data['Sustainability_Score'].mean()
        st.metric(
            label="🌿 SIRIN - Average Sustainability Score",
            value=f"{sirin_sustainability:.2f}"
        )
    
    with col8:
        darnu_sustainability = darnu_data['Sustainability_Score'].mean()
        st.metric(
            label="🌿 Darnu - Average Sustainability Score",
            value=f"{darnu_sustainability:.2f}"
        )
    
    # Explanation of metrics
    st.markdown("### 📖 About the Metrics")
    st.info("""
    **BMQ (Brand Media Quality)**: A quality score between 0 and 1, determined by how many times the company was mentioned in the article and how high the outlet ranks on PageRank.
    
    **Sustainability Score**: A score between 1 and 5 which shows how much an article was actually about sustainability and how much the company in question was involved with this sustainability.
    """)
    
    st.markdown("---")
    
    # Time Series Analysis
    st.header("📈 Articles Over Time")
    
    # Create tabs for different metrics
    tab1, tab2 = st.tabs(["📰 Number of Articles", "👁️ Impressions"])
    
    with tab1:
        # Group by month and company for article count
        monthly_articles = df_filtered.groupby([
            df_filtered['Published Date'].dt.to_period('M'), 
            'company'
        ]).size().reset_index(name='Article_Count')
        
        monthly_articles['Published Date'] = monthly_articles['Published Date'].astype(str)
        
        fig_articles = px.line(
            monthly_articles, 
            x='Published Date', 
            y='Article_Count', 
            color='company',
            title="Number of Articles by Month",
            markers=True
        )
        fig_articles.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Articles",
            hovermode='x unified'
        )
        st.plotly_chart(fig_articles, use_container_width=True)
    
    with tab2:
        # Group by month and company for impressions
        monthly_impressions = df_filtered.groupby([
            df_filtered['Published Date'].dt.to_period('M'), 
            'company'
        ])['Impressions'].sum().reset_index()
        
        monthly_impressions['Published Date'] = monthly_impressions['Published Date'].astype(str)
        
        fig_impressions = px.line(
            monthly_impressions, 
            x='Published Date', 
            y='Impressions', 
            color='company',
            title="Impressions by Month",
            markers=True
        )
        fig_impressions.update_layout(
            xaxis_title="Month",
            yaxis_title="Impressions",
            hovermode='x unified'
        )
        st.plotly_chart(fig_impressions, use_container_width=True)
    
    st.markdown("---")
    
    # Share of Voice Analysis
    st.header("🥧 Share of Voice")
    
    # Create tabs for different metrics
    tab3, tab4 = st.tabs(["📰 Articles Share", "👁️ Impressions Share"])
    
    with tab3:
        # Article share
        article_share = df_filtered['company'].value_counts()
        fig_articles_pie = px.pie(
            values=article_share.values,
            names=article_share.index,
            title="Share of Articles by Company"
        )
        st.plotly_chart(fig_articles_pie, use_container_width=True)
    
    with tab4:
        # Impressions share
        impressions_share = df_filtered.groupby('company')['Impressions'].sum()
        fig_impressions_pie = px.pie(
            values=impressions_share.values,
            names=impressions_share.index,
            title="Share of Impressions by Company"
        )
        st.plotly_chart(fig_impressions_pie, use_container_width=True)
    
    # Themes Analysis
    st.subheader("📋 All Sustainability Themes by Company")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("**🏢 SIRIN Themes**")
        sirin_themes = sirin_data['Sustainability_Theme'].value_counts()
        if not sirin_themes.empty:
            sirin_df = pd.DataFrame({
                'Theme': sirin_themes.index,
                'Count': sirin_themes.values
            })
            st.dataframe(sirin_df, use_container_width=True, hide_index=True)
            st.caption(f"Total unique themes: {len(sirin_themes)}")
        else:
            st.info("No themes available for SIRIN")
    
    with col_right:
        st.markdown("**🏢 Darnu Themes**")
        darnu_themes = darnu_data['Sustainability_Theme'].value_counts()
        if not darnu_themes.empty:
            darnu_df = pd.DataFrame({
                'Theme': darnu_themes.index,
                'Count': darnu_themes.values
            })
            st.dataframe(darnu_df, use_container_width=True, hide_index=True)
            st.caption(f"Total unique themes: {len(darnu_themes)}")
        else:
            st.info("No themes available for Darnu")
    
    st.markdown("---")
    
    # Top Sustainability Themes
    st.header("🎯 Top Sustainability Themes by Company")
    
    # Create tabs for different metrics
    tab5, tab6 = st.tabs(["📰 By Article Count", "👁️ By Impressions"])
    
    with tab5:
        # Top themes by article count
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("🏢 SIRIN")
            sirin_themes_count = sirin_data['Sustainability_Theme'].value_counts().head(5)
            if not sirin_themes_count.empty:
                fig_sirin_count = px.bar(
                    x=sirin_themes_count.values,
                    y=sirin_themes_count.index,
                    orientation='h',
                    title="Top 5 Themes by Article Count",
                    labels={'x': 'Number of Articles', 'y': 'Sustainability Theme'}
                )
                fig_sirin_count.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_sirin_count, use_container_width=True)
            else:
                st.info("No data available for SIRIN")
        
        with col_right:
            st.subheader("🏢 Darnu")
            darnu_themes_count = darnu_data['Sustainability_Theme'].value_counts().head(5)
            if not darnu_themes_count.empty:
                fig_darnu_count = px.bar(
                    x=darnu_themes_count.values,
                    y=darnu_themes_count.index,
                    orientation='h',
                    title="Top 5 Themes by Article Count",
                    labels={'x': 'Number of Articles', 'y': 'Sustainability Theme'}
                )
                fig_darnu_count.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_darnu_count, use_container_width=True)
            else:
                st.info("No data available for Darnu")
    
    with tab6:
        # Top themes by impressions
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("🏢 SIRIN")
            sirin_themes_impressions = sirin_data.groupby('Sustainability_Theme')['Impressions'].sum().sort_values(ascending=True).tail(5)
            if not sirin_themes_impressions.empty:
                fig_sirin_impressions = px.bar(
                    x=sirin_themes_impressions.values,
                    y=sirin_themes_impressions.index,
                    orientation='h',
                    title="Top 5 Themes by Impressions",
                    labels={'x': 'Impressions', 'y': 'Sustainability Theme'}
                )
                fig_sirin_impressions.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_sirin_impressions, use_container_width=True)
            else:
                st.info("No data available for SIRIN")
        
        with col_right:
            st.subheader("🏢 Darnu")
            darnu_themes_impressions = darnu_data.groupby('Sustainability_Theme')['Impressions'].sum().sort_values(ascending=True).tail(5)
            if not darnu_themes_impressions.empty:
                fig_darnu_impressions = px.bar(
                    x=darnu_themes_impressions.values,
                    y=darnu_themes_impressions.index,
                    orientation='h',
                    title="Top 5 Themes by Impressions",
                    labels={'x': 'Impressions', 'y': 'Sustainability Theme'}
                )
                fig_darnu_impressions.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_darnu_impressions, use_container_width=True)
            else:
                st.info("No data available for Darnu")

else:
    st.error("Unable to load data. Please check the file path and try again.")
