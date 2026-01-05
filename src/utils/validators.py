"""
Validators and Utilities
Text cleaning, URL validation, date parsing utilities.
"""
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse, urljoin
from dateutil import parser as date_parser
from dateutil.tz import tzutc, tzlocal


def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
    
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def normalize_url(url: str, base_url: str = None) -> str:
    """
    Normalize a URL, handling relative URLs.
    
    Args:
        url: URL to normalize
        base_url: Base URL for relative URLs
    
    Returns:
        Normalized absolute URL
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Handle relative URLs
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    # Ensure https
    if url.startswith('http://'):
        url = 'https://' + url[7:]
    
    return url


def clean_text(text: str, max_length: int = None) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Text to clean
        max_length: Optional maximum length
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove common unwanted patterns
    patterns_to_remove = [
        r'\s*\[\.\.\.?\]',  # [...] or [..]
        r'\s*Read more\.?',
        r'\s*Continue reading\.?',
        r'\s*Click here\.?',
        r'^\s*Advertisement\s*$',
        r'\s*Share this:?\s*',
    ]
    
    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up HTML entities
    html_entities = {
        '&nbsp;': ' ',
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&quot;': '"',
        '&#39;': "'",
        '&mdash;': '—',
        '&ndash;': '–',
    }
    
    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)
    
    # Final cleanup
    text = text.strip()
    
    # Truncate if needed
    if max_length and len(text) > max_length:
        text = text[:max_length - 3] + '...'
    
    return text


def parse_date(date_string: str) -> Optional[datetime]:
    """
    Parse various date formats into datetime object.
    
    Args:
        date_string: Date string to parse
    
    Returns:
        Datetime object or None if parsing fails
    """
    if not date_string:
        return None
    
    # Clean the string
    date_string = date_string.strip()
    
    # Handle relative dates
    relative_patterns = {
        r'(\d+)\s*minutes?\s*ago': lambda m: datetime.now() - timedelta(minutes=int(m.group(1))),
        r'(\d+)\s*hours?\s*ago': lambda m: datetime.now() - timedelta(hours=int(m.group(1))),
        r'(\d+)\s*days?\s*ago': lambda m: datetime.now() - timedelta(days=int(m.group(1))),
        r'just\s*now': lambda m: datetime.now(),
        r'today': lambda m: datetime.now().replace(hour=0, minute=0, second=0),
        r'yesterday': lambda m: (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0),
    }
    
    from datetime import timedelta
    
    for pattern, handler in relative_patterns.items():
        match = re.search(pattern, date_string, re.IGNORECASE)
        if match:
            return handler(match)
    
    # Try standard date parsing
    try:
        return date_parser.parse(date_string, fuzzy=True)
    except Exception:
        pass
    
    # Try common formats manually
    date_formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d %B %Y',
        '%B %d, %Y',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%d-%m-%Y',
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    return None


def extract_domain(url: str) -> str:
    """
    Extract domain name from URL.
    
    Args:
        url: URL to extract domain from
    
    Returns:
        Domain name
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def is_valid_article_url(url: str, base_domain: str = None) -> bool:
    """
    Check if URL appears to be a valid article URL.
    
    Args:
        url: URL to check
        base_domain: Expected domain
    
    Returns:
        True if appears to be valid article URL
    """
    if not validate_url(url):
        return False
    
    # Check domain matches if specified
    if base_domain:
        url_domain = extract_domain(url)
        base_domain_clean = extract_domain(base_domain) if '://' in base_domain else base_domain
        if base_domain_clean not in url_domain:
            return False
    
    # Exclude common non-article URLs
    excluded_patterns = [
        r'/tag/',
        r'/category/',
        r'/author/',
        r'/search',
        r'/login',
        r'/register',
        r'/subscribe',
        r'/advertisement',
        r'\.pdf$',
        r'\.jpg$',
        r'\.png$',
        r'\.gif$',
    ]
    
    url_lower = url.lower()
    for pattern in excluded_patterns:
        if re.search(pattern, url_lower):
            return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string for use as a filename.
    
    Args:
        filename: String to sanitize
    
    Returns:
        Safe filename string
    """
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename
