# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Scrape fund data
```bash
# Scrape all categories listed in category_urls.txt
python scrape_etmoney_multicap.py

# Scrape with options
python scrape_etmoney_multicap.py --limit 10 --outfile my_funds.csv --sleep 1.5
```

### Convert CSVs to Parquet
```bash
python convert_to_parquet.py
```

### Run the dashboard
```bash
streamlit run reports/Category_Explorer.py
```

### Setup (first time)
```bash
pip install -r requirements.txt
playwright install chromium
```

## Architecture

This is a two-stage pipeline: scrape -> visualize.

**Stage 1 - Scraper** (`scrape_etmoney_multicap.py`):
- `ETMoneyScraper` class takes a category URL and scrapes all fund pages in that category
- Primary strategy: `requests` + `BeautifulSoup`, parsing `__NEXT_DATA__` JSON embedded in the page (Next.js site)
- Fallback strategy: Playwright headless Chromium for JavaScript-rendered pages
- `category_urls.txt` lists all category URLs to scrape; the script iterates over all of them
- Output goes to `output/etmoney_<category-name>.csv` per category

**Stage 2 - Converter** (`convert_to_parquet.py`):
- Merges all per-category CSVs into `output/all_funds.parquet`
- Adds a `fund_category` column derived from the filename

**Stage 3 - Dashboard** (`reports/`):
- Streamlit multi-page app; entry point is `reports/Category_Explorer.py`
- Pages live in `reports/pages/` (Streamlit auto-discovers them)
- Loads `output/all_funds.parquet` at startup via `@st.cache_data`
- Page 1 (`Category_Explorer.py`): AUM-weighted category comparison with bubble charts and box plots
- Page 2 (`pages/1_Efficient_Frontier.py`): Pareto-optimal fund selection within a category

## Key data columns

`fund_name`, `fund_url`, `fund_category`, `aum_cr`, `expense_ratio`, `alpha`, `sharpe`, `beta`, `sd`, `fund_age_years`, `largecap_pct`, `midcap_pct`, `smallcap_pct`, `return_1m`, `return_3m`, `return_6m`, `return_1y`, `return_3y`, `return_5y`, `return_since_inception`
