#!/usr/bin/env python3
"""
News Scraper REST API
Provides API endpoints for accessing scraped news data.
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scraper import NewsScraper
from src.exporters.sqlite_exporter import SQLiteExporter
from config.settings import SETTINGS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize components
scraper = NewsScraper()
db = SQLiteExporter()


# ============================================================================
# API Routes
# ============================================================================

@app.route('/')
def home():
    """API home page."""
    return jsonify({
        'name': 'Multi-Region News Scraper API',
        'version': '1.0.0',
        'description': 'REST API for scraping and accessing news from Kenya and USA',
        'endpoints': {
            'GET /api/sources': 'List all available news sources',
            'GET /api/articles': 'Get scraped articles',
            'GET /api/articles/<region>': 'Get articles by region',
            'GET /api/stats': 'Get scraping statistics',
            'POST /api/scrape': 'Trigger a new scraping job',
            'POST /api/scrape/<region>': 'Scrape specific region',
            'GET /api/health': 'Health check endpoint',
        }
    })


@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/sources')
def list_sources():
    """List all available news sources."""
    sources = NewsScraper.list_sources()
    return jsonify({
        'success': True,
        'sources': sources,
        'total_count': sum(len(s) for s in sources.values())
    })


@app.route('/api/articles')
def get_articles():
    """
    Get scraped articles.
    
    Query parameters:
        - region: Filter by region (kenya/usa)
        - source: Filter by source name
        - limit: Maximum number of results (default: 50)
        - offset: Pagination offset (default: 0)
    """
    region = request.args.get('region')
    source = request.args.get('source')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        articles = db.get_articles(
            region=region,
            source=source,
            limit=limit,
            offset=offset
        )
        
        total_count = db.get_article_count(region=region, source=source)
        
        return jsonify({
            'success': True,
            'articles': articles,
            'count': len(articles),
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': offset + len(articles) < total_count
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/articles/<region>')
def get_articles_by_region(region: str):
    """Get articles filtered by region."""
    if region not in ['kenya', 'usa']:
        return jsonify({
            'success': False,
            'error': 'Invalid region. Must be "kenya" or "usa"'
        }), 400
    
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        articles = db.get_articles(
            region=region,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'region': region,
            'articles': articles,
            'count': len(articles)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats')
def get_stats():
    """Get database statistics."""
    try:
        sources = db.get_sources()
        total_articles = db.get_article_count()
        kenya_count = db.get_article_count(region='kenya')
        usa_count = db.get_article_count(region='usa')
        
        return jsonify({
            'success': True,
            'stats': {
                'total_articles': total_articles,
                'by_region': {
                    'kenya': kenya_count,
                    'usa': usa_count
                },
                'sources': sources
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/scrape', methods=['POST'])
def trigger_scrape():
    """
    Trigger a new scraping job.
    
    Request body (optional):
        - region: Specific region to scrape
        - source: Specific source to scrape
    """
    try:
        data = request.get_json() or {}
        region = data.get('region')
        source = data.get('source')
        
        # Create new scraper instance
        new_scraper = NewsScraper()
        
        if source:
            articles = new_scraper.scrape_source(source)
        elif region:
            articles = new_scraper.scrape_region(region)
        else:
            articles = new_scraper.scrape_all()
        
        # Save to database
        saved_count = db.export(articles)
        
        stats = new_scraper.get_stats()
        
        return jsonify({
            'success': True,
            'message': f'Scraped {len(articles)} articles',
            'articles_scraped': len(articles),
            'articles_saved': saved_count,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/scrape/<region>', methods=['POST'])
def trigger_region_scrape(region: str):
    """Trigger scraping for a specific region."""
    if region not in ['kenya', 'usa']:
        return jsonify({
            'success': False,
            'error': 'Invalid region. Must be "kenya" or "usa"'
        }), 400
    
    try:
        new_scraper = NewsScraper()
        articles = new_scraper.scrape_region(region)
        
        saved_count = db.export(articles)
        
        return jsonify({
            'success': True,
            'region': region,
            'articles_scraped': len(articles),
            'articles_saved': saved_count
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/search')
def search_articles():
    """
    Search articles by keyword.
    
    Query parameters:
        - q: Search query (searches title and summary)
        - limit: Maximum results (default: 20)
    """
    query = request.args.get('q', '')
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query (q) is required'
        }), 400
    
    try:
        # Get all articles and filter (simple implementation)
        # For production, use full-text search in SQLite
        all_articles = db.get_articles(limit=500)
        
        query_lower = query.lower()
        matching = [
            a for a in all_articles
            if query_lower in a.get('title', '').lower() or
               query_lower in (a.get('summary') or '').lower()
        ][:limit]
        
        return jsonify({
            'success': True,
            'query': query,
            'results': matching,
            'count': len(matching)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


# ============================================================================
# Main
# ============================================================================

def main():
    """Run the API server."""
    host = SETTINGS.get('api_host', '0.0.0.0')
    port = SETTINGS.get('api_port', 5000)
    debug = SETTINGS.get('api_debug', False)
    
    print(f"\n🚀 Starting News Scraper API")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"\n   API Documentation: http://localhost:{port}/")
    print(f"   Health Check: http://localhost:{port}/api/health\n")
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()
