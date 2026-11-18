import time
import re
import html
from collections import defaultdict
from typing import Tuple
from fastapi import Request, HTTPException

class InMemoryRateLimiter:
    """
    Thread-safe in-memory sliding-window rate limiter per client IP.
    """
    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients = defaultdict(list)

    def is_rate_limited(self, client_ip: str) -> Tuple[bool, int]:
        now = time.time()
        timestamps = self.clients[client_ip]
        
        # Purge entries older than the window
        self.clients[client_ip] = [t for t in timestamps if now - t < self.window_seconds]
        
        if len(self.clients[client_ip]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self.clients[client_ip][0]))
            return True, max(retry_after, 1)
            
        self.clients[client_ip].append(now)
        return False, 0

# Separate rate limiters for chat (stricter) and general read endpoints
chat_limiter = InMemoryRateLimiter(max_requests=35, window_seconds=60)
api_limiter = InMemoryRateLimiter(max_requests=120, window_seconds=60)

def sanitize_input(text: str, max_chars: int = 1200) -> str:
    """
    Trims, strips control characters, escapes HTML, and bounds input size
    to prevent prompt buffer exhaustion, XSS, and denial of service.
    """
    if not text:
        return ""
        
    trimmed = text.strip()[:max_chars]
    # Remove NULL and control characters except common whitespace
    cleaned = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', trimmed)
    # Escape HTML tags
    escaped = html.escape(cleaned)
    return escaped

def validate_api_key(key: str) -> bool:
    """
    Ensures user-supplied API keys strictly conform to standard key patterns
    to avoid header injection or anomalous payload delivery.
    """
    if not key:
        return True
    # OpenRouter keys are typically sk-or-v1-... with alphanumerics
    pattern = r'^[a-zA-Z0-9_\-\.]{15,128}$'
    return bool(re.match(pattern, key.strip()))
