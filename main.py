#!/usr/bin/env python3
"""Standalone News Scraper - All-in-One Script"""

import argparse, sys, time, json, csv, sqlite3, logging, hashlib, requests, feedparser, re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential
from dateutil import parser as date_parser

# ============================================================================
# CONFIG
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

SETTINGS = {
    'rate_limit_delay': 2, 'timeout': 30, 'max_retries': 3,
    'rotate_user_agent': True, 'output_dir': str(DATA_DIR),
    'log_level': 'INFO', 'log_file': str(LOGS_DIR / 'scraper.log'),
    'database_path': str(DATA_DIR / 'news.db'),
    'max_articles_per_source': 50,
}

# News sources - simplified format
SOURCES = {
    'kenya': [
        {'name': 'Nation Africa', 'url': 'https://nation.africa', 'rss': 'https://nation.africa/kenya/news/rss', 'cats': ['general', 'politics']},
        {'name': 'The Standard', 'url': 'https://www.standardmedia.co.ke', 'rss': 'https://www.standardmedia.co.ke/rss/headlines.php', 'cats': ['general', 'politics']},
        {'name': 'Capital FM', 'url': 'https://www.capitalfm.co.ke', 'cats': ['business']},
        {'name': 'Citizen Digital', 'url': 'https://www.citizen.digital', 'cats': ['general', 'news']},
        {'name': 'Business Daily', 'url': 'https://www.businessdailyafrica.com', 'rss': 'https://www.businessdailyafrica.com/rss', 'cats': ['business']},
        {'name': 'The Star Kenya', 'url': 'https://www.the-star.co.ke', 'cats': ['general', 'politics']},
    ],
    'usa': [
        {'name': 'CNN', 'url': 'https://www.cnn.com', 'rss': 'http://rss.cnn.com/rss/cnn_topstories.rss', 'cats': ['general', 'politics']},
        {'name': 'Fox News', 'url': 'https://www.foxnews.com', 'rss': 'https://moxie.foxnews.com/google-publisher/latest.xml', 'cats': ['general', 'politics']},
        {'name': 'NBC News', 'url': 'https://www.nbcnews.com', 'rss': 'https://feeds.nbcnews.com/nbcnews/public/news', 'cats': ['general']},
        {'name': 'CBS News', 'url': 'https://www.cbsnews.com', 'rss': 'https://www.cbsnews.com/latest/rss/main', 'cats': ['general']},
        {'name': 'ABC News', 'url': 'https://abcnews.go.com', 'rss': 'https://abcnews.go.com/abcnews/topstories', 'cats': ['general']},
        {'name': 'NPR', 'url': 'https://www.npr.org', 'rss': 'https://feeds.npr.org/1001/rss.xml', 'cats': ['general']},
    ]
}

# ============================================================================
# LOGGING & UTILS
# ============================================================================

def setup_logger(name="news_scraper", log_file=None, level="INFO"):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    logger.handlers = []
    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(name)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

logger = setup_logger("news_scraper", SETTINGS['log_file'], SETTINGS['log_level'])

def clean_text(text, max_len=None):
    if not text: return ""
    text = ' '.join(text.split())
    for pat in [r'\s*\[\.\.\.?\]', r'\s*Read more\.?', r'\s*Continue reading\.?']:
        text = re.sub(pat, '', text, flags=re.IGNORECASE)
    for ent, repl in {'&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'", '&mdash;': '—'}.items():
        text = text.replace(ent, repl)
    text = text.strip()
    if max_len and len(text) > max_len: text = text[:max_len-3] + '...'
    return text

def normalize_url(url, base_url=None):
    if not url: return None
    url = url.strip()
    if base_url and not url.startswith(('http://', 'https://')): url = urljoin(base_url, url)
    if url.startswith('http://'): url = 'https://' + url[7:]
    return url

def parse_date(date_str):
    if not date_str: return None
    date_str = date_str.strip()
    for pat, handler in {'(\d+)\s*minutes?\s*ago': lambda m: datetime.now() - timedelta(minutes=int(m.group(1))), '(\d+)\s*hours?\s*ago': lambda m: datetime.now() - timedelta(hours=int(m.group(1))), '(\d+)\s*days?\s*ago': lambda m: datetime.now() - timedelta(days=int(m.group(1)))}.items():
        match = re.search(pat, date_str, re.IGNORECASE)
        if match: return handler(match)
    try: return date_parser.parse(date_str, fuzzy=True)
    except: return None

# ============================================================================
# ARTICLE MODEL
# ============================================================================

class Article:
    def __init__(self, title, url, source_name, source_url, region, summary=None, author=None, published_date=None, categories=None, image_url=None):
        self.id = hashlib.md5(f"{url}{title}".encode()).hexdigest()[:16]
        self.title = clean_text(title) if title else ""
        self.url = url
        self.summary = clean_text(summary) if summary else None
        self.author = author
        self.published_date = published_date
        self.scraped_at = datetime.now()
        self.source_name = source_name
        self.source_url = source_url
        self.region = (region or "").lower()
        self.categories = categories or []
        self.image_url = image_url
    
    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'url': self.url, 'summary': self.summary,
            'author': self.author, 'published_date': self.published_date.isoformat() if self.published_date else None,
            'scraped_at': self.scraped_at.isoformat(), 'source_name': self.source_name,
            'source_url': self.source_url, 'region': self.region, 'categories': self.categories, 'image_url': self.image_url,
        }
    
    def __eq__(self, other): return isinstance(other, Article) and self.id == other.id
    def __hash__(self): return hash(self.id)

# ============================================================================
# SCRAPER
# ============================================================================

class NewsScraper:
    def __init__(self, source_config, region):
        self.config = source_config
        self.name = source_config['name']
        self.base_url = source_config['url']
        self.rss_feed = source_config.get('rss')
        self.categories = source_config.get('cats', [])
        self.region = region
        self.logger = logging.getLogger(f"scraper.{self.name}")
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        try: self.ua = UserAgent()
        except: self.ua = None
        self._last_req = {}
    
    def _rate_limit(self, url):
        domain = urlparse(url).netloc
        now = time.time()
        if domain in self._last_req and now - self._last_req[domain] < SETTINGS['rate_limit_delay']:
            time.sleep(SETTINGS['rate_limit_delay'] - (now - self._last_req[domain]))
        self._last_req[domain] = time.time()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch(self, url):
        self._rate_limit(url)
        if self.ua:
            try: self.session.headers['User-Agent'] = self.ua.random
            except: pass
        return self.session.get(url, timeout=SETTINGS['timeout'], allow_redirects=True).text
    
    def _parse_rss(self):
        articles = []
        try:
            feed = feedparser.parse(self.rss_feed)
            for entry in feed.entries:
                try:
                    title = clean_text(entry.get('title', ''))
                    url = entry.get('link', '')
                    summary = clean_text(entry.get('summary', '') or entry.get('description', ''))
                    author = entry.get('author', '')
                    published_date = None
                    if 'published_parsed' in entry and entry.published_parsed:
                        published_date = datetime(*entry.published_parsed[:6])
                    image_url = None
                    if 'media_content' in entry and entry.media_content:
                        image_url = entry.media_content[0].get('url')
                    elif 'media_thumbnail' in entry and entry.media_thumbnail:
                        image_url = entry.media_thumbnail[0].get('url')
                    if title and url:
                        articles.append(Article(title, url, self.name, self.base_url, self.region, summary, author, published_date, self.categories, image_url))
                except: pass
        except Exception as e:
            self.logger.error(f"RSS error: {str(e)}")
        return articles
    
    def scrape(self):
        articles = []
        if self.rss_feed:
            articles = self._parse_rss()
        self.logger.info(f"Scraped {len(articles)} articles from {self.name}")
        return articles[:SETTINGS['max_articles_per_source']]

# ============================================================================
# EXPORTERS
# ============================================================================

class Exporter:
    def __init__(self, output_dir=None):
        self.output_dir = Path(output_dir or DATA_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_filename(self, filename=None, ext=''):
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"news_export_{timestamp}{ext}"
        return self.output_dir / filename

class JSONExporter(Exporter):
    def export(self, articles, filename=None):
        path = self._get_filename(filename, '.json')
        data = {
            'metadata': {'exported_at': datetime.now().isoformat(), 'total_articles': len(articles), 'format_version': '1.0'},
            'articles': [a.to_dict() for a in articles]
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return str(path)

class CSVExporter(Exporter):
    HEADERS = ['id', 'title', 'url', 'summary', 'author', 'published_date', 'scraped_at', 'source_name', 'source_url', 'region', 'categories', 'image_url']
    
    def export(self, articles, filename=None):
        path = self._get_filename(filename, '.csv')
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.HEADERS)
            writer.writeheader()
            for a in articles:
                writer.writerow({
                    'id': a.id, 'title': a.title, 'url': a.url, 'summary': a.summary or '',
                    'author': a.author or '', 'published_date': a.published_date.isoformat() if a.published_date else '',
                    'scraped_at': a.scraped_at.isoformat(), 'source_name': a.source_name,
                    'source_url': a.source_url, 'region': a.region,
                    'categories': '|'.join(a.categories), 'image_url': a.image_url or ''
                })
        return str(path)

class SQLiteExporter(Exporter):
    def __init__(self, db_path=None):
        super().__init__()
        self.db_path = Path(db_path or SETTINGS['database_path'])
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.execute('''CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL UNIQUE,
            summary TEXT, author TEXT, published_date TEXT, scraped_at TEXT NOT NULL,
            source_name TEXT NOT NULL, source_url TEXT NOT NULL, region TEXT NOT NULL,
            categories TEXT, image_url TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_region ON articles(region)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_source ON articles(source_name)')
        conn.commit()
        conn.close()
    
    def export(self, articles):
        conn = sqlite3.connect(str(self.db_path))
        count = 0
        for a in articles:
            try:
                conn.execute('''INSERT OR REPLACE INTO articles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (a.id, a.title, a.url, a.summary, a.author, 
                     a.published_date.isoformat() if a.published_date else None,
                     a.scraped_at.isoformat(), a.source_name, a.source_url, a.region,
                     '|'.join(a.categories), a.image_url, datetime.now().isoformat()))
                count += 1
            except sqlite3.IntegrityError: pass
        conn.commit()
        conn.close()
        return count

# ============================================================================
# ORCHESTRATOR
# ============================================================================

class ArticleScraper:
    def __init__(self):
        self.articles = []
        self.stats = {'total': 0, 'by_region': {}, 'by_source': {}, 'errors': [], 'start': None, 'end': None}
    
    def scrape_all(self):
        logger.info("Starting scrape of all sources...")
        self.stats['start'] = datetime.now()
        for region, sources in SOURCES.items():
            for src in sources:
                try:
                    scraper = NewsScraper(src, region)
                    articles = scraper.scrape()
                    self.articles.extend(articles)
                    self.stats['by_source'][src['name']] = len(articles)
                except Exception as e:
                    logger.error(f"Error scraping {src['name']}: {str(e)}")
                    self.stats['errors'].append(str(e))
        self.articles = list(set(self.articles))
        self.stats['total'] = len(self.articles)
        self.stats['by_region'] = {'kenya': len([a for a in self.articles if a.region == 'kenya']), 'usa': len([a for a in self.articles if a.region == 'usa'])}
        self.stats['end'] = datetime.now()
        logger.info(f"Scraped {len(self.articles)} articles")
        return self.articles
    
    def scrape_region(self, region):
        self.articles = []
        for src in SOURCES.get(region.lower(), []):
            try:
                scraper = NewsScraper(src, region)
                self.articles.extend(scraper.scrape())
            except Exception as e:
                logger.error(f"Error: {str(e)}")
        self.articles = list(set(self.articles))
        return self.articles
    
    def scrape_source(self, source_name):
        for region, sources in SOURCES.items():
            for src in sources:
                if src['name'].lower() == source_name.lower():
                    scraper = NewsScraper(src, region)
                    self.articles = scraper.scrape()
                    return self.articles
        logger.error(f"Source not found: {source_name}")
        return []
    
    def export_json(self, filename=None): return JSONExporter().export(self.articles, filename)
    def export_csv(self, filename=None): return CSVExporter().export(self.articles, filename)
    def export_sqlite(self): return SQLiteExporter().export(self.articles)
    
    @staticmethod
    def list_sources():
        return {region: [s['name'] for s in sources] for region, sources in SOURCES.items()}

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='News Scraper - Multi-region news from Kenya & USA', formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--all', '-a', action='store_true', help='Scrape all sources')
    group.add_argument('--region', '-r', choices=['kenya', 'usa'], help='Scrape specific region')
    group.add_argument('--source', '-s', type=str, help='Scrape specific source')
    group.add_argument('--list', '-l', action='store_true', help='List all sources')
    parser.add_argument('--format', '-f', choices=['json', 'csv', 'sqlite', 'all'], default='json', help='Output format')
    parser.add_argument('--output', '-o', type=str, help='Output filename')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress output')
    args = parser.parse_args()
    
    if args.quiet: logger.setLevel(logging.ERROR)
    elif args.verbose: logger.setLevel(logging.DEBUG)
    
    scraper = ArticleScraper()
    
    if args.list:
        sources = scraper.list_sources()
        print("\n=== Available Sources ===\n")
        for region, src_list in sources.items():
            print(f"{region.upper()}: {', '.join(src_list)}\n")
    elif args.all:
        scraper.scrape_all()
        if args.format in ['json', 'all']: print(f"JSON: {scraper.export_json(args.output)}")
        if args.format in ['csv', 'all']: print(f"CSV: {scraper.export_csv(args.output)}")
        if args.format in ['sqlite', 'all']: print(f"SQLite: {scraper.export_sqlite()} articles to {SETTINGS['database_path']}")
    elif args.region:
        scraper.scrape_region(args.region)
        print(f"Scraped {len(scraper.articles)} articles from {args.region}")
        if args.format in ['json', 'all']: print(f"JSON: {scraper.export_json(args.output)}")
        if args.format in ['csv', 'all']: print(f"CSV: {scraper.export_csv(args.output)}")
        if args.format in ['sqlite', 'all']: print(f"SQLite: {scraper.export_sqlite()} articles")
    elif args.source:
        scraper.scrape_source(args.source)
        print(f"Scraped {len(scraper.articles)} articles from {args.source}")
        if args.format in ['json', 'all']: print(f"JSON: {scraper.export_json(args.output)}")
        if args.format in ['csv', 'all']: print(f"CSV: {scraper.export_csv(args.output)}")
        if args.format in ['sqlite', 'all']: print(f"SQLite: {scraper.export_sqlite()} articles")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
