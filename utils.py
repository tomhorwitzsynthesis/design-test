"""
Utility functions for SIRIN Monitoring Dashboard
Contains helper functions for data processing, date handling, and common operations
"""

import pandas as pd
import re
from datetime import datetime, timedelta
import json
import os
from config import DISPLAY_NAME_MAP, COUNTRY_CODES

def extract_date(snippet):
    """
    Extract date from snippet text using various patterns
    
    Args:
        snippet (str): Text snippet containing date information
        
    Returns:
        str: Formatted date string (MM/DD/YYYY) or None if no date found
    """
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

def load_keys_file(data_folder):
    """
    Load company-file mappings from JSON keys file
    
    Args:
        data_folder (str): Path to data folder containing keys.txt
        
    Returns:
        dict: Company mappings or empty dict if file not found
    """
    keys_file = os.path.join(data_folder, "keys.txt")
    
    if not os.path.exists(keys_file):
        return {}
    
    try:
        with open(keys_file, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading keys file: {e}")
        return {}

def get_company_data(data_folder, company, sheet_name="Raw Data"):
    """
    Load company data from Excel file
    
    Args:
        data_folder (str): Path to data folder
        company (str): Company name
        sheet_name (str): Excel sheet name to load
        
    Returns:
        pd.DataFrame: Company data or empty DataFrame if file not found
    """
    company_lower = company.lower()
    file_path = os.path.join(data_folder, "agility", f"{company_lower}_agility.xlsx")
    
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    try:
        return pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        print(f"Error loading data for {company}: {e}")
        return pd.DataFrame()

def filter_data_by_date_range(df, start_date, end_date, date_column="Published Date"):
    """
    Filter DataFrame by date range
    
    Args:
        df (pd.DataFrame): Input DataFrame
        start_date (datetime): Start date for filtering
        end_date (datetime): End date for filtering
        date_column (str): Name of date column
        
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    if date_column not in df.columns:
        return df
    
    df_copy = df.copy()
    df_copy[date_column] = pd.to_datetime(df_copy[date_column], errors='coerce')
    df_copy = df_copy.dropna(subset=[date_column])
    
    return df_copy[
        (df_copy[date_column] >= pd.to_datetime(start_date)) & 
        (df_copy[date_column] <= pd.to_datetime(end_date))
    ]

def create_month_labels(available_months):
    """
    Create user-facing month labels for dropdowns
    
    Args:
        available_months (list): List of (year, month) tuples
        
    Returns:
        tuple: (month_labels, label_to_date_mapping)
    """
    from calendar import month_name
    
    month_labels = [f"{month_name[m]} {y}" for y, m in available_months]
    label_to_date = {label: (y, m) for label, (y, m) in zip(month_labels, available_months)}
    
    return month_labels, label_to_date

