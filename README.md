# ET Money Multi-Cap Mutual Funds Scraper

A Python scraper that collects all Multi-Cap mutual funds from ET Money, visits each fund's page, and extracts key metrics (AUM, Expense Ratio, Alpha, Sharpe, Beta, Standard Deviation) into a CSV file.

## Features

- **Dual scraping approach**: Uses `requests` + `BeautifulSoup4` for initial fetches, with automatic fallback to Playwright for JavaScript-rendered content
- **Robust data extraction**: Parses structured data (`__NEXT_DATA__`, JSON-LD) and HTML content
- **Proxy support**: Configurable via CLI or environment variables
- **Retry/backoff**: Built-in retry logic for failed requests with exponential backoff
- **Progress logging**: Console logs for tracking scraping progress
- **Error handling**: Gracefully handles missing data and continues scraping

## Data Extracted

For each fund, the scraper extracts:

- **Fund Name**
- **Fund URL**
- **AUM (₹ Cr)** - Assets Under Management in Crores
- **Expense Ratio** (%)
- **Alpha** - Excess return over benchmark
- **Sharpe Ratio** - Risk-adjusted return metric
- **Beta** - Market volatility measure
- **Standard Deviation (SD)** - Volatility measure

## Installation

### Windows

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

   If you encounter execution policy errors, run:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```powershell
   playwright install chromium
   ```

### macOS / Linux

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

## Usage

### Basic Usage

Scrape all Multi-Cap funds and save to default CSV file:

```bash
python scrape_etmoney_multicap.py
```

### Advanced Options

```bash
python scrape_etmoney_multicap.py --limit 10 --outfile my_funds.csv --sleep 1.5 --proxy http://proxy.example.com:8080
```

### CLI Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--limit` | int | None | Maximum number of funds to scrape (None = all) |
| `--outfile` | str | `etmoney_multicap.csv` | Output CSV filename |
| `--sleep` | float | 0.8 | Delay between requests in seconds |
| `--proxy` | str | None | Proxy URL (e.g., `http://user:pass@host:port`) |

### Proxy Configuration

The scraper supports proxies in three ways (in order of precedence):

1. **CLI argument**: `--proxy http://proxy.example.com:8080`
2. **Environment variable**: `HTTP_PROXY` or `HTTPS_PROXY`
3. **No proxy**: Direct connection

Example with environment variable:

**Windows (PowerShell)**:
```powershell
$env:HTTP_PROXY = "http://proxy.example.com:8080"
python scrape_etmoney_multicap.py
```

**macOS/Linux**:
```bash
export HTTP_PROXY="http://proxy.example.com:8080"
python scrape_etmoney_multicap.py
```

## Examples

### Scrape first 5 funds with custom output file

```bash
python scrape_etmoney_multicap.py --limit 5 --outfile test_funds.csv
```

### Scrape with slower rate limiting

```bash
python scrape_etmoney_multicap.py --sleep 2.0
```

### Scrape using proxy

```bash
python scrape_etmoney_multicap.py --proxy http://myproxy.com:8080
```

## Output

The scraper generates a CSV file with the following columns:

- `fund_name` - Name of the mutual fund
- `fund_url` - Full URL to the fund page
- `aum_cr` - Assets Under Management in Crores (₹)
- `expense_ratio` - Expense ratio (%)
- `alpha` - Alpha value
- `sharpe` - Sharpe ratio
- `beta` - Beta value
- `sd` - Standard deviation

Example output:

```csv
fund_name,fund_url,aum_cr,expense_ratio,alpha,sharpe,beta,sd
Axis Multicap Fund,https://www.etmoney.com/mutual-funds/axis-multicap-fund/42348,12500.5,1.75,2.3,1.8,0.95,15.2
...
```

## How It Works

1. **Fetch Category Page**: Retrieves the Multi-Cap funds listing page
2. **Extract Fund Links**: Parses all fund URLs matching the pattern `/mutual-funds/<slug>/<id>`
3. **Visit Each Fund**: 
   - First attempts to fetch with `requests`
   - If content appears JavaScript-rendered, falls back to Playwright
4. **Extract Data**:
   - Prioritizes structured data (`__NEXT_DATA__` JSON)
   - Falls back to HTML parsing with regex patterns
5. **Export to CSV**: Writes all collected data to the specified CSV file

## Troubleshooting

### Playwright Installation Issues

If Playwright fails to install browsers, run manually:

```bash
playwright install chromium
```

### Missing Data

If some fields are consistently missing, check the logs for warnings. The scraper will continue even if some fields can't be extracted.

### Rate Limiting / Blocking

If you encounter 429 (Too Many Requests) errors:

1. Increase the `--sleep` delay (e.g., `--sleep 2.0`)
2. Use a proxy with `--proxy`
3. Reduce concurrent scraping by using `--limit`

### Memory Issues

For very large scraping jobs, process in batches using `--limit`:

```bash
python scrape_etmoney_multicap.py --limit 50 --outfile batch1.csv
```

## Dependencies

- Python 3.8+
- requests - HTTP library
- beautifulsoup4 - HTML parsing
- playwright - Browser automation (JavaScript fallback)
- urllib3 - HTTP retry logic

See [requirements.txt](requirements.txt) for specific versions.

## License

This scraper is for educational purposes only. Please respect ET Money's terms of service and robots.txt when using this tool. Use reasonable rate limiting and consider the impact on their servers.

## Notes

- The scraper includes polite delays between requests (default 0.8s)
- Retry logic with exponential backoff is built-in for transient failures
- Logs warnings for missing data but continues scraping
- Supports both Windows and Unix-like systems
