"""
Kenya News Sources Scraper
Implements scrapers for major Kenyan news outlets.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import feedparser

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.sources.base import BaseScraper
from src.models.article import Article
from src.utils.validators import clean_text, parse_date, normalize_url
from src.utils.logger import get_logger
from config.settings import KENYA_SOURCES, SETTINGS


class KenyaScraper(BaseScraper):
    """
    Scraper for Kenyan news sources.
    """
    
    REGION = 'kenya'
    
    def __init__(self, source_config: Dict[str, Any]):
        super().__init__(source_config)
    
    def scrape(self) -> List[Article]:
        """
        Scrape articles from the Kenyan news source.
        
        Returns:
            List of Article objects
        """
        articles = []
        
        # Try RSS feed first (more reliable)
        if self.rss_feed:
            rss_articles = self._scrape_rss()
            if rss_articles:
                articles.extend(rss_articles)
        
        # Fall back to HTML scraping
        if not articles:
            html_articles = self._scrape_html()
            articles.extend(html_articles)
        
        self.logger.info(f"Scraped {len(articles)} articles from {self.name}")
        return articles[:SETTINGS.get('max_articles_per_source', 50)]
    
    def _scrape_rss(self) -> List[Article]:
        """Scrape articles from RSS feed."""
        articles = []
        
        try:
            self.logger.debug(f"Fetching RSS feed: {self.rss_feed}")
            feed = feedparser.parse(self.rss_feed)
            
            for entry in feed.entries:
                article = self._parse_rss_entry(entry)
                if article:
                    articles.append(article)
        
        except Exception as e:
            self.logger.error(f"Error scraping RSS feed: {str(e)}")
        
        return articles
    
    def _parse_rss_entry(self, entry) -> Optional[Article]:
        """Parse a single RSS entry into an Article."""
        try:
            title = clean_text(entry.get('title', ''))
            url = entry.get('link', '')
            summary = clean_text(entry.get('summary', '') or entry.get('description', ''))
            
            # Parse date
            published_date = None
            if 'published_parsed' in entry and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6])
            elif 'published' in entry:
                published_date = parse_date(entry.published)
            
            # Get author
            author = entry.get('author', '')
            
            # Get image
            image_url = None
            if 'media_content' in entry and entry.media_content:
                image_url = entry.media_content[0].get('url')
            elif 'enclosures' in entry and entry.enclosures:
                for enc in entry.enclosures:
                    if enc.get('type', '').startswith('image/'):
                        image_url = enc.get('url')
                        break
            
            # Get categories
            categories = []
            if 'tags' in entry:
                categories = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
            
            return self._create_article(
                title=title,
                url=url,
                region=self.REGION,
                summary=summary,
                author=author,
                published_date=published_date,
                image_url=image_url,
                categories=categories or self.categories
            )
        
        except Exception as e:
            self.logger.debug(f"Error parsing RSS entry: {str(e)}")
            return None
    
    def _scrape_html(self) -> List[Article]:
        """Scrape articles from HTML page."""
        articles = []
        
        try:
            html = self._fetch_page(self.base_url)
            if not html:
                return articles
            
            soup = self._parse_html(html)
            
            # Find article elements
            article_selector = self.selectors.get('article_list', 'article')
            article_elements = soup.select(article_selector)[:30]
            
            for element in article_elements:
                article = self._parse_article_element(element)
                if article:
                    articles.append(article)
        
        except Exception as e:
            self.logger.error(f"Error scraping HTML: {str(e)}")
        
        return articles
    
    def _parse_article_element(self, element) -> Optional[Article]:
        """Parse a single HTML article element."""
        try:
            # Extract data using selectors
            title = self._extract_text(element, self.selectors.get('headline', 'h2'))
            url = self._extract_link(element, self.selectors.get('link', 'a'))
            summary = self._extract_text(element, self.selectors.get('summary', 'p'))
            author = self._extract_text(element, self.selectors.get('author', '.author'))
            published_date = self._extract_date(element, self.selectors.get('date', 'time'))
            image_url = self._extract_image(element, self.selectors.get('image', 'img'))
            
            if not title or not url:
                return None
            
            return self._create_article(
                title=title,
                url=url,
                region=self.REGION,
                summary=summary,
                author=author,
                published_date=published_date,
                image_url=image_url
            )
        
        except Exception as e:
            self.logger.debug(f"Error parsing article element: {str(e)}")
            return None


class NationAfricaScraper(KenyaScraper):
    """Specialized scraper for Nation Africa."""
    
    def _scrape_html(self) -> List[Article]:
        articles = []
        
        try:
            # Scrape multiple sections
            sections = [
                f"{self.base_url}/kenya/news",
                f"{self.base_url}/kenya/business",
                f"{self.base_url}/kenya/sports",
            ]
            
            for section_url in sections:
                try:
                    html = self._fetch_page(section_url)
                    if html:
                        soup = self._parse_html(html)
                        article_elements = soup.select('article.story-card, .teaser-item')[:15]
                        
                        for element in article_elements:
                            article = self._parse_article_element(element)
                            if article:
                                articles.append(article)
                except Exception as e:
                    self.logger.debug(f"Error scraping section {section_url}: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"Error in Nation Africa scraper: {str(e)}")
        
        return articles


class StandardMediaScraper(KenyaScraper):
    """Specialized scraper for The Standard."""
    
    def _scrape_html(self) -> List[Article]:
        articles = []
        
        try:
            html = self._fetch_page(self.base_url)
            if html:
                soup = self._parse_html(html)
                
                # Find news articles
                article_elements = soup.select('.article-wrapper, .story-teaser, article')[:30]
                
                for element in article_elements:
                    article = self._parse_article_element(element)
                    if article:
                        articles.append(article)
        
        except Exception as e:
            self.logger.error(f"Error in Standard Media scraper: {str(e)}")
        
        return articles


def create_kenya_scrapers() -> List[KenyaScraper]:
    """
    Create scraper instances for all enabled Kenya sources.
    
    Returns:
        List of KenyaScraper instances
    """
    scrapers = []
    
    for source_config in KENYA_SOURCES:
        if not source_config.get('enabled', True):
            continue
        
        name = source_config['name'].lower()
        
        # Use specialized scrapers where available
        if 'nation' in name:
            scraper = NationAfricaScraper(source_config)
        elif 'standard' in name:
            scraper = StandardMediaScraper(source_config)
        else:
            scraper = KenyaScraper(source_config)
        
        scrapers.append(scraper)
    
    return scrapers


def scrape_kenya_news() -> List[Article]:
    """
    Scrape all Kenya news sources.
    
    Returns:
        List of all scraped articles
    """
    logger = get_logger("scraper.kenya")
    all_articles = []
    
    scrapers = create_kenya_scrapers()
    logger.info(f"Starting Kenya news scraping with {len(scrapers)} sources")
    
    for scraper in scrapers:
        try:
            logger.info(f"Scraping: {scraper.name}")
            articles = scraper.scrape()
            all_articles.extend(articles)
            logger.info(f"Got {len(articles)} articles from {scraper.name}")
        except Exception as e:
            logger.error(f"Error scraping {scraper.name}: {str(e)}")
    
    logger.info(f"Total Kenya articles: {len(all_articles)}")
    return all_articles
