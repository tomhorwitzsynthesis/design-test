# SIRIN vs Darnu Sustainability Dashboard

A Streamlit dashboard for analyzing sustainability-related articles and media coverage for SIRIN and Darnu companies.

## Features

- **Key Statistics**: Side-by-side comparison of articles, impressions, BMQ, and sustainability scores
- **Time Series Analysis**: Line charts showing article trends over time (January - September 2025)
- **Share of Voice**: Pie charts comparing market share between companies
- **Top Themes**: Analysis of the most prominent sustainability themes for each company

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Place your data file `Full_Sustainability_Data_Labeled_Scored_Themed.xlsx` in the same directory as the dashboard
2. Run the dashboard:
   ```bash
   streamlit run sustainability_dashboard.py
   ```

## Configuration

You can set the `DATA_ROOT` environment variable to specify a different directory for the data file:

```bash
export DATA_ROOT=/path/to/your/data
streamlit run sustainability_dashboard.py
```

## Data Requirements

The dashboard expects an Excel file with the following columns:
- `Published Date`: Article publication date
- `company`: Company name (SIRIN or Darnu)
- `Impressions`: Number of impressions
- `BMQ`: Brand Media Quality score
- `Sustainability_Score`: Sustainability content score
- `Sustainability_Theme`: Theme classification

## Time Period

The dashboard analyzes data from January 1, 2025 to September 18, 2025.

