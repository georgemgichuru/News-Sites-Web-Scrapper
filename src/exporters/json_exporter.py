"""
JSON Exporter
Export scraped articles to JSON format.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Union

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.article import Article, ArticleCollection
from config.settings import SETTINGS, DATA_DIR


class JSONExporter:
    """
    Export articles to JSON format.
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize JSON exporter.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir or DATA_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(
        self,
        articles: Union[List[Article], ArticleCollection],
        filename: str = None,
        pretty: bool = True
    ) -> str:
        """
        Export articles to JSON file.
        
        Args:
            articles: List of articles or ArticleCollection
            filename: Output filename (auto-generated if not provided)
            pretty: Whether to format JSON with indentation
        
        Returns:
            Path to the exported file
        """
        if isinstance(articles, ArticleCollection):
            data = self._collection_to_dict(articles)
        else:
            data = self._articles_to_dict(articles)
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"news_export_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            else:
                json.dump(data, f, ensure_ascii=False, default=str)
        
        return str(output_path)
    
    def _articles_to_dict(self, articles: List[Article]) -> dict:
        """Convert articles list to dictionary."""
        return {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'total_articles': len(articles),
                'format_version': '1.0'
            },
            'articles': [article.to_dict() for article in articles]
        }
    
    def _collection_to_dict(self, collection: ArticleCollection) -> dict:
        """Convert ArticleCollection to dictionary."""
        return {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'scraped_at': collection.scraped_at.isoformat(),
                'total_articles': collection.total_count,
                'sources_scraped': collection.sources_scraped,
                'regions': collection.regions,
                'format_version': '1.0'
            },
            'articles': collection.to_dict_list()
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
            filename = f"news_{region}_{timestamp}.json"
        
        return self.export(filtered, filename)
    
    def export_by_source(
        self,
        articles: List[Article],
        source_name: str,
        filename: str = None
    ) -> str:
        """
        Export articles filtered by source.
        
        Args:
            articles: List of articles
            source_name: Source name to filter by
            filename: Output filename
        
        Returns:
            Path to the exported file
        """
        filtered = [a for a in articles if a.source_name == source_name]
        
        if not filename:
            safe_name = source_name.lower().replace(' ', '_')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"news_{safe_name}_{timestamp}.json"
        
        return self.export(filtered, filename)


def export_to_json(
    articles: List[Article],
    filename: str = None,
    output_dir: str = None
) -> str:
    """
    Convenience function to export articles to JSON.
    
    Args:
        articles: List of articles
        filename: Output filename
        output_dir: Output directory
    
    Returns:
        Path to the exported file
    """
    exporter = JSONExporter(output_dir)
    return exporter.export(articles, filename)
