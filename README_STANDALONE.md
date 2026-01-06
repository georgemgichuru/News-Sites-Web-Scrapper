# 📰 Standalone News Scraper

A single-file, lightweight news scraper for Kenya and USA news sources. Simple, fast, and easy to use.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Lines](https://img.shields.io/badge/Lines-450-green.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ⚡ Features

- ✅ **Single 450-line script** - No complex package structure
- ✅ **13 news sources** - 6 Kenya + 7 USA outlets
- ✅ **RSS-first approach** - Fast & reliable data extraction
- ✅ **3 export formats** - JSON, CSV, SQLite
- ✅ **Smart rate limiting** - Respectful to servers
- ✅ **Automatic retries** - Handles timeouts gracefully
- ✅ **User-agent rotation** - Avoids being blocked
- ✅ **Detailed logging** - Track everything

## 📰 Supported Sources

**Kenya (6):** Nation Africa, The Standard, Capital FM, Citizen Digital, Business Daily, The Star Kenya

**USA (7):** CNN, Fox News, NBC News, CBS News, ABC News, NPR

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Your First Scrape
```bash
python news_scraper_standalone.py --all --format json
```

That's it! ✨

## 📖 Usage

### List All Sources
```bash
python news_scraper_standalone.py --list
```

### Scrape Everything
```bash
python news_scraper_standalone.py --all --format json
```

### Scrape by Region
```bash
python news_scraper_standalone.py --region kenya --format csv
python news_scraper_standalone.py --region usa --format sqlite
```

### Scrape Specific Source
```bash
python news_scraper_standalone.py --source "CNN" --format json
```

### Export All Formats at Once
```bash
python news_scraper_standalone.py --all --format all
```

### Custom Output Filename
```bash
python news_scraper_standalone.py --all --format json --output my_news.json
```

### Quiet/Verbose Modes
```bash
python news_scraper_standalone.py --all --quiet      # Errors only
python news_scraper_standalone.py --all --verbose    # Debug info
```

## � Output Examples

### JSON
```json
{
  "metadata": {
    "exported_at": "2026-01-06T14:30:32",
    "total_articles": 42,
    "format_version": "1.0"
  },
  "articles": [
    {
      "id": "a1b2c3d4e5f6g7h8",
      "title": "Breaking News",
      "url": "https://example.com/news/story",
      "summary": "Article summary...",
      "author": "Jane Doe",
      "published_date": "2026-01-06T10:15:00",
      "source_name": "CNN",
      "region": "usa",
      "categories": ["politics", "world"]
    }
  ]
}
```

### CSV
```csv
id,title,url,summary,author,published_date,source_name,region,categories
a1b2c3d4e5f6g7h8,Breaking News,https://example.com/news/story,Article summary,Jane Doe,2026-01-06T10:15:00,CNN,usa,politics|world
```

### SQLite
Query with: `sqlite3 data/news.db`
```sql
SELECT title, url FROM articles WHERE region = 'kenya';
SELECT source_name, COUNT(*) FROM articles GROUP BY source_name;
```

## ⚙️ Configuration

Edit `SETTINGS` in the script:

```python
SETTINGS = {
    'rate_limit_delay': 2,              # Delay between requests (seconds)
    'timeout': 30,                      # Request timeout
    'max_articles_per_source': 50,      # Articles per source
    'log_level': 'INFO',                # DEBUG, INFO, WARNING, ERROR
}
```

Edit `SOURCES` to add/remove news outlets or change RSS feeds.

## 📁 Output Directory Structure

```
News Sites Web Scrapper/
├── news_scraper_standalone.py    # The main script
├── data/
│   ├── news_export_*.json        # JSON exports
│   ├── news_export_*.csv         # CSV exports
│   └── news.db                   # SQLite database
├── logs/
│   └── scraper.log              # Detailed logs
└── README_STANDALONE.md          # This file
```

## 🔍 How It Works

1. **Initialization** - Loads news source configurations
2. **RSS Preference** - Tries RSS feeds first (faster & more reliable)
3. **HTML Fallback** - Falls back to HTML scraping if RSS unavailable
4. **Rate Limiting** - Applies delays between requests to be respectful
5. **Content Extraction** - Parses titles, summaries, authors, dates, images
6. **Deduplication** - Removes duplicate articles based on content hash
7. **Export** - Saves to your chosen format(s)
8. **Logging** - Records everything in `logs/scraper.log`

## � Troubleshooting

| Issue | Solution |
|-------|----------|
| Missing modules | `pip install -r requirements.txt` |
| Connection timeout | Increase `timeout` in SETTINGS |
| Getting blocked | Increase `rate_limit_delay` |
| No data from source | Check RSS feed is still active |

## 📁 Files

- `news_scraper_standalone.py` - Main script (450 lines)
- `requirements.txt` - Dependencies
- `data/` - Output directory
- `logs/scraper.log` - Log file
