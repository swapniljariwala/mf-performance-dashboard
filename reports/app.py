"""
Mutual Fund Dashboard - Page 1: Category Tradeoff Explorer
"""
import streamlit as st
import pandas as pd
import plotly.express as px

# Page config
st.set_page_config(page_title="MF Dashboard - Category Explorer", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_parquet('output/all_funds.parquet')
    # Fill NaN values with 0 for AUM (size of bubble)
    df['aum_cr'] = df['aum_cr'].fillna(0)
    return df

df = load_data()

# Filter data based on selected view (drop rows with NaN in x or y axis)
def get_filtered_data(dataframe, x_col, y_col):
    return dataframe.dropna(subset=[x_col, y_col, 'aum_cr'])

# Title
st.title("📊 Mutual Fund Category Explorer")
st.markdown("**Goal**: Visual exploration of tradeoffs to identify best categories")

st.markdown("---")

# Filters in two columns
col1, col2 = st.columns(2)

with col1:
    # Return period selector
    return_period_options = {
        "1 Month": "return_1m",
        "3 Months": "return_3m", 
        "6 Months": "return_6m",
        "1 Year": "return_1y",
        "3 Years": "return_3y",
        "5 Years": "return_5y",
        "Since Inception": "return_since_inception"
    }
    
    selected_period = st.selectbox(
        "Select Return Period:",
        options=list(return_period_options.keys()),
        index=3  # Default to 1 Year
    )
    
    return_col = return_period_options[selected_period]

with col2:
    # View selector
    view_options = {
        "Return vs Risk (SD)": ("sd", "Risk-Return Tradeoff"),
        "Return vs Expense Ratio": ("expense_ratio", "Return-Cost Tradeoff"),
        "Sharpe vs Expense Ratio": ("expense_ratio", "Value Sweet Spot"),
        "Alpha vs Beta": ("beta", "Excess Return vs Market Sensitivity")
    }

    selected_view = st.selectbox(
        "Select View:",
        options=list(view_options.keys()),
        index=0
    )

# Get axis configuration
x_col, title_suffix = view_options[selected_view]

# Set y-axis based on view type
if selected_view == "Sharpe vs Expense Ratio":
    y_col = "sharpe"
elif selected_view == "Alpha vs Beta":
    y_col = "alpha"
else:
    # For return-based views, use the selected return period
    y_col = return_col

# Filter data for this view
df_filtered = get_filtered_data(df, x_col, y_col)

# View toggle
view_mode = st.radio(
    "Visualization Mode:",
    options=["Category Aggregates (Recommended)", "All Individual Funds"],
    horizontal=True
)

# Create scatter plot
st.subheader(f"Graph 1: {selected_view}")

if view_mode == "Category Aggregates (Recommended)":
    # Aggregate by category
    category_stats = df_filtered.groupby('fund_category').agg({
        x_col: 'mean',
        y_col: 'mean',
        'aum_cr': 'sum',  # Total AUM for category
        'sharpe': 'mean',
        'expense_ratio': 'mean',
        'sd': 'mean',
        'fund_name': 'count',  # Number of funds
        'return_1y': 'mean',
        'return_3y': 'mean',
        'return_5y': 'mean'
    }).reset_index()
    
    category_stats.rename(columns={'fund_name': 'num_funds'}, inplace=True)
    
    fig = px.scatter(
        category_stats,
        x=x_col,
        y=y_col,
        size="aum_cr",
        color="fund_category",
        text="fund_category",
        hover_data={
            "fund_category": True,
            "num_funds": True,
            "return_1y": ":.2f",
            "return_3y": ":.2f",
            "return_5y": ":.2f",
            "sharpe": ":.2f",
            "expense_ratio": ":.2f",
            "sd": ":.2f",
            "aum_cr": ":.0f",
            x_col: ":.2f",
            y_col: ":.2f"
        },
        title=f"{title_suffix} - Category Averages",
        labels={
            "sd": "Avg Risk (SD)",
            "return_1y": "Avg 1Y Return (%)",
            "return_3y": "Avg 3Y Return (%)",
            "return_5y": "Avg 5Y Return (%)",
            "expense_ratio": "Avg Expense Ratio (%)",
            "sharpe": "Avg Sharpe Ratio",
            "alpha": "Avg Alpha",
            "beta": "Avg Beta",
            "aum_cr": "Total AUM (Cr)",
            "fund_category": "Category",
            "num_funds": "# of Funds"
        },
        size_max=60
    )
    
    # Add category labels on the plot
    fig.update_traces(textposition='top center', textfont_size=10)
    
else:
    # Individual fund view (original)
    fig = px.scatter(
        df_filtered,
        x=x_col,
        y=y_col,
        size="aum_cr",
        color="fund_category",
        hover_name="fund_name",
        hover_data={
            "fund_category": True,
            "return_1m": ":.2f",
            "return_3m": ":.2f",
            "return_6m": ":.2f",
            "return_1y": ":.2f",
            "return_3y": ":.2f",
            "return_5y": ":.2f",
            "return_since_inception": ":.2f",
            "sharpe": ":.2f",
            "expense_ratio": ":.2f",
            "sd": ":.2f",
            "aum_cr": ":.0f",
            x_col: ":.2f",
            y_col: ":.2f"
        },
        title=f"{title_suffix}",
        labels={
            "sd": "Standard Deviation (Risk)",
            "return_1m": "1-Month Return (%)",
            "return_3m": "3-Month Return (%)",
            "return_6m": "6-Month Return (%)",
            "return_1y": "1-Year Return (%)",
            "return_3y": "3-Year Return (%)",
            "return_5y": "5-Year Return (%)",
            "return_since_inception": "Since Inception Return (%)",
            "expense_ratio": "Expense Ratio (%)",
            "sharpe": "Sharpe Ratio",
            "alpha": "Alpha",
            "beta": "Beta",
            "aum_cr": "AUM (Crores)",
            "fund_category": "Category"
        },
        size_max=30
    )

# Update layout
fig.update_layout(
    height=600,
    xaxis_title=fig.layout.xaxis.title.text,
    yaxis_title=fig.layout.yaxis.title.text,
    hovermode='closest'
)

# Display plot
st.plotly_chart(fig, use_container_width=True)

# Category Summary Cards
st.markdown("---")
st.subheader("📋 Category Summary")

# Calculate category statistics
category_summary = df.groupby('fund_category').agg({
    'return_1y': 'mean',
    'return_3y': 'mean',
    'return_5y': 'mean',
    'sharpe': 'mean',
    'expense_ratio': 'mean',
    'sd': 'mean',
    'aum_cr': ['sum', 'min', 'max'],
    'fund_name': 'count'
}).round(2)

category_summary.columns = ['_'.join(col).strip('_') for col in category_summary.columns]
category_summary = category_summary.reset_index()

# Display in grid
num_cols = 3
categories = category_summary['fund_category'].unique()

for i in range(0, len(categories), num_cols):
    cols = st.columns(num_cols)
    for j, col in enumerate(cols):
        if i + j < len(categories):
            cat = categories[i + j]
            cat_data = category_summary[category_summary['fund_category'] == cat].iloc[0]
            
            with col:
                st.markdown(f"### {cat}")
                st.metric("Funds", int(cat_data['fund_name_count']))
                st.metric("Avg 1Y Return", f"{cat_data['return_1y_mean']:.2f}%")
                st.metric("Avg 3Y Return", f"{cat_data['return_3y_mean']:.2f}%")
                st.metric("Avg Sharpe", f"{cat_data['sharpe_mean']:.2f}")
                st.metric("Avg Risk (SD)", f"{cat_data['sd_mean']:.2f}%")
                st.metric("Avg Expense", f"{cat_data['expense_ratio_mean']:.2f}%")
                st.metric("Total AUM", f"₹{cat_data['aum_cr_sum']:.0f} Cr")

# Data summary
st.markdown("---")
st.markdown(f"**Total Funds**: {len(df)} | **Categories**: {df['fund_category'].nunique()}")
