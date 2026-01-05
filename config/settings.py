"""
News Scraper Configuration Settings
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Output directories
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Scraper settings
SETTINGS = {
    # Request settings
    'rate_limit_delay': 2,          # Seconds between requests to same domain
    'timeout': 30,                   # Request timeout in seconds
    'max_retries': 3,                # Number of retry attempts
    'retry_delay': 5,                # Delay between retries
    
    # User agent rotation
    'rotate_user_agent': True,
    'default_user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    
    # Output settings
    'output_dir': str(DATA_DIR),
    'default_format': 'json',
    
    # Logging
    'log_level': 'INFO',
    'log_file': str(LOGS_DIR / 'scraper.log'),
    
    # Database
    'database_path': str(DATA_DIR / 'news.db'),
    
    # API settings
    'api_host': '0.0.0.0',
    'api_port': 5000,
    'api_debug': False,
    
    # Scheduler
    'schedule_interval_hours': 6,
    
    # Article limits
    'max_articles_per_source': 50,
    'max_article_age_days': 7,
}

# Kenya News Sources Configuration
KENYA_SOURCES = [
    {
        'name': 'Nation Africa',
        'url': 'https://nation.africa',
        'rss_feed': 'https://nation.africa/kenya/news/rss',
        'categories': ['general', 'politics', 'business', 'sports'],
        'selectors': {
            'article_list': 'article.story-card, div.article-item',
            'headline': 'h1, h2.headline, .story-title',
            'summary': '.story-summary, .article-summary, p.lead',
            'author': '.author-name, .byline, span.author',
            'date': 'time, .published-date, .date',
            'link': 'a[href*="/news/"], a[href*="/kenya/"]',
            'image': 'img.story-image, figure img',
        },
        'enabled': True
    },
    {
        'name': 'The Standard',
        'url': 'https://www.standardmedia.co.ke',
        'rss_feed': 'https://www.standardmedia.co.ke/rss/headlines.php',
        'categories': ['general', 'politics', 'entertainment', 'sports'],
        'selectors': {
            'article_list': 'article, .article-card, .news-item',
            'headline': 'h1, h2, .article-title',
            'summary': '.article-excerpt, .summary, p.intro',
            'author': '.author, .writer-name',
            'date': 'time, .date, .published',
            'link': 'a[href*="/article/"], a[href*="/news/"]',
            'image': 'img.article-image, .featured-image img',
        },
        'enabled': True
    },
    {
        'name': 'Capital FM',
        'url': 'https://www.capitalfm.co.ke',
        'categories': ['business', 'lifestyle', 'news'],
        'selectors': {
            'article_list': 'article, .post, .news-card',
            'headline': 'h1, h2, .entry-title',
            'summary': '.entry-excerpt, .post-summary',
            'author': '.author-name, .byline',
            'date': 'time, .post-date',
            'link': 'a[href*="/news/"], a[href*="/business/"]',
            'image': 'img.post-thumbnail, .featured-image img',
        },
        'enabled': True
    },
    {
        'name': 'Citizen Digital',
        'url': 'https://www.citizen.digital',
        'categories': ['general', 'news', 'entertainment'],
        'selectors': {
            'article_list': 'article, .story-item, .news-card',
            'headline': 'h1, h2, .story-title',
            'summary': '.story-excerpt, .lead-text',
            'author': '.author, .reporter',
            'date': 'time, .timestamp',
            'link': 'a[href*="/news/"]',
            'image': 'img.story-image',
        },
        'enabled': True
    },
    {
        'name': 'Business Daily',
        'url': 'https://www.businessdailyafrica.com',
        'rss_feed': 'https://www.businessdailyafrica.com/rss',
        'categories': ['business', 'markets', 'economy'],
        'selectors': {
            'article_list': 'article, .article-item',
            'headline': 'h1, h2, .article-title',
            'summary': '.article-summary, .teaser',
            'author': '.author-name',
            'date': 'time, .date',
            'link': 'a[href*="/bd/"]',
            'image': 'img.article-image',
        },
        'enabled': True
    },
    {
        'name': 'The Star Kenya',
        'url': 'https://www.the-star.co.ke',
        'categories': ['general', 'politics', 'sports'],
        'selectors': {
            'article_list': 'article, .article-card',
            'headline': 'h1, h2, .title',
            'summary': '.excerpt, .summary',
            'author': '.author',
            'date': 'time, .date',
            'link': 'a[href*="/news/"]',
            'image': 'img.thumbnail',
        },
        'enabled': True
    },
]

# USA News Sources Configuration
USA_SOURCES = [
    {
        'name': 'CNN',
        'url': 'https://www.cnn.com',
        'rss_feed': 'http://rss.cnn.com/rss/cnn_topstories.rss',
        'categories': ['general', 'politics', 'world', 'business'],
        'selectors': {
            'article_list': 'article, .card, .container__item',
            'headline': 'h1, h2, .container__headline',
            'summary': '.container__text, p.paragraph',
            'author': '.byline__name, .author',
            'date': 'time, .timestamp',
            'link': 'a[href*="/2025/"], a[href*="/2026/"]',
            'image': 'img.image__dam, picture img',
        },
        'enabled': True
    },
    {
        'name': 'Fox News',
        'url': 'https://www.foxnews.com',
        'rss_feed': 'https://moxie.foxnews.com/google-publisher/latest.xml',
        'categories': ['general', 'politics', 'opinion'],
        'selectors': {
            'article_list': 'article, .article, .content-item',
            'headline': 'h1, h2, .headline',
            'summary': '.dek, .article-summary',
            'author': '.author-byline, .author',
            'date': 'time, .article-date',
            'link': 'a[href*="/news/"], a[href*="/politics/"]',
            'image': 'img.article-image',
        },
        'enabled': True
    },
    {
        'name': 'NBC News',
        'url': 'https://www.nbcnews.com',
        'rss_feed': 'https://feeds.nbcnews.com/nbcnews/public/news',
        'categories': ['general', 'politics', 'business', 'health'],
        'selectors': {
            'article_list': 'article, .wide-tease-item, .tease-card',
            'headline': 'h1, h2, .wide-tease-item__headline',
            'summary': '.wide-tease-item__description',
            'author': '.byline, .author',
            'date': 'time, .relative-time',
            'link': 'a[href*="/news/"]',
            'image': 'img.wide-tease-item__image',
        },
        'enabled': True
    },
    {
        'name': 'CBS News',
        'url': 'https://www.cbsnews.com',
        'rss_feed': 'https://www.cbsnews.com/latest/rss/main',
        'categories': ['general', 'politics', 'entertainment'],
        'selectors': {
            'article_list': 'article, .item, .content-item',
            'headline': 'h1, h2, .item__hed',
            'summary': '.item__dek, .description',
            'author': '.byline, .author',
            'date': 'time, .timestamp',
            'link': 'a[href*="/news/"]',
            'image': 'img.thumbnail',
        },
        'enabled': True
    },
    {
        'name': 'ABC News',
        'url': 'https://abcnews.go.com',
        'rss_feed': 'https://abcnews.go.com/abcnews/topstories',
        'categories': ['general', 'politics', 'international'],
        'selectors': {
            'article_list': 'article, .ContentRoll__Item, .news-item',
            'headline': 'h1, h2, .ContentRoll__Headline',
            'summary': '.ContentRoll__Desc, .description',
            'author': '.Byline, .author',
            'date': 'time, .timestamp',
            'link': 'a[href*="/story"]',
            'image': 'img.ContentRoll__Image',
        },
        'enabled': True
    },
    {
        'name': 'NPR',
        'url': 'https://www.npr.org',
        'rss_feed': 'https://feeds.npr.org/1001/rss.xml',
        'categories': ['general', 'culture', 'politics', 'science'],
        'selectors': {
            'article_list': 'article, .story-text, .item',
            'headline': 'h1, h2, .title',
            'summary': '.teaser, .summary',
            'author': '.byline, .author',
            'date': 'time, .date',
            'link': 'a[href*="/2025/"], a[href*="/2026/"]',
            'image': 'img.respArchiveImg',
        },
        'enabled': True
    },
]

# All sources combined
ALL_SOURCES = {
    'kenya': KENYA_SOURCES,
    'usa': USA_SOURCES
}
