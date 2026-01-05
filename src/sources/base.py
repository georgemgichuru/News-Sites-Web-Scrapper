"""
Base Scraper Class
Abstract base class for all news source scrapers.
"""
import time
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.article import Article
from src.utils.rate_limiter import RateLimiter, DomainThrottler
from src.utils.validators import clean_text, parse_date, normalize_url, is_valid_article_url
from src.utils.logger import get_logger
from config.settings import SETTINGS


class BaseScraper(ABC):
    """
    Abstract base class for news scrapers.
    Provides common functionality for all news source scrapers.
    """
    
    def __init__(self, source_config: Dict[str, Any]):
        """
        Initialize the base scraper.
        
        Args:
            source_config: Configuration dictionary for the news source
        """
        self.config = source_config
        self.name = source_config['name']
        self.base_url = source_config['url']
        self.selectors = source_config.get('selectors', {})
        self.categories = source_config.get('categories', [])
        self.rss_feed = source_config.get('rss_feed')
        self.enabled = source_config.get('enabled', True)
        
        # Initialize components
        self.logger = get_logger(f"scraper.{self.name}")
        self.throttler = DomainThrottler(SETTINGS.get('rate_limit_delay', 2))
        self.session = self._create_session()
        
        # User agent rotation
        try:
            self.ua = UserAgent()
        except Exception:
            self.ua = None
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with default headers."""
        session = requests.Session()
        session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        return session
    
    def _get_user_agent(self) -> str:
        """Get a random user agent."""
        if self.ua and SETTINGS.get('rotate_user_agent', True):
            try:
                return self.ua.random
            except Exception:
                pass
        return SETTINGS.get('default_user_agent', 'Mozilla/5.0')
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with retry logic.
        
        Args:
            url: URL to fetch
        
        Returns:
            HTML content or None
        """
        try:
            # Apply rate limiting
            self.throttler.throttle(url)
            
            # Update user agent
            self.session.headers['User-Agent'] = self._get_user_agent()
            
            # Make request
            response = self.session.get(
                url,
                timeout=SETTINGS.get('timeout', 30),
                allow_redirects=True
            )
            response.raise_for_status()
            
            return response.text
        
        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout fetching {url}")
            raise
        except requests.exceptions.HTTPError as e:
            self.logger.warning(f"HTTP error {e.response.status_code} for {url}")
            raise
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error for {url}: {str(e)}")
            raise
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content."""
        return BeautifulSoup(html, 'lxml')
    
    def _extract_text(self, element, selector: str) -> Optional[str]:
        """
        Extract text from an element using selector.
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector
        
        Returns:
            Extracted and cleaned text
        """
        if not element or not selector:
            return None
        
        found = element.select_one(selector)
        if found:
            return clean_text(found.get_text())
        return None
    
    def _extract_link(self, element, selector: str) -> Optional[str]:
        """
        Extract link from an element.
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector
        
        Returns:
            Normalized URL
        """
        if not element or not selector:
            return None
        
        found = element.select_one(selector)
        if found:
            href = found.get('href')
            return normalize_url(href, self.base_url)
        return None
    
    def _extract_image(self, element, selector: str) -> Optional[str]:
        """
        Extract image URL from an element.
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector
        
        Returns:
            Image URL
        """
        if not element or not selector:
            return None
        
        found = element.select_one(selector)
        if found:
            src = found.get('src') or found.get('data-src') or found.get('data-lazy-src')
            return normalize_url(src, self.base_url)
        return None
    
    def _extract_date(self, element, selector: str) -> Optional[datetime]:
        """
        Extract and parse date from an element.
        
        Args:
            element: BeautifulSoup element
            selector: CSS selector
        
        Returns:
            Parsed datetime
        """
        if not element or not selector:
            return None
        
        found = element.select_one(selector)
        if found:
            # Try datetime attribute first
            date_str = found.get('datetime') or found.get_text()
            return parse_date(date_str)
        return None
    
    @abstractmethod
    def scrape(self) -> List[Article]:
        """
        Scrape articles from the source.
        Must be implemented by subclasses.
        
        Returns:
            List of Article objects
        """
        pass
    
    def scrape_article_content(self, url: str) -> Optional[str]:
        """
        Scrape full content of a single article.
        
        Args:
            url: Article URL
        
        Returns:
            Article content
        """
        try:
            html = self._fetch_page(url)
            if not html:
                return None
            
            soup = self._parse_html(html)
            
            # Try common article content selectors
            content_selectors = [
                'article',
                '.article-content',
                '.article-body',
                '.story-content',
                '.post-content',
                '.entry-content',
                'main',
            ]
            
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    # Remove unwanted elements
                    for unwanted in content.select('script, style, nav, aside, .ads, .advertisement'):
                        unwanted.decompose()
                    
                    text = clean_text(content.get_text())
                    if len(text) > 100:
                        return text
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error scraping article content: {str(e)}")
            return None
    
    def _create_article(
        self,
        title: str,
        url: str,
        region: str,
        summary: str = None,
        author: str = None,
        published_date: datetime = None,
        image_url: str = None,
        categories: List[str] = None
    ) -> Optional[Article]:
        """
        Create an Article object with validation.
        
        Returns:
            Article object or None if invalid
        """
        if not title or not url:
            return None
        
        if not is_valid_article_url(url, self.base_url):
            return None
        
        try:
            return Article(
                title=title,
                url=url,
                summary=summary,
                author=author,
                published_date=published_date,
                source_name=self.name,
                source_url=self.base_url,
                region=region,
                categories=categories or self.categories,
                image_url=image_url
            )
        except Exception as e:
            self.logger.error(f"Error creating article: {str(e)}")
            return None
