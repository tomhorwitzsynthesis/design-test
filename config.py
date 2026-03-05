"""
Configuration file for SIRIN Monitoring Dashboard
Contains all constants, settings, and configuration parameters
"""

import os
from calendar import month_name

# Data folder configuration
DATA_FOLDER = "data sirin december"  # Default data folder

# Available data months - Format: list of (year, month_number) tuples
AVAILABLE_MONTHS = [
    (2025, 1), (2025, 2), (2025, 3), (2025, 4), (2025, 5), (2025, 6), (2025, 7), (2025, 8), (2025, 9), (2025, 10), (2025, 11), (2025, 12),
    (2026, 1), (2026, 2)
]

# Company display name mappings
DISPLAY_NAME_MAP = {
    "Darnu": "Darnu",
    "Eika": "Eika", 
    "Kapitel": "Kapitel",
    "Piche": "Piche",
    "Restate": "Restate",
    "SIRIN": "SIRIN",
    "Favorte": "Favorte",
    "Park Rae": "Park Rae",
    "VGP": "VGP",
}

# Country codes for display
COUNTRY_CODES = {
    "Lithuania": "LT", 
    "Latvia": "LV", 
    "Estonia": "EE"
}

# Sentiment color mapping
SENTIMENT_COLORS = {
    "Positive": "green", 
    "Neutral": "grey", 
    "Negative": "red"
}

# Chart configuration
CHART_CONFIG = {
    "scatter_size": 10,
    "scatter_color": "blue",
    "line_markers": True,
    "pie_color_override": {"SIRIN": "#00FF00"}
}

# Date range for trends (past 4 months)
TRENDS_MONTHS = 4

