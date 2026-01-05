# 📰 Multi-Region News Aggregator & Web Scraper

A professional-grade, scalable web scraping solution for aggregating news from major publications in **Kenya** and the **USA**. Built with Python, featuring robust error handling, rate limiting, data validation, and multiple export formats.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Maintained](https://img.shields.io/badge/Maintained-Yes-brightgreen.svg)

## 🌟 Features

- **Multi-Region Support**: Scrapes news from 10+ major news outlets across Kenya and USA
- **Smart Rate Limiting**: Respects website policies with configurable delays
- **Robust Error Handling**: Retry logic, timeout handling, and graceful degradation
- **Multiple Export Formats**: JSON, CSV, SQLite database, and Excel
- **Content Extraction**: Headlines, article summaries, authors, timestamps, and categories
- **Deduplication**: Intelligent duplicate detection to avoid repeated articles
- **Async Support**: High-performance asynchronous scraping for faster results
- **Logging & Monitoring**: Comprehensive logging for debugging and monitoring
- **Scheduled Scraping**: Built-in scheduler for automated news collection
- **API Ready**: RESTful API endpoint for integration with other applications

## 📊 Supported News Sources

### 🇰🇪 Kenya
| Source | URL | Categories |
|--------|-----|------------|
| Nation Africa | nation.africa | General, Business, Sports |
| The Standard | standardmedia.co.ke | General, Politics, Entertainment |
| Capital FM | capitalfm.co.ke | Business, Lifestyle |
| Citizen Digital | citizen.digital | General, News |
| Business Daily | businessdailyafrica.com | Business, Markets |
| The Star | the-star.co.ke | General, Politics |

### 🇺🇸 USA
| Source | URL | Categories |
|--------|-----|------------|
| CNN | cnn.com | General, Politics, World |
| Fox News | foxnews.com | General, Politics |
| NBC News | nbcnews.com | General, Business |
| CBS News | cbsnews.com | General, Entertainment |
| ABC News | abcnews.go.com | General, Politics |
| NPR | npr.org | General, Culture |

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/news-scraper.git
cd news-scraper

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from src.scraper import NewsScraper

# Initialize scraper
scraper = NewsScraper()

# Scrape all sources
articles = scraper.scrape_all()

# Scrape specific region
kenya_news = scraper.scrape_region('kenya')
usa_news = scraper.scrape_region('usa')

# Export to different formats
scraper.export_to_json('news_data.json')
scraper.export_to_csv('news_data.csv')
scraper.export_to_sqlite('news_data.db')
```

### Command Line Interface

```bash
# Scrape all sources
python main.py --all

# Scrape specific region
python main.py --region kenya
python main.py --region usa

# Scrape specific source
python main.py --source "Nation Africa"

# Export to specific format
python main.py --all --format json --output news.json

# Run with scheduler (every 6 hours)
python main.py --schedule 6
```

## 📁 Project Structure

```
news-scraper/
├── src/
│   ├── __init__.py
│   ├── scraper.py          # Main scraper class
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── base.py         # Base scraper class
│   │   ├── kenya.py        # Kenya news sources
│   │   └── usa.py          # USA news sources
│   ├── models/
│   │   ├── __init__.py
│   │   └── article.py      # Article data model
│   ├── exporters/
│   │   ├── __init__.py
│   │   ├── json_exporter.py
│   │   ├── csv_exporter.py
│   │   └── sqlite_exporter.py
│   └── utils/
│       ├── __init__.py
│       ├── rate_limiter.py
│       ├── validators.py
│       └── logger.py
├── tests/
│   ├── __init__.py
│   ├── test_scraper.py
│   └── test_exporters.py
├── config/
│   └── settings.py
├── data/                    # Scraped data output
├── logs/                    # Application logs
├── main.py                  # CLI entry point
├── api.py                   # REST API server
├── requirements.txt
├── README.md
└── LICENSE
```

## ⚙️ Configuration

Edit `config/settings.py` to customize:

```python
SETTINGS = {
    'rate_limit_delay': 2,      # Seconds between requests
    'timeout': 30,               # Request timeout
    'max_retries': 3,            # Retry attempts
    'user_agent': 'NewsBot/1.0',
    'output_dir': 'data/',
    'log_level': 'INFO'
}
```

## 🔌 API Endpoints

Start the API server:
```bash
python api.py
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scrape` | POST | Trigger scraping job |
| `/api/articles` | GET | Get all articles |
| `/api/articles/{region}` | GET | Get articles by region |
| `/api/sources` | GET | List available sources |
| `/api/status` | GET | Get scraper status |

## 📈 Performance

- Async scraping: ~50 articles/minute
- Memory efficient: Processes articles in batches
- SQLite indexing for fast queries

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Your Name**
- Portfolio: [yourwebsite.com](https://yourwebsite.com)
- LinkedIn: [linkedin.com/in/yourprofile](https://linkedin.com/in/yourprofile)
- Upwork: [upwork.com/freelancers/yourprofile](https://upwork.com/freelancers/yourprofile)

---

⭐ If you find this project useful, please consider giving it a star!
