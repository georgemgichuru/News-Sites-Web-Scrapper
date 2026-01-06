# 📰 News Scraper

A simple, single-file news scraper for Kenya and USA news sources. Fast, lightweight, and easy to use.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Lines](https://img.shields.io/badge/Lines-450-green.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ⚡ Features

- ✅ **Single-file design** - ~450 lines, no complex structure
- ✅ **13 news sources** - Kenya & USA outlets
- ✅ **RSS-first approach** - Fast & reliable
- ✅ **3 export formats** - JSON, CSV, SQLite
- ✅ **Smart rate limiting** - Respectful to servers
- ✅ **Auto retries** - Handles timeouts gracefully
- ✅ **User-agent rotation** - Avoids blocking
- ✅ **Detailed logging** - Full audit trail

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

Done! 🎉

## � Usage

### List All Sources
```bash
python news_scraper_standalone.py --list
```

### Scrape by Region
```bash
python news_scraper_standalone.py --region kenya --format json
python news_scraper_standalone.py --region usa --format csv
```

### Scrape Specific Source
```bash
python news_scraper_standalone.py --source "CNN" --format json
```

### Export All Formats
```bash
python news_scraper_standalone.py --all --format all
```

### Custom Output
```bash
python news_scraper_standalone.py --all --format json --output my_news.json
```

### Debug Modes
```bash
python news_scraper_standalone.py --all --verbose    # Debug info
python news_scraper_standalone.py --all --quiet      # Errors only
```

## ⚙️ Configuration

Edit `SETTINGS` in the script:

```python
SETTINGS = {
    'rate_limit_delay': 2,          # Delay between requests (seconds)
    'timeout': 30,                  # Request timeout
    'max_articles_per_source': 50,  # Articles per source
    'log_level': 'INFO',            # DEBUG, INFO, WARNING, ERROR
}
```

Edit `SOURCES` to add/remove outlets or change RSS feeds.

## 📊 Output

### JSON
```json
{
  "metadata": {
    "exported_at": "2026-01-06T14:30:32",
    "total_articles": 42
  },
  "articles": [
    {
      "title": "Breaking News",
      "url": "https://example.com/news",
      "summary": "Article summary...",
      "source_name": "CNN",
      "region": "usa"
    }
  ]
}
```

### CSV
```csv
title,url,summary,source_name,region
Breaking News,https://example.com/news,Article summary,CNN,usa
```

### SQLite
```bash
sqlite3 data/news.db
SELECT * FROM articles WHERE region = 'kenya';
```

## 📁 Files

- `news_scraper_standalone.py` - Main script
- `requirements.txt` - Dependencies
- `README_STANDALONE.md` - Detailed documentation
- `data/` - Output directory
- `logs/scraper.log` - Log file

## � Screenshots

### Scraper Output
![News Scraper](docs/images/image1.png)
*Example of scraper running and collecting articles from multiple sources*

### Data Export
![Data Export](docs/images/image.png)
*Sample exported data in JSON, CSV, and SQLite formats*

## �🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Missing modules | `pip install -r requirements.txt` |
| Connection timeout | Increase `timeout` in SETTINGS |
| Getting blocked | Increase `rate_limit_delay` |
| No RSS data | Check feed URL is active |
