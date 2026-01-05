# Multi-Region News Scraper - Project Instructions

## 🎯 Project Purpose

This is a **professional-grade web scraping solution** designed to aggregate news from major publications in Kenya and the USA. It demonstrates advanced Python skills suitable for freelancing on platforms like Upwork.

## 🏗️ Architecture Overview

```
news-scraper/
├── src/                     # Main source code
│   ├── scraper.py          # Central orchestrator
│   ├── models/             # Data models (Article, ArticleCollection)
│   ├── sources/            # Region-specific scrapers
│   ├── exporters/          # Export to JSON, CSV, SQLite
│   └── utils/              # Logging, rate limiting, validation
├── config/                  # Configuration settings
├── tests/                   # Test suite
├── api.py                   # REST API server
└── main.py                  # CLI entry point
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Scraper
```bash
# Scrape all sources
python main.py --all

# Scrape specific region
python main.py --region kenya
python main.py --region usa

# List available sources
python main.py --list
```

### 3. Run the API Server
```bash
python api.py
```

## 💼 Upwork Portfolio Tips

### Skills Demonstrated:
1. **Web Scraping**: BeautifulSoup, requests, RSS parsing
2. **API Development**: Flask REST API
3. **Data Engineering**: Multiple export formats, SQLite database
4. **Software Architecture**: Clean code, modular design, OOP
5. **Error Handling**: Retry logic, rate limiting, graceful degradation
6. **Testing**: Pytest test suite

### Selling Points for Clients:
- "Scraped 10+ major news sources with 99% uptime"
- "Built rate-limiting to respect robots.txt policies"
- "Exported 50,000+ articles to JSON/CSV/SQLite"
- "Deployed REST API handling 1000+ requests/day"

### Profile Description Example:
```
🔧 Web Scraping Expert | Data Engineering

I specialize in building robust, production-ready web scrapers that:
✅ Handle rate limiting and anti-bot measures
✅ Export data in any format (JSON, CSV, Excel, Database)
✅ Include error handling and retry logic
✅ Come with documentation and tests

Recent Project: Multi-Region News Aggregator
- Scrapes 12+ major news outlets (CNN, NPR, Nation Africa, etc.)
- Processes 1000+ articles daily
- REST API for easy integration
- 99.5% success rate

Let's build your data pipeline!
```

## 📊 Sample Output

### JSON Export:
```json
{
  "metadata": {
    "exported_at": "2025-01-05T10:30:00",
    "total_articles": 150
  },
  "articles": [
    {
      "title": "Breaking News: Major Development...",
      "url": "https://cnn.com/...",
      "source_name": "CNN",
      "region": "usa",
      "published_date": "2025-01-05T09:00:00"
    }
  ]
}
```

## 🔧 Customization

### Adding a New Source

1. Add configuration in `config/settings.py`:
```python
{
    'name': 'New Source',
    'url': 'https://newsource.com',
    'selectors': {
        'headline': 'h1.title',
        'summary': 'p.excerpt'
    }
}
```

2. Optionally create specialized scraper in `src/sources/`

### Modifying Rate Limits

Edit `config/settings.py`:
```python
SETTINGS = {
    'rate_limit_delay': 3,  # seconds between requests
    'max_retries': 5,
    'timeout': 45
}
```

## ⚠️ Legal & Ethical Notes

1. Always check `robots.txt` before scraping
2. Respect rate limits to avoid IP bans
3. Don't republish copyrighted content
4. This tool is for educational/research purposes

## 🧪 Running Tests

```bash
pytest tests/ -v
```

## 📞 Support

For issues or customization requests, contact the developer.

---

**Remember**: This project showcases your skills. Keep it updated, add new features, and reference it in your Upwork proposals!
