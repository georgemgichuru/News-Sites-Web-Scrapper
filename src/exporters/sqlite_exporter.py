"""
SQLite Exporter
Export scraped articles to SQLite database.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Union, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.article import Article, ArticleCollection
from config.settings import DATA_DIR


class SQLiteExporter:
    """
    Export articles to SQLite database.
    Supports upsert operations and advanced querying.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize SQLite exporter.
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = DATA_DIR / 'news.db'
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                summary TEXT,
                content TEXT,
                author TEXT,
                published_date TEXT,
                scraped_at TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                region TEXT NOT NULL,
                categories TEXT,
                image_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indices for common queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_articles_region 
            ON articles(region)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_articles_source 
            ON articles(source_name)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_articles_published 
            ON articles(published_date)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_articles_scraped 
            ON articles(scraped_at)
        ''')
        
        # Create scrape_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scrape_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                articles_count INTEGER DEFAULT 0,
                sources_scraped TEXT,
                regions TEXT,
                status TEXT DEFAULT 'running',
                errors TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def export(
        self,
        articles: Union[List[Article], ArticleCollection],
        upsert: bool = True
    ) -> int:
        """
        Export articles to SQLite database.
        
        Args:
            articles: List of articles or ArticleCollection
            upsert: If True, update existing articles; if False, skip duplicates
        
        Returns:
            Number of articles inserted/updated
        """
        if isinstance(articles, ArticleCollection):
            articles = articles.articles
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        count = 0
        for article in articles:
            try:
                if upsert:
                    cursor.execute('''
                        INSERT INTO articles 
                        (id, title, url, summary, content, author, published_date, 
                         scraped_at, source_name, source_url, region, categories, 
                         image_url, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            title = excluded.title,
                            summary = excluded.summary,
                            content = excluded.content,
                            author = excluded.author,
                            published_date = excluded.published_date,
                            scraped_at = excluded.scraped_at,
                            categories = excluded.categories,
                            image_url = excluded.image_url,
                            updated_at = excluded.updated_at
                    ''', self._article_to_tuple(article))
                else:
                    cursor.execute('''
                        INSERT OR IGNORE INTO articles 
                        (id, title, url, summary, content, author, published_date, 
                         scraped_at, source_name, source_url, region, categories, 
                         image_url, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', self._article_to_tuple(article))
                
                count += cursor.rowcount
            except Exception as e:
                print(f"Error inserting article: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return count
    
    def _article_to_tuple(self, article: Article) -> tuple:
        """Convert article to database tuple."""
        return (
            article.id,
            article.title,
            article.url,
            article.summary,
            article.content,
            article.author,
            article.published_date.isoformat() if article.published_date else None,
            article.scraped_at.isoformat(),
            article.source_name,
            article.source_url,
            article.region,
            '|'.join(article.categories),
            article.image_url,
            datetime.now().isoformat()
        )
    
    def get_articles(
        self,
        region: str = None,
        source: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[dict]:
        """
        Retrieve articles from database.
        
        Args:
            region: Filter by region
            source: Filter by source name
            limit: Maximum number of results
            offset: Offset for pagination
        
        Returns:
            List of article dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM articles WHERE 1=1"
        params = []
        
        if region:
            query += " AND region = ?"
            params.append(region)
        
        if source:
            query += " AND source_name = ?"
            params.append(source)
        
        query += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_article_count(self, region: str = None, source: str = None) -> int:
        """Get total article count with optional filters."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "SELECT COUNT(*) FROM articles WHERE 1=1"
        params = []
        
        if region:
            query += " AND region = ?"
            params.append(region)
        
        if source:
            query += " AND source_name = ?"
            params.append(source)
        
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count
    
    def get_sources(self) -> List[dict]:
        """Get list of all sources with article counts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT source_name, region, COUNT(*) as article_count,
                   MAX(scraped_at) as last_scraped
            FROM articles
            GROUP BY source_name, region
            ORDER BY article_count DESC
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def log_scrape(
        self,
        started_at: datetime,
        completed_at: datetime = None,
        articles_count: int = 0,
        sources_scraped: List[str] = None,
        regions: List[str] = None,
        status: str = 'completed',
        errors: str = None
    ) -> int:
        """Log a scraping session."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scrape_logs 
            (started_at, completed_at, articles_count, sources_scraped, 
             regions, status, errors)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            started_at.isoformat(),
            completed_at.isoformat() if completed_at else None,
            articles_count,
            '|'.join(sources_scraped) if sources_scraped else None,
            '|'.join(regions) if regions else None,
            status,
            errors
        ))
        
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return log_id
    
    def delete_old_articles(self, days: int = 30) -> int:
        """Delete articles older than specified days."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            DELETE FROM articles 
            WHERE scraped_at < ?
        ''', (cutoff_date.isoformat(),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count


def export_to_sqlite(
    articles: List[Article],
    db_path: str = None
) -> int:
    """
    Convenience function to export articles to SQLite.
    
    Args:
        articles: List of articles
        db_path: Database path
    
    Returns:
        Number of articles inserted/updated
    """
    from datetime import timedelta
    exporter = SQLiteExporter(db_path)
    return exporter.export(articles)
