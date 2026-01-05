"""
Article Data Model
Defines the structure for scraped news articles using Pydantic for validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl, validator
import hashlib


class Article(BaseModel):
    """
    Represents a news article with all its metadata.
    """
    id: Optional[str] = Field(None, description="Unique identifier for the article")
    title: str = Field(..., min_length=1, max_length=500, description="Article headline")
    url: str = Field(..., description="Full URL to the article")
    summary: Optional[str] = Field(None, max_length=2000, description="Article summary or excerpt")
    content: Optional[str] = Field(None, description="Full article content")
    author: Optional[str] = Field(None, max_length=200, description="Article author")
    published_date: Optional[datetime] = Field(None, description="Publication date")
    scraped_at: datetime = Field(default_factory=datetime.now, description="When the article was scraped")
    source_name: str = Field(..., description="Name of the news source")
    source_url: str = Field(..., description="Base URL of the news source")
    region: str = Field(..., description="Geographic region (kenya/usa)")
    categories: List[str] = Field(default_factory=list, description="Article categories")
    image_url: Optional[str] = Field(None, description="Featured image URL")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate a unique ID based on URL and title."""
        unique_string = f"{self.url}{self.title}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]
    
    @validator('title')
    def clean_title(cls, v):
        """Clean and normalize the title."""
        if v:
            return ' '.join(v.strip().split())
        return v
    
    @validator('summary')
    def clean_summary(cls, v):
        """Clean and normalize the summary."""
        if v:
            return ' '.join(v.strip().split())
        return v
    
    @validator('region')
    def validate_region(cls, v):
        """Ensure region is valid."""
        valid_regions = ['kenya', 'usa']
        if v.lower() not in valid_regions:
            raise ValueError(f"Region must be one of: {valid_regions}")
        return v.lower()
    
    def to_dict(self) -> dict:
        """Convert article to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'summary': self.summary,
            'content': self.content,
            'author': self.author,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'scraped_at': self.scraped_at.isoformat(),
            'source_name': self.source_name,
            'source_url': self.source_url,
            'region': self.region,
            'categories': self.categories,
            'image_url': self.image_url,
        }
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if isinstance(other, Article):
            return self.id == other.id
        return False


class ArticleCollection(BaseModel):
    """
    Collection of articles with metadata.
    """
    articles: List[Article] = Field(default_factory=list)
    total_count: int = Field(0, description="Total number of articles")
    scraped_at: datetime = Field(default_factory=datetime.now)
    sources_scraped: List[str] = Field(default_factory=list)
    regions: List[str] = Field(default_factory=list)
    
    def add_article(self, article: Article):
        """Add an article to the collection."""
        if article not in self.articles:
            self.articles.append(article)
            self.total_count = len(self.articles)
    
    def add_articles(self, articles: List[Article]):
        """Add multiple articles to the collection."""
        for article in articles:
            self.add_article(article)
    
    def get_by_region(self, region: str) -> List[Article]:
        """Get articles by region."""
        return [a for a in self.articles if a.region == region]
    
    def get_by_source(self, source_name: str) -> List[Article]:
        """Get articles by source name."""
        return [a for a in self.articles if a.source_name == source_name]
    
    def get_by_category(self, category: str) -> List[Article]:
        """Get articles by category."""
        return [a for a in self.articles if category in a.categories]
    
    def to_dict_list(self) -> List[dict]:
        """Convert all articles to list of dictionaries."""
        return [article.to_dict() for article in self.articles]
    
    def deduplicate(self):
        """Remove duplicate articles."""
        seen = set()
        unique_articles = []
        for article in self.articles:
            if article.id not in seen:
                seen.add(article.id)
                unique_articles.append(article)
        self.articles = unique_articles
        self.total_count = len(self.articles)
