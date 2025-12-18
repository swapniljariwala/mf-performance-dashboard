# Mutual Fund Dashboard - Design Document

**Goal**: Help decide which fund category to invest in and which fund to buy within the category

**Approach**: Multi-dimensional tradeoff analysis (Risk vs Return vs AUM vs Expense Ratio)

---

## Available Data

### Columns in Dataset
```
fund_name, fund_url, fund_age_years, aum_cr, expense_ratio, alpha, sharpe, beta, sd, 
large_cap_pct, mid_cap_pct, small_cap_pct, other_cap_pct, 
return_1m, return_3m, return_6m, return_1y, return_3y, return_5y, return_since_inception
```

### Fund Categories
- Aggressive Hybrid (58 funds)
- Dynamic Asset Allocation (64 funds)
- Flexicap (64 funds)
- International (32 funds)
- Large Cap (64 funds)
- Mid Cap (58 funds)
- Multi Cap (59 funds)
- Small Cap (59 funds)
- Value Oriented (142 funds)

**Total**: 600 funds across 9 categories

---

## Dashboard Structure

### Page 1: Category Tradeoff Explorer

**Purpose**: Visual exploration of tradeoffs to identify best categories

#### Interactive Visualizations

1. **Primary Tradeoff Scatter Plot**
   - X-axis: Risk (SD or Beta) 
   - Y-axis: Return (selectable: 1y/3y/5y)
   - Bubble size: AUM 
   - Color: Category
   - Tooltip: Fund name, expense ratio, Sharpe ratio, alpha
   
2. **Efficient Frontier**
   - Highlight Pareto-optimal funds (best risk-return combinations)
   - Show dominated vs non-dominated funds

3. **Multiple View Options**
   - Return vs Risk (SD) - colored by expense ratio
   - Return vs Expense Ratio - sized by AUM
   - Sharpe vs Expense Ratio - value sweet spot
   - Alpha vs Beta - excess return vs market sensitivity
   - Risk-Adjusted Return (Sharpe) vs Cost efficiency

#### Interactive Filters (Sliders)
- Min/Max Return range
- Max acceptable risk (SD)
- Min AUM (avoid very small funds)
- Max expense ratio tolerance
- Fund age filter

#### Category Summary Cards
For each category display:
- Average return (1y, 3y, 5y)
- Average Sharpe ratio
- Average expense ratio
- Average risk (SD)
- Number of funds
- Best fund in category
- AUM range

---

### Page 2: Customizable Tradeoff Matrix

**Purpose**: Personalize analysis based on investor priorities

#### Priority Sliders (0-100%)
- Importance of Returns
- Importance of Low Risk  
- Importance of Low Cost (expense ratio)
- Importance of Fund Size (AUM)

#### Dynamic Features
- **Real-time Scoring**: Recalculate composite scores based on weight adjustments
- **Tradeoff Visualization**: Show gains/losses when adjusting priorities
- **Dominated Solutions**: Gray out funds strictly worse on all dimensions
- **Top Recommendations**: Auto-update top 10 funds based on custom weights

#### Composite Score Formula
```
Score = (w1 × normalized_return) + 
        (w2 × normalized_sharpe) - 
        (w3 × normalized_expense_ratio) + 
        (w4 × normalized_log_aum)
```

---

### Page 3: Pairwise Tradeoff Analysis

**Purpose**: Deep dive into specific metric relationships

#### Configurable Scatter Plots
- **X-axis selector**: Choose any metric
- **Y-axis selector**: Choose any metric
- **Size dimension**: Choose metric for bubble size
- **Color dimension**: Category or another metric
- **Filters**: By category, metric ranges

#### Example Analyses
1. "High return funds - what's the risk/cost penalty?"
2. "Low cost funds - what's the return sacrifice?"
3. "Large AUM funds - are they less risky but lower return?"
4. "Does fund age correlate with performance?"

#### Statistical Overlays
- Regression lines
- Correlation coefficients
- Trend zones
- Outlier identification

---

### Page 4: Category Comparison Dashboard

**Purpose**: Compare tradeoffs across categories

#### Visualizations
1. **Box Plots**: Distribution of each metric per category
   - Returns (1y, 3y, 5y)
   - Risk metrics (SD, Beta)
   - Cost (expense ratio)
   - Size (AUM)

2. **Category Efficient Frontier Overlay**
   - Show best funds from each category
   - Identify which categories dominate others

3. **Heatmap**: Average metrics by category
   - Rows: Categories
   - Columns: Metrics
   - Color: Performance level

4. **Radar Charts**: Multi-dimensional category profiles
   - Compare 2-3 categories simultaneously
   - See strengths/weaknesses

---

### Page 5: Fund Selector within Category

**Purpose**: Once category chosen, find best fund(s)

#### Smart Ranking Table
Columns:
- Fund name (linked to fund_url)
- Composite score
- Return 1y / 3y / 5y (color-coded)
- Sharpe ratio
- Expense ratio
- AUM
- Alpha
- SD
- Age

#### Features
- Sortable by any column
- Multi-select for comparison
- Export selected funds
- Color coding:
  - Green: Top 25%
  - Yellow: Middle 50%
  - Red: Bottom 25%

#### Auto-Recommendations
- **Best Overall**: Highest composite score
- **Best Value**: Lowest expense ratio in top performers
- **Best Risk-Adjusted**: Highest Sharpe ratio
- **Aggressive Pick**: Highest returns
- **Conservative Pick**: Lowest SD with decent returns

#### Side-by-Side Comparison Tool
- Select 2-5 funds
- See all metrics in comparison table
- Radar chart overlay
- Highlight differences

---

### Page 6: Fund Deep Dive

**Purpose**: Final validation before investment decision

#### Fund Profile
- All metrics displayed
- Fund age and URL
- Portfolio composition (pie chart):
  - Large cap %
  - Mid cap %
  - Small cap %
  - Other %

#### Benchmarking
- Percentile ranking within category
- Comparison bars vs category average
- Comparison bars vs category best
- Visual indicators if fund is above/below average

#### Risk-Return Positioning
- Show fund's position on category scatter plot
- Highlight if fund is on efficient frontier
- Show nearest comparable funds

#### Red Flags / Green Flags
- **Red Flags**:
  - Very high expense ratio (>2%)
  - Very low AUM (<100 Cr)
  - Negative alpha
  - Very high SD vs category
  
- **Green Flags**:
  - Top quartile returns
  - High Sharpe ratio
  - Low expense ratio
  - Consistent performer across timeframes

---

## Technical Implementation

### Technology Stack
- **Streamlit**: Main dashboard framework
- **Pandas**: Data manipulation
- **Plotly**: Interactive visualizations
- **Plotly Express**: Quick multi-dimensional plots
- **PyArrow**: Fast parquet loading

### Key Visualizations
1. **Scatter plots** (2D and 3D)
2. **Box plots** for distributions
3. **Heatmaps** for correlation/comparison
4. **Radar charts** for multi-metric comparison
5. **Parallel coordinates** for all dimensions simultaneously
6. **Bar charts** for rankings
7. **Pie charts** for portfolio composition

### Special Features to Implement

1. **Pareto Frontier Calculation**
   - Identify non-dominated solutions
   - Multi-objective optimization

2. **Constraint-based Search**
   - Example: "Show funds with return>12%, SD<15%, expense<1.5%"
   - Boolean filters with AND/OR logic

3. **Sensitivity Analysis**
   - "How does ranking change if I prioritize X over Y?"
   - Dynamic weight adjustment visualization

4. **Correlation Matrix**
   - See which metrics move together
   - Identify redundant vs complementary metrics

5. **Tradeoff Navigator**
   - "If I want 15% return, what's minimum risk/cost?"
   - Interactive constraint solver

### User Experience Features
- Tooltips explaining each metric
- Help section with definitions
- Preset filter configurations (Conservative, Balanced, Aggressive)
- Save/load filter preferences
- Export analysis reports
- Responsive design
- Fast loading with caching

---

## Key Metrics Explained

### Performance Metrics
- **Returns (1m, 3m, 6m, 1y, 3y, 5y)**: Historical returns over different periods
- **Alpha**: Excess return over benchmark (positive = outperforming)
- **Sharpe Ratio**: Risk-adjusted return (higher = better return per unit risk)

### Risk Metrics
- **Beta**: Market sensitivity (>1 = more volatile than market)
- **SD (Standard Deviation)**: Volatility/risk (lower = more stable)

### Cost Metrics
- **Expense Ratio**: Annual fund management fee (lower = better)

### Size Metrics
- **AUM (Assets Under Management)**: Fund size in Crores (too low = risky, established funds are larger)
- **Fund Age**: Years since inception

---

## Decision Framework

### Step 1: Define Your Profile
- Risk tolerance: Low / Medium / High
- Time horizon: Short (<1y) / Medium (1-3y) / Long (>3y)
- Cost sensitivity: How important are low fees?
- Fund size preference: Prefer established (large AUM) or nimble (smaller AUM)?

### Step 2: Explore Category Tradeoffs
- Use scatter plots to visualize risk-return tradeoffs
- Apply filters based on your constraints
- Identify categories on the efficient frontier

### Step 3: Set Custom Priorities
- Adjust importance weights
- See how recommendations change
- Find your optimal category

### Step 4: Deep Dive into Category
- Examine all funds in chosen category
- Compare top performers
- Check for red flags

### Step 5: Final Fund Selection
- Validate with deep dive page
- Check portfolio composition
- Review all metrics one last time
- Make informed decision

---

## Future Enhancements

### Data Additions
- Historical NAV data for trend analysis
- Benchmark comparisons (Nifty 50, Sensex, category average)
- Dividend history
- Tax implications calculator
- SIP return calculator

### Advanced Analytics
- Machine learning predictions
- Risk clustering analysis
- Portfolio optimization (multiple funds)
- Monte Carlo simulations for future returns
- Drawdown analysis

### Personalization
- User portfolios
- Watchlists
- Alerts for metric changes
- Comparison with owned funds

---

## Deliverables

1. ✅ Parquet data file with all funds and categories
2. ⬜ Streamlit dashboard with 6 pages
3. ⬜ Documentation/user guide
4. ⬜ Requirements.txt with all dependencies
5. ⬜ README with setup instructions

---

**Created**: December 18, 2025
**Last Updated**: December 18, 2025
