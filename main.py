#!/usr/bin/env python3
"""
News Scraper CLI
Command-line interface for the multi-region news scraper.
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scraper import NewsScraper
from src.utils.logger import setup_logger
from config.settings import SETTINGS


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Multi-Region News Scraper - Scrape news from Kenya and USA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python main.py --all                     Scrape all sources
  python main.py --region kenya            Scrape Kenya sources only
  python main.py --region usa              Scrape USA sources only
  python main.py --source "CNN"            Scrape specific source
  python main.py --all --format json       Export to JSON
  python main.py --all --format csv        Export to CSV
  python main.py --all --format sqlite     Export to SQLite
  python main.py --list                    List all available sources
  python main.py --schedule 6              Run every 6 hours
        '''
    )
    
    # Scraping options
    scrape_group = parser.add_mutually_exclusive_group()
    scrape_group.add_argument(
        '--all', '-a',
        action='store_true',
        help='Scrape all configured news sources'
    )
    scrape_group.add_argument(
        '--region', '-r',
        choices=['kenya', 'usa'],
        help='Scrape news from a specific region'
    )
    scrape_group.add_argument(
        '--source', '-s',
        type=str,
        help='Scrape news from a specific source by name'
    )
    scrape_group.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available news sources'
    )
    
    # Export options
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'csv', 'sqlite', 'all'],
        default='json',
        help='Output format (default: json)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output filename (auto-generated if not specified)'
    )
    
    # Scheduling options
    parser.add_argument(
        '--schedule',
        type=int,
        metavar='HOURS',
        help='Run scraper every N hours'
    )
    
    # Other options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )
    
    return parser.parse_args()


def list_sources():
    """List all available news sources."""
    sources = NewsScraper.list_sources()
    
    print("\n" + "=" * 60)
    print("Available News Sources")
    print("=" * 60)
    
    for region, source_list in sources.items():
        print(f"\n🌍 {region.upper()}")
        print("-" * 40)
        for source in source_list:
            print(f"  • {source}")
    
    print("\n" + "=" * 60)
    print(f"Total: {sum(len(s) for s in sources.values())} sources")
    print("=" * 60 + "\n")


def run_scraper(args):
    """Run the scraper with given arguments."""
    scraper = NewsScraper()
    
    print("\n" + "=" * 60)
    print("🗞️  Multi-Region News Scraper")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # Determine what to scrape
    if args.all:
        print("Mode: Scraping ALL sources")
        articles = scraper.scrape_all()
    elif args.region:
        print(f"Mode: Scraping {args.region.upper()} sources")
        articles = scraper.scrape_region(args.region)
    elif args.source:
        print(f"Mode: Scraping source '{args.source}'")
        articles = scraper.scrape_source(args.source)
    else:
        print("Mode: Scraping ALL sources (default)")
        articles = scraper.scrape_all()
    
    # Display results
    print("-" * 60)
    print(f"✅ Scraped {len(articles)} articles")
    
    stats = scraper.get_stats()
    if stats.get('by_region'):
        for region, count in stats['by_region'].items():
            print(f"   - {region.upper()}: {count} articles")
    
    # Export results
    print("-" * 60)
    print("Exporting data...")
    
    export_format = args.format
    output_file = args.output
    
    if export_format == 'all':
        json_path = scraper.export_to_json()
        print(f"📄 JSON: {json_path}")
        
        csv_path = scraper.export_to_csv()
        print(f"📊 CSV: {csv_path}")
        
        count = scraper.export_to_sqlite()
        print(f"🗃️  SQLite: {count} articles saved")
    
    elif export_format == 'json':
        path = scraper.export_to_json(output_file)
        print(f"📄 Exported to: {path}")
    
    elif export_format == 'csv':
        path = scraper.export_to_csv(output_file)
        print(f"📊 Exported to: {path}")
    
    elif export_format == 'sqlite':
        count = scraper.export_to_sqlite(output_file)
        print(f"🗃️  Saved {count} articles to SQLite database")
    
    print("-" * 60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if stats.get('duration'):
        print(f"Duration: {stats['duration']}")
    print("=" * 60 + "\n")
    
    return articles


def run_scheduled(hours: int):
    """Run scraper on a schedule."""
    import schedule
    
    print(f"\n🕐 Scheduler started - running every {hours} hour(s)")
    print("Press Ctrl+C to stop\n")
    
    # Create args for full scrape
    class ScheduleArgs:
        all = True
        region = None
        source = None
        format = 'all'
        output = None
    
    args = ScheduleArgs()
    
    # Run immediately
    run_scraper(args)
    
    # Schedule subsequent runs
    schedule.every(hours).hours.do(run_scraper, args)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\n\n⏹️  Scheduler stopped")


def main():
    """Main entry point."""
    args = parse_args()
    
    # Set up logging
    log_level = 'DEBUG' if args.verbose else ('ERROR' if args.quiet else 'INFO')
    setup_logger('news_scraper', SETTINGS.get('log_file'), log_level)
    
    try:
        if args.list:
            list_sources()
        elif args.schedule:
            run_scheduled(args.schedule)
        else:
            run_scraper(args)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Scraping cancelled by user")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
