"""
Rate Limiter
Implements rate limiting to respect website policies and avoid being blocked.
"""
import time
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock
from typing import Optional


class RateLimiter:
    """
    Rate limiter for controlling request frequency per domain.
    Implements token bucket algorithm for smooth rate limiting.
    """
    
    def __init__(
        self,
        requests_per_second: float = 0.5,
        burst_size: int = 3
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum sustained request rate
            burst_size: Maximum burst of requests allowed
        """
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.tokens = defaultdict(lambda: burst_size)
        self.last_update = defaultdict(datetime.now)
        self.lock = Lock()
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def _refill_tokens(self, domain: str):
        """Refill tokens based on time elapsed."""
        now = datetime.now()
        time_passed = (now - self.last_update[domain]).total_seconds()
        new_tokens = time_passed * self.requests_per_second
        self.tokens[domain] = min(
            self.burst_size,
            self.tokens[domain] + new_tokens
        )
        self.last_update[domain] = now
    
    def acquire(self, url: str) -> float:
        """
        Acquire permission to make a request.
        Returns the time to wait before making the request.
        
        Args:
            url: The URL being requested
        
        Returns:
            Time to wait in seconds (0 if can proceed immediately)
        """
        domain = self._get_domain(url)
        
        with self.lock:
            self._refill_tokens(domain)
            
            if self.tokens[domain] >= 1:
                self.tokens[domain] -= 1
                return 0
            else:
                # Calculate wait time
                wait_time = (1 - self.tokens[domain]) / self.requests_per_second
                return wait_time
    
    def wait(self, url: str):
        """
        Wait if necessary before making a request.
        
        Args:
            url: The URL being requested
        """
        wait_time = self.acquire(url)
        if wait_time > 0:
            time.sleep(wait_time)
    
    async def async_wait(self, url: str):
        """
        Async version of wait.
        
        Args:
            url: The URL being requested
        """
        wait_time = self.acquire(url)
        if wait_time > 0:
            await asyncio.sleep(wait_time)


class AdaptiveRateLimiter(RateLimiter):
    """
    Adaptive rate limiter that adjusts based on response codes.
    Slows down on errors, speeds up on success.
    """
    
    def __init__(
        self,
        initial_rate: float = 0.5,
        min_rate: float = 0.1,
        max_rate: float = 2.0,
        burst_size: int = 3
    ):
        super().__init__(initial_rate, burst_size)
        self.current_rate = defaultdict(lambda: initial_rate)
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.success_streak = defaultdict(int)
        self.error_streak = defaultdict(int)
    
    def record_success(self, url: str):
        """Record a successful request."""
        domain = self._get_domain(url)
        self.success_streak[domain] += 1
        self.error_streak[domain] = 0
        
        # Speed up after consecutive successes
        if self.success_streak[domain] >= 5:
            new_rate = min(
                self.current_rate[domain] * 1.1,
                self.max_rate
            )
            self.current_rate[domain] = new_rate
            self.requests_per_second = new_rate
            self.success_streak[domain] = 0
    
    def record_error(self, url: str, status_code: int = None):
        """Record a failed request."""
        domain = self._get_domain(url)
        self.error_streak[domain] += 1
        self.success_streak[domain] = 0
        
        # Slow down on errors
        if status_code == 429 or self.error_streak[domain] >= 2:
            new_rate = max(
                self.current_rate[domain] * 0.5,
                self.min_rate
            )
            self.current_rate[domain] = new_rate
            self.requests_per_second = new_rate
            self.error_streak[domain] = 0


class DomainThrottler:
    """
    Simple domain-based throttler with configurable delays.
    """
    
    def __init__(self, default_delay: float = 2.0):
        """
        Initialize throttler.
        
        Args:
            default_delay: Default delay between requests to same domain
        """
        self.default_delay = default_delay
        self.domain_delays = {}
        self.last_request = {}
        self.lock = Lock()
    
    def set_domain_delay(self, domain: str, delay: float):
        """Set custom delay for a specific domain."""
        self.domain_delays[domain] = delay
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    
    def throttle(self, url: str):
        """
        Apply throttling for a URL.
        Blocks until it's safe to make the request.
        """
        domain = self._get_domain(url)
        delay = self.domain_delays.get(domain, self.default_delay)
        
        with self.lock:
            now = time.time()
            if domain in self.last_request:
                elapsed = now - self.last_request[domain]
                if elapsed < delay:
                    time.sleep(delay - elapsed)
            
            self.last_request[domain] = time.time()
    
    async def async_throttle(self, url: str):
        """Async version of throttle."""
        domain = self._get_domain(url)
        delay = self.domain_delays.get(domain, self.default_delay)
        
        now = time.time()
        if domain in self.last_request:
            elapsed = now - self.last_request[domain]
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
        
        self.last_request[domain] = time.time()
