"""
Test Suite for News Scraper
"""
import pytest
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.article import Article, ArticleCollection
from src.utils.validators import validate_url, clean_text, parse_date, normalize_url
from src.exporters.json_exporter import JSONExporter
from src.exporters.csv_exporter import CSVExporter


class TestArticleModel:
    """Tests for Article model."""
    
    def test_article_creation(self):
        """Test basic article creation."""
        article = Article(
            title="Test Article",
            url="https://example.com/article/1",
            source_name="Test Source",
            source_url="https://example.com",
            region="kenya"
        )
        
        assert article.title == "Test Article"
        assert article.url == "https://example.com/article/1"
        assert article.region == "kenya"
        assert article.id is not None
    
    def test_article_id_generation(self):
        """Test that article IDs are generated consistently."""
        article1 = Article(
            title="Test Article",
            url="https://example.com/article/1",
            source_name="Test Source",
            source_url="https://example.com",
            region="kenya"
        )
        
        article2 = Article(
            title="Test Article",
            url="https://example.com/article/1",
            source_name="Test Source",
            source_url="https://example.com",
            region="kenya"
        )
        
        # Same URL and title should generate same ID
        assert article1.id == article2.id
    
    def test_article_to_dict(self):
        """Test article serialization to dictionary."""
        article = Article(
            title="Test Article",
            url="https://example.com/article/1",
            summary="Test summary",
            source_name="Test Source",
            source_url="https://example.com",
            region="usa",
            categories=["politics", "news"]
        )
        
        data = article.to_dict()
        
        assert data['title'] == "Test Article"
        assert data['url'] == "https://example.com/article/1"
        assert data['summary'] == "Test summary"
        assert data['region'] == "usa"
        assert "politics" in data['categories']
    
    def test_article_title_cleaning(self):
        """Test that titles are cleaned properly."""
        article = Article(
            title="  Test   Article  With   Spaces  ",
            url="https://example.com/article/1",
            source_name="Test Source",
            source_url="https://example.com",
            region="kenya"
        )
        
        assert article.title == "Test Article With Spaces"
    
    def test_invalid_region(self):
        """Test that invalid regions raise an error."""
        with pytest.raises(ValueError):
            Article(
                title="Test",
                url="https://example.com",
                source_name="Test",
                source_url="https://example.com",
                region="invalid"
            )


class TestArticleCollection:
    """Tests for ArticleCollection."""
    
    def test_add_article(self):
        """Test adding articles to collection."""
        collection = ArticleCollection()
        
        article = Article(
            title="Test Article",
            url="https://example.com/article/1",
            source_name="Test Source",
            source_url="https://example.com",
            region="kenya"
        )
        
        collection.add_article(article)
        
        assert collection.total_count == 1
        assert len(collection.articles) == 1
    
    def test_deduplication(self):
        """Test that duplicates are removed."""
        collection = ArticleCollection()
        
        article1 = Article(
            title="Test Article",
            url="https://example.com/article/1",
            source_name="Test Source",
            source_url="https://example.com",
            region="kenya"
        )
        
        article2 = Article(
            title="Test Article",
            url="https://example.com/article/1",
            source_name="Test Source",
            source_url="https://example.com",
            region="kenya"
        )
        
        collection.add_article(article1)
        collection.add_article(article2)
        collection.deduplicate()
        
        assert collection.total_count == 1
    
    def test_get_by_region(self):
        """Test filtering by region."""
        collection = ArticleCollection()
        
        kenya_article = Article(
            title="Kenya News",
            url="https://example.com/kenya/1",
            source_name="Nation",
            source_url="https://nation.africa",
            region="kenya"
        )
        
        usa_article = Article(
            title="USA News",
            url="https://example.com/usa/1",
            source_name="CNN",
            source_url="https://cnn.com",
            region="usa"
        )
        
        collection.add_article(kenya_article)
        collection.add_article(usa_article)
        
        kenya_articles = collection.get_by_region("kenya")
        usa_articles = collection.get_by_region("usa")
        
        assert len(kenya_articles) == 1
        assert len(usa_articles) == 1
        assert kenya_articles[0].title == "Kenya News"


class TestValidators:
    """Tests for validator utilities."""
    
    def test_validate_url_valid(self):
        """Test valid URLs."""
        assert validate_url("https://example.com") == True
        assert validate_url("http://example.com/path") == True
        assert validate_url("https://sub.example.com/path?query=1") == True
    
    def test_validate_url_invalid(self):
        """Test invalid URLs."""
        assert validate_url("not a url") == False
        assert validate_url("") == False
        assert validate_url("example.com") == False
    
    def test_clean_text(self):
        """Test text cleaning."""
        assert clean_text("  Multiple   spaces  ") == "Multiple spaces"
        assert clean_text("Text with\n\nnewlines") == "Text with newlines"
        assert clean_text("Read more... Click here") == "..."
    
    def test_clean_text_max_length(self):
        """Test text truncation."""
        long_text = "A" * 100
        cleaned = clean_text(long_text, max_length=50)
        assert len(cleaned) == 50
        assert cleaned.endswith("...")
    
    def test_normalize_url(self):
        """Test URL normalization."""
        assert normalize_url("/path", "https://example.com") == "https://example.com/path"
        assert normalize_url("http://example.com") == "https://example.com"
    
    def test_parse_date_iso(self):
        """Test ISO date parsing."""
        date = parse_date("2025-01-05T10:30:00")
        assert date is not None
        assert date.year == 2025
        assert date.month == 1
        assert date.day == 5
    
    def test_parse_date_relative(self):
        """Test relative date parsing."""
        date = parse_date("2 hours ago")
        assert date is not None
        
        date = parse_date("yesterday")
        assert date is not None


class TestExporters:
    """Tests for exporters."""
    
    def test_json_exporter(self, tmp_path):
        """Test JSON export."""
        articles = [
            Article(
                title="Test Article",
                url="https://example.com/article/1",
                source_name="Test Source",
                source_url="https://example.com",
                region="kenya"
            )
        ]
        
        exporter = JSONExporter(str(tmp_path))
        output_path = exporter.export(articles, "test.json")
        
        assert Path(output_path).exists()
        
        import json
        with open(output_path) as f:
            data = json.load(f)
        
        assert 'articles' in data
        assert len(data['articles']) == 1
    
    def test_csv_exporter(self, tmp_path):
        """Test CSV export."""
        articles = [
            Article(
                title="Test Article",
                url="https://example.com/article/1",
                source_name="Test Source",
                source_url="https://example.com",
                region="kenya"
            )
        ]
        
        exporter = CSVExporter(str(tmp_path))
        output_path = exporter.export(articles, "test.csv")
        
        assert Path(output_path).exists()
        
        import csv
        with open(output_path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['title'] == "Test Article"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
