"""
Main News Scraper Class
Central orchestrator for all scraping operations.
"""
from typing import List, Dict, Optional, Union
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.article import Article, ArticleCollection
from src.sources.kenya import create_kenya_scrapers, scrape_kenya_news
from src.sources.usa import create_usa_scrapers, scrape_usa_news
from src.exporters.json_exporter import JSONExporter
from src.exporters.csv_exporter import CSVExporter
from src.exporters.sqlite_exporter import SQLiteExporter
from src.utils.logger import setup_logger, ScraperLogger
from config.settings import SETTINGS, ALL_SOURCES


class NewsScraper:
    """
    Main news scraper class.
    Orchestrates scraping from multiple sources and regions.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the news scraper.
        
        Args:
            config: Optional configuration override
        """
        self.config = config or SETTINGS
        self.logger = ScraperLogger("news_scraper")
        
        # Initialize exporters
        self.json_exporter = JSONExporter()
        self.csv_exporter = CSVExporter()
        self.sqlite_exporter = SQLiteExporter()
        
        # Storage for scraped articles
        self.collection = ArticleCollection()
        
        # Statistics
        self.stats = {
            'total_articles': 0,
            'by_region': {},
            'by_source': {},
            'errors': [],
            'start_time': None,
            'end_time': None
        }
    
    def scrape_all(self, parallel: bool = False) -> List[Article]:
        """
        Scrape all configured news sources.
        
        Args:
            parallel: Whether to scrape sources in parallel
        
        Returns:
            List of scraped articles
        """
        self.logger.start_session()
        self.stats['start_time'] = datetime.now()
        
        all_articles = []
        
        try:
            # Scrape Kenya news
            self.logger.log_info("Scraping Kenya news sources...")
            kenya_articles = scrape_kenya_news()
            all_articles.extend(kenya_articles)
            self.stats['by_region']['kenya'] = len(kenya_articles)
            
            # Scrape USA news
            self.logger.log_info("Scraping USA news sources...")
            usa_articles = scrape_usa_news()
            all_articles.extend(usa_articles)
            self.stats['by_region']['usa'] = len(usa_articles)
            
            # Add to collection
            self.collection.add_articles(all_articles)
            self.collection.deduplicate()
            
            # Update stats
            self.stats['total_articles'] = self.collection.total_count
            
        except Exception as e:
            self.logger.log_error(f"Error during scraping: {str(e)}")
            self.stats['errors'].append(str(e))
        
        self.stats['end_time'] = datetime.now()
        self.logger.end_session()
        
        return self.collection.articles
    
    def scrape_region(self, region: str) -> List[Article]:
        """
        Scrape news from a specific region.
        
        Args:
            region: Region to scrape ('kenya' or 'usa')
        
        Returns:
            List of scraped articles
        """
        self.logger.log_info(f"Scraping {region} news sources...")
        
        if region.lower() == 'kenya':
            articles = scrape_kenya_news()
        elif region.lower() == 'usa':
            articles = scrape_usa_news()
        else:
            self.logger.log_error(f"Unknown region: {region}")
            return []
        
        self.collection.add_articles(articles)
        self.stats['by_region'][region] = len(articles)
        
        return articles
    
    def scrape_source(self, source_name: str) -> List[Article]:
        """
        Scrape news from a specific source.
        
        Args:
            source_name: Name of the source to scrape
        
        Returns:
            List of scraped articles
        """
        # Find source configuration
        source_config = None
        region = None
        
        for reg, sources in ALL_SOURCES.items():
            for source in sources:
                if source['name'].lower() == source_name.lower():
                    source_config = source
                    region = reg
                    break
        
        if not source_config:
            self.logger.log_error(f"Source not found: {source_name}")
            return []
        
        # Create appropriate scraper
        if region == 'kenya':
            from src.sources.kenya import KenyaScraper
            scraper = KenyaScraper(source_config)
        else:
            from src.sources.usa import USAScraper
            scraper = USAScraper(source_config)
        
        articles = scraper.scrape()
        self.collection.add_articles(articles)
        
        return articles
    
    def export_to_json(self, filename: str = None) -> str:
        """
        Export scraped articles to JSON.
        
        Args:
            filename: Output filename
        
        Returns:
            Path to exported file
        """
        return self.json_exporter.export(self.collection, filename)
    
    def export_to_csv(self, filename: str = None) -> str:
        """
        Export scraped articles to CSV.
        
        Args:
            filename: Output filename
        
        Returns:
            Path to exported file
        """
        return self.csv_exporter.export(self.collection, filename)
    
    def export_to_sqlite(self, db_path: str = None) -> int:
        """
        Export scraped articles to SQLite database.
        
        Args:
            db_path: Database path
        
        Returns:
            Number of articles exported
        """
        if db_path:
            exporter = SQLiteExporter(db_path)
            return exporter.export(self.collection)
        return self.sqlite_exporter.export(self.collection)
    
    def get_articles(self) -> List[Article]:
        """Get all scraped articles."""
        return self.collection.articles
    
    def get_articles_by_region(self, region: str) -> List[Article]:
        """Get articles filtered by region."""
        return self.collection.get_by_region(region)
    
    def get_articles_by_source(self, source_name: str) -> List[Article]:
        """Get articles filtered by source."""
        return self.collection.get_by_source(source_name)
    
    def get_stats(self) -> Dict:
        """Get scraping statistics."""
        return {
            **self.stats,
            'duration': str(self.stats['end_time'] - self.stats['start_time']) 
                if self.stats['start_time'] and self.stats['end_time'] else None
        }
    
    def clear(self):
        """Clear all scraped articles."""
        self.collection = ArticleCollection()
        self.stats = {
            'total_articles': 0,
            'by_region': {},
            'by_source': {},
            'errors': [],
            'start_time': None,
            'end_time': None
        }
    
    @staticmethod
    def list_sources() -> Dict[str, List[str]]:
        """
        List all available news sources.
        
        Returns:
            Dictionary of regions with their sources
        """
        return {
            region: [source['name'] for source in sources]
            for region, sources in ALL_SOURCES.items()
        }


# Convenience functions for quick usage
def scrape_all_news() -> List[Article]:
    """Quick function to scrape all news."""
    scraper = NewsScraper()
    return scraper.scrape_all()


def scrape_kenya() -> List[Article]:
    """Quick function to scrape Kenya news."""
    scraper = NewsScraper()
    return scraper.scrape_region('kenya')


def scrape_usa() -> List[Article]:
    """Quick function to scrape USA news."""
    scraper = NewsScraper()
    return scraper.scrape_region('usa')
