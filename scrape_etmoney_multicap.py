#!/usr/bin/env python3
"""
ET Money Multi-Cap Mutual Funds Scraper

Scrapes fund data from ET Money's multi-cap category page and individual fund pages.
Supports proxy, retry/backoff, and Playwright fallback for JavaScript-rendered content.
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Playwright imports (will be used for fallback)
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logging.warning("Playwright not available. JS-rendered content fallback disabled.")


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ETMoneyScraper:
    """Scraper for ET Money mutual funds data."""
    
    BASE_URL = "https://www.etmoney.com"
    
    def __init__(self, category_url: str, sleep_time: float = 2, proxy: Optional[str] = None):
        """
        Initialize the scraper.
        
        Args:
            category_url: URL of the category page to scrape
            sleep_time: Delay between requests in seconds
            proxy: Proxy URL (e.g., 'http://user:pass@host:port')
        """
        self.category_url = category_url
        self.sleep_time = sleep_time
        self.proxy = proxy or os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')
        self.session = self._create_session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Configure proxy if provided
        if self.proxy:
            session.proxies = {
                'http': self.proxy,
                'https': self.proxy
            }
            logger.info(f"Using proxy: {self.proxy}")
        
        return session
    
    def fetch_with_requests(self, url: str) -> Tuple[Optional[str], int]:
        """
        Fetch a URL using requests.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (HTML content, status code)
        """
        try:
            response = self.session.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.text, response.status_code
        except requests.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None, 0
    
    def fetch_with_playwright(self, url: str) -> Optional[str]:
        """
        Fetch a URL using Playwright for JavaScript-rendered content.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available. Cannot fallback to browser rendering.")
            return None
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, proxy={
                    "server": self.proxy
                } if self.proxy else None)
                
                context = browser.new_context(
                    user_agent=self.headers['User-Agent']
                )
                
                page = context.new_page()
                page.goto(url, wait_until='networkidle', timeout=30000)
                
                # Wait for content to load
                time.sleep(2)
                
                content = page.content()
                browser.close()
                
                return content
        except PlaywrightTimeout:
            logger.error(f"Playwright timeout for {url}")
            return None
        except Exception as e:
            logger.error(f"Playwright error for {url}: {e}")
            return None
    
    def extract_fund_links(self, html: str) -> List[str]:
        """
        Extract all fund links from the category page.
        
        Args:
            html: HTML content of the category page
            
        Returns:
            List of fund URLs
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # Pattern to match fund URLs: /mutual-funds/<slug>/<id>
        fund_pattern = re.compile(r'^/mutual-funds/[^/]+/\d+$')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if fund_pattern.match(href):
                full_url = urljoin(self.BASE_URL, href)
                if full_url not in links:
                    links.append(full_url)
        
        logger.info(f"Found {len(links)} fund links on category page")
        return links
    
    def parse_next_data(self, html: str) -> Optional[Dict]:
        """
        Extract __NEXT_DATA__ JSON from the page if present.
        
        Args:
            html: HTML content
            
        Returns:
            Parsed JSON data or None
        """
        soup = BeautifulSoup(html, 'html.parser')
        script_tag = soup.find('script', id='__NEXT_DATA__', type='application/json')
        
        if script_tag and script_tag.string:
            try:
                data = json.loads(script_tag.string)
                return data
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse __NEXT_DATA__: {e}")
        
        return None
    
    def clean_numeric_value(self, value: str) -> Optional[float]:
        """
        Clean and convert a numeric string to float.
        
        Args:
            value: String value (e.g., "1,234.56", "12.5%", "₹1,234")
            
        Returns:
            Float value or None
        """
        if not value:
            return None
        
        # Remove currency symbols, commas, percentage signs, and whitespace
        cleaned = re.sub(r'[₹$€£,\s%]', '', value)
        
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def extract_fund_data(self, url: str, html: str) -> Dict[str, Optional[str]]:
        """
        Extract fund data from a fund page.
        
        Args:
            url: Fund page URL
            html: HTML content
            
        Returns:
            Dictionary with fund data
        """
        soup = BeautifulSoup(html, 'html.parser')
        data = {
            'fund_name': None,
            'fund_url': url,
            'fund_age_years': None,
            'aum_cr': None,
            'expense_ratio': None,
            'alpha': None,
            'sharpe': None,
            'beta': None,
            'sd': None,
            'large_cap_pct': None,
            'mid_cap_pct': None,
            'small_cap_pct': None,
            'other_cap_pct': None,
            'return_1m': None,
            'return_3m': None,
            'return_6m': None,
            'return_1y': None,
            'return_3y': None,
            'return_5y': None,
            'return_since_inception': None
        }
        
        # Try to extract from __NEXT_DATA__ first
        next_data = self.parse_next_data(html)
        if next_data:
            try:
                # Navigate through the structure to find fund data
                props = next_data.get('props', {})
                page_props = props.get('pageProps', {})
                
                # Extract fund name
                if 'fundName' in page_props:
                    data['fund_name'] = page_props['fundName']
                
                # Extract fund age
                inception_date = fund_details.get('inceptionDate') or fund_info.get('inceptionDate') or page_props.get('inceptionDate')
                fund_age = fund_details.get('fundAge') or fund_info.get('fundAge') or page_props.get('fundAge')
                
                if fund_age:
                    data['fund_age_years'] = self.clean_numeric_value(str(fund_age))
                elif inception_date:
                    # Try to parse inception date and calculate age
                    try:
                        from datetime import datetime
                        # Try different date formats
                        for date_format in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d']:
                            try:
                                inception = datetime.strptime(str(inception_date).split('T')[0], date_format)
                                age_years = (datetime.now() - inception).days / 365.25
                                data['fund_age_years'] = round(age_years, 2)
                                break
                            except ValueError:
                                continue
                    except Exception:
                        pass
                
                # Extract metrics from various possible locations
                fund_details = page_props.get('fundDetails', {})
                fund_info = page_props.get('fundInfo', {})
                
                # AUM
                aum = fund_details.get('aum') or fund_info.get('aum')
                if aum:
                    data['aum_cr'] = self.clean_numeric_value(str(aum))
                
                # Expense ratio
                expense = fund_details.get('expenseRatio') or fund_info.get('expenseRatio')
                if expense:
                    data['expense_ratio'] = self.clean_numeric_value(str(expense))
                
                # Risk metrics
                risk_metrics = fund_details.get('riskMetrics', {}) or fund_info.get('riskMetrics', {})
                if risk_metrics:
                    data['alpha'] = self.clean_numeric_value(str(risk_metrics.get('alpha', '')))
                    data['sharpe'] = self.clean_numeric_value(str(risk_metrics.get('sharpe', '')))
                    data['beta'] = self.clean_numeric_value(str(risk_metrics.get('beta', '')))
                    data['sd'] = self.clean_numeric_value(str(risk_metrics.get('standardDeviation', '')))
                
                # Market cap allocation
                allocation = fund_details.get('allocation', {}) or fund_info.get('allocation', {}) or page_props.get('allocation', {})
                if allocation:
                    data['large_cap_pct'] = self.clean_numeric_value(str(allocation.get('largeCap', '')))
                    data['mid_cap_pct'] = self.clean_numeric_value(str(allocation.get('midCap', '')))
                    data['small_cap_pct'] = self.clean_numeric_value(str(allocation.get('smallCap', '')))
                    data['other_cap_pct'] = self.clean_numeric_value(str(allocation.get('otherCap', '') or allocation.get('other', '')))
                
                # Returns
                returns = fund_details.get('returns', {}) or fund_info.get('returns', {}) or page_props.get('returns', {})
                if returns:
                    data['return_1m'] = self.clean_numeric_value(str(returns.get('1M', '') or returns.get('oneMonth', '')))
                    data['return_3m'] = self.clean_numeric_value(str(returns.get('3M', '') or returns.get('threeMonth', '')))
                    data['return_6m'] = self.clean_numeric_value(str(returns.get('6M', '') or returns.get('sixMonth', '')))
                    data['return_1y'] = self.clean_numeric_value(str(returns.get('1Y', '') or returns.get('oneYear', '')))
                    data['return_3y'] = self.clean_numeric_value(str(returns.get('3Y', '') or returns.get('threeYear', '')))
                    data['return_5y'] = self.clean_numeric_value(str(returns.get('5Y', '') or returns.get('fiveYear', '')))
                    data['return_since_inception'] = self.clean_numeric_value(str(returns.get('sinceInception', '') or returns.get('SI', '')))
                
            except Exception as e:
                logger.warning(f"Error parsing __NEXT_DATA__: {e}")
        
        # Fallback to HTML parsing if data not found
        if not data['fund_name']:
            # Try meta tag first
            meta_title = soup.find('meta', property='og:title')
            if meta_title and meta_title.get('content'):
                data['fund_name'] = meta_title['content'].strip()
            else:
                # Try h1 or title
                h1 = soup.find('h1')
                title = soup.find('title')
                if h1:
                    data['fund_name'] = h1.get_text(strip=True)
                elif title:
                    data['fund_name'] = title.get_text(strip=True)
        
        # Clean fund name - remove common suffixes
        if data['fund_name']:
            # Remove ": Latest NAV, Holdings, Performance" and similar patterns
            data['fund_name'] = re.sub(r':\s*Latest\s+NAV,?\s*Holdings,?\s*Performance.*$', '', data['fund_name'], flags=re.IGNORECASE).strip()
        
        # Extract metrics from HTML if not found in JSON
        # Look for key-value pairs in the page
        text_content = soup.get_text()
        
        # AUM patterns
        if not data['aum_cr']:
            aum_patterns = [
                r'AUM\s*(?:\(Fund size\))?\s*[:\-]?\s*₹?\s*([\d,\.]+)\s*Cr',
                r'Fund\s*Size\s*[:\-]?\s*₹?\s*([\d,\.]+)\s*Cr',
                r'Assets\s*Under\s*Management\s*[:\-]?\s*₹?\s*([\d,\.]+)\s*Cr'
            ]
            for pattern in aum_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    data['aum_cr'] = self.clean_numeric_value(match.group(1))
                    break
        
        # Expense ratio patterns
        if not data['expense_ratio']:
            expense_patterns = [
                r'Expense\s*Ratio\s*[:\-]?\s*([\d,\.]+)%?',
                r'Total\s*Expense\s*Ratio\s*[:\-]?\s*([\d,\.]+)%?'
            ]
            for pattern in expense_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    data['expense_ratio'] = self.clean_numeric_value(match.group(1))
                    break
        
        # Risk metrics patterns
        metrics_patterns = {
            'alpha': r'Alpha\s*[:\-]?\s*([\-\d,\.]+)',
            'sharpe': r'Sharpe\s*(?:Ratio)?\s*[:\-]?\s*([\-\d,\.]+)',
            'beta': r'Beta\s*[:\-]?\s*([\-\d,\.]+)',
            'sd': r'(?:Standard\s*Deviation|SD|Std\.?\s*Dev\.?)\s*[:\-]?\s*([\-\d,\.]+)'
        }
        
        for key, pattern in metrics_patterns.items():
            if not data[key]:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    data[key] = self.clean_numeric_value(match.group(1))
        
        # Market cap allocation patterns
        cap_patterns = {
            'large_cap_pct': r'Large\s*Cap\s*[:\-]?\s*([\d,\.]+)%?',
            'mid_cap_pct': r'Mid\s*Cap\s*[:\-]?\s*([\d,\.]+)%?',
            'small_cap_pct': r'Small\s*Cap\s*[:\-]?\s*([\d,\.]+)%?',
            'other_cap_pct': r'Other\s*Cap\s*[:\-]?\s*([\d,\.]+)%?'
        }
        
        for key, pattern in cap_patterns.items():
            if not data[key]:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    data[key] = self.clean_numeric_value(match.group(1))
        
        # Returns patterns
        return_patterns = {
            'return_1m': r'(?:1\s*Month|1M)\s*[:\-]?\s*([\-\d,\.]+)%?',
            'return_3m': r'(?:3\s*Months?|3M)\s*[:\-]?\s*([\-\d,\.]+)%?',
            'return_6m': r'(?:6\s*Months?|6M)\s*[:\-]?\s*([\-\d,\.]+)%?',
            'return_1y': r'(?:1\s*Year|1Y)\s*[:\-]?\s*([\-\d,\.]+)%?',
            'return_3y': r'(?:3\s*Years?|3Y)\s*[:\-]?\s*([\-\d,\.]+)%?',
            'return_5y': r'(?:5\s*Years?|5Y)\s*[:\-]?\s*([\-\d,\.]+)%?',
            'return_since_inception': r'(?:Since\s*Inception|SI)\s*[:\-]?\s*([\-\d,\.]+)%?'
        }
        
        for key, pattern in return_patterns.items():
            if not data[key]:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    data[key] = self.clean_numeric_value(match.group(1))
        
        # Fund age patterns
        if not data['fund_age_years']:
            # Look for patterns like "Age: 5 years" or "Fund Age: 10.5 years"
            age_patterns = [
                r'(?:Fund\s*)?Age\s*[:\-]?\s*([\d,\.]+)\s*(?:years?|yrs?)',
                r'Inception\s*Date\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
            ]
            
            for pattern in age_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    # Check if it's a date or a number
                    if '/' in value or '-' in value:
                        # It's a date, calculate age
                        try:
                            from datetime import datetime
                            for date_format in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                                try:
                                    inception = datetime.strptime(value, date_format)
                                    age_years = (datetime.now() - inception).days / 365.25
                                    data['fund_age_years'] = round(age_years, 2)
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            pass
                    else:
                        # It's already a number (years)
                        data['fund_age_years'] = self.clean_numeric_value(value)
                    
                    if data['fund_age_years']:
                        break
        
        return data
    
    def needs_playwright_fallback(self, html: str) -> bool:
        """
        Check if the page likely needs Playwright fallback.
        
        Args:
            html: HTML content
            
        Returns:
            True if fallback is needed
        """
        # Check for key indicators that content is JS-rendered
        indicators = ['AUM', 'Expense Ratio', 'Alpha', 'Sharpe', 'Beta', 'Standard Deviation']
        text = html.lower()
        
        # If very few indicators are present, likely JS-rendered
        found_count = sum(1 for indicator in indicators if indicator.lower() in text)
        
        return found_count < 2
    
    def scrape_fund_page(self, url: str) -> Dict[str, Optional[str]]:
        """
        Scrape a single fund page.
        
        Args:
            url: Fund page URL
            
        Returns:
            Dictionary with fund data
        """
        logger.info(f"Scraping fund: {url}")
        
        # Try with requests first
        html, status = self.fetch_with_requests(url)
        
        if html and status == 200:
            # Check if we need Playwright fallback
            if self.needs_playwright_fallback(html):
                logger.warning(f"Content appears JS-rendered, falling back to Playwright: {url}")
                playwright_html = self.fetch_with_playwright(url)
                if playwright_html:
                    html = playwright_html
        
        if not html:
            logger.error(f"Failed to fetch content for {url}")
            return {
                'fund_name': None,
                'fund_url': url,
                'fund_age_years': None,
                'aum_cr': None,
                'expense_ratio': None,
                'alpha': None,
                'sharpe': None,
                'beta': None,
                'sd': None,
                'large_cap_pct': None,
                'mid_cap_pct': None,
                'small_cap_pct': None,
                'other_cap_pct': None,
                'return_1m': None,
                'return_3m': None,
                'return_6m': None,
                'return_1y': None,
                'return_3y': None,
                'return_5y': None,
                'return_since_inception': None
            }
        
        # Extract data
        data = self.extract_fund_data(url, html)
        
        # Log warnings for missing data
        missing_fields = [k for k, v in data.items() if k != 'fund_url' and v is None]
        if missing_fields:
            logger.warning(f"Missing fields for {url}: {', '.join(missing_fields)}")
        
        # Sleep to be polite
        time.sleep(self.sleep_time)
        
        return data
    
    def scrape_all(self, limit: Optional[int] = None) -> List[Dict[str, Optional[str]]]:
        """
        Scrape all funds from the category page.
        
        Args:
            limit: Maximum number of funds to scrape (None for all)
            
        Returns:
            List of fund data dictionaries
        """
        logger.info(f"Fetching category page: {self.category_url}")
        
        # Fetch category page
        html, status = self.fetch_with_requests(self.category_url)
        
        if not html or status != 200:
            logger.error("Failed to fetch category page, trying Playwright...")
            html = self.fetch_with_playwright(self.category_url)
            
            if not html:
                logger.error("Failed to fetch category page with both methods")
                return []
        
        # Extract fund links
        fund_links = self.extract_fund_links(html)
        
        if not fund_links:
            logger.error("No fund links found on category page")
            return []
        
        # Apply limit
        if limit:
            fund_links = fund_links[:limit]
            logger.info(f"Limiting to {limit} funds")
        
        # Scrape each fund
        results = []
        for idx, url in enumerate(fund_links, 1):
            logger.info(f"Processing fund {idx}/{len(fund_links)}")
            data = self.scrape_fund_page(url)
            results.append(data)
        
        return results
    
    def save_to_csv(self, data: List[Dict], filename: str):
        """
        Save scraped data to CSV.
        
        Args:
            data: List of fund data dictionaries
            filename: Output CSV filename
        """
        if not data:
            logger.warning("No data to save")
            return
        
        fieldnames = ['fund_name', 'fund_url', 'fund_age_years', 'aum_cr', 'expense_ratio', 'alpha', 'sharpe', 'beta', 'sd', 
                      'large_cap_pct', 'mid_cap_pct', 'small_cap_pct', 'other_cap_pct',
                      'return_1m', 'return_3m', 'return_6m', 'return_1y', 'return_3y', 'return_5y', 'return_since_inception']
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"Successfully saved {len(data)} records to {filename}")
        except IOError as e:
            logger.error(f"Failed to write CSV file: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scrape ET Money mutual funds data',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--url',
        type=str,
        default='https://www.etmoney.com/mutual-funds/equity/flexi-cap/79',
        help='Category page URL to scrape (default: flexi-cap)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of funds to scrape'
    )
    
    parser.add_argument(
        '--outfile',
        type=str,
        default=None,
        help='Output CSV filename (default: auto-generated from URL slug, e.g., etmoney_flexicap.csv)'
    )
    
    parser.add_argument(
        '--sleep',
        type=float,
        default=0.8,
        help='Delay between requests in seconds'
    )
    
    parser.add_argument(
        '--proxy',
        type=str,
        default=None,
        help='Proxy URL (e.g., http://user:pass@host:port). Falls back to HTTP_PROXY/HTTPS_PROXY env vars'
    )
    
    args = parser.parse_args()
    
    # Generate default output filename from URL slug if not provided
    if args.outfile is None:
        # Extract category slug from URL (e.g., "flexi-cap" from ".../equity/flexi-cap/79")
        url_parts = args.url.rstrip('/').split('/')
        # Find the category slug (typically second-to-last part before the ID)
        if len(url_parts) >= 2:
            category_slug = url_parts[-2]
            args.outfile = f'etmoney_{category_slug.replace("-", "")}.csv'
        else:
            args.outfile = 'etmoney_funds.csv'
        logger.info(f"Auto-generated output filename: {args.outfile}")
    
    # Initialize scraper
    scraper = ETMoneyScraper(category_url=args.url, sleep_time=args.sleep, proxy=args.proxy)
    
    # Scrape all funds
    logger.info("Starting scrape...")
    results = scraper.scrape_all(limit=args.limit)
    
    if not results:
        logger.error("No data scraped")
        sys.exit(1)
    
    # Save to CSV
    scraper.save_to_csv(results, args.outfile)
    
    logger.info(f"Scraping complete! Results saved to {args.outfile}")


if __name__ == '__main__':
    main()
