"""
Logging Configuration
Provides centralized logging setup for the scraper.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(
    name: str = "news_scraper",
    log_file: str = None,
    level: str = "INFO"
) -> logging.Logger:
    """
    Set up and configure a logger.
    
    Args:
        name: Logger name
        log_file: Path to log file (optional)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "news_scraper") -> logging.Logger:
    """
    Get an existing logger or create a new one.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class ScraperLogger:
    """
    Context-aware logger for scraping operations.
    """
    
    def __init__(self, name: str = "news_scraper"):
        self.logger = get_logger(name)
        self.stats = {
            'articles_scraped': 0,
            'errors': 0,
            'sources_completed': 0,
            'start_time': None,
            'end_time': None
        }
    
    def start_session(self):
        """Mark the start of a scraping session."""
        self.stats['start_time'] = datetime.now()
        self.logger.info("=" * 60)
        self.logger.info("Starting new scraping session")
        self.logger.info("=" * 60)
    
    def end_session(self):
        """Mark the end of a scraping session and log summary."""
        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']
        
        self.logger.info("=" * 60)
        self.logger.info("Scraping session completed")
        self.logger.info(f"Duration: {duration}")
        self.logger.info(f"Articles scraped: {self.stats['articles_scraped']}")
        self.logger.info(f"Sources completed: {self.stats['sources_completed']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info("=" * 60)
    
    def log_source_start(self, source_name: str):
        """Log the start of scraping a source."""
        self.logger.info(f"Starting to scrape: {source_name}")
    
    def log_source_complete(self, source_name: str, article_count: int):
        """Log completion of scraping a source."""
        self.stats['sources_completed'] += 1
        self.stats['articles_scraped'] += article_count
        self.logger.info(f"Completed {source_name}: {article_count} articles")
    
    def log_error(self, message: str, exc: Exception = None):
        """Log an error."""
        self.stats['errors'] += 1
        if exc:
            self.logger.error(f"{message}: {str(exc)}")
        else:
            self.logger.error(message)
    
    def log_warning(self, message: str):
        """Log a warning."""
        self.logger.warning(message)
    
    def log_debug(self, message: str):
        """Log debug information."""
        self.logger.debug(message)
    
    def log_info(self, message: str):
        """Log information."""
        self.logger.info(message)
