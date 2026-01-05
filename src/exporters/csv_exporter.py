"""
CSV Exporter
Export scraped articles to CSV format.
"""
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Union

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.article import Article, ArticleCollection
from config.settings import DATA_DIR


class CSVExporter:
    """
    Export articles to CSV format.
    """
    
    # CSV column headers
    HEADERS = [
        'id',
        'title',
        'url',
        'summary',
        'author',
        'published_date',
        'scraped_at',
        'source_name',
        'source_url',
        'region',
        'categories',
        'image_url'
    ]
    
    def __init__(self, output_dir: str = None):
        """
        Initialize CSV exporter.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir or DATA_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self,
        articles: Union[List[Article], ArticleCollection],
        filename: str = None
    ) -> str:
        """
        Export articles to CSV file.
        
        Args:
            articles: List of articles or ArticleCollection
            filename: Output filename (auto-generated if not provided)
        
        Returns:
            Path to the exported file
        """
        if isinstance(articles, ArticleCollection):
            articles = articles.articles
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"news_export_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.HEADERS)
            writer.writeheader()
            
            for article in articles:
                row = self._article_to_row(article)
                writer.writerow(row)
        
        return str(output_path)
    
    def _article_to_row(self, article: Article) -> dict:
        """Convert an article to a CSV row dictionary."""
        return {
            'id': article.id,
            'title': article.title,
            'url': article.url,
            'summary': article.summary or '',
            'author': article.author or '',
            'published_date': article.published_date.isoformat() if article.published_date else '',
            'scraped_at': article.scraped_at.isoformat(),
            'source_name': article.source_name,
            'source_url': article.source_url,
            'region': article.region,
            'categories': '|'.join(article.categories),
            'image_url': article.image_url or ''
        }
    
    def export_by_region(
        self,
        articles: List[Article],
        region: str,
        filename: str = None
    ) -> str:
        """
        Export articles filtered by region.
        
        Args:
            articles: List of articles
            region: Region to filter by
            filename: Output filename
        
        Returns:
            Path to the exported file
        """
        filtered = [a for a in articles if a.region == region]
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"news_{region}_{timestamp}.csv"
        
        return self.export(filtered, filename)
    
    def append(self, articles: List[Article], filename: str) -> str:
        """
        Append articles to an existing CSV file.
        
        Args:
            articles: List of articles to append
            filename: Existing CSV filename
        
        Returns:
            Path to the file
        """
        output_path = self.output_dir / filename
        
        # Check if file exists and has headers
        file_exists = output_path.exists()
        
        with open(output_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.HEADERS)
            
            if not file_exists:
                writer.writeheader()
            
            for article in articles:
                row = self._article_to_row(article)
                writer.writerow(row)
        
        return str(output_path)


def export_to_csv(
    articles: List[Article],
    filename: str = None,
    output_dir: str = None
) -> str:
    """
    Convenience function to export articles to CSV.
    
    Args:
        articles: List of articles
        filename: Output filename
        output_dir: Output directory
    
    Returns:
        Path to the exported file
    """
    exporter = CSVExporter(output_dir)
    return exporter.export(articles, filename)
