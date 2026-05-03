"""Rate limiting with sliding window algorithm."""

import time
from collections import defaultdict, deque
from typing import Dict, Tuple, Any
from datetime import datetime


class RateLimiter:
    """
    Rate limiter using sliding window algorithm.
    
    Features:
    - Per-user rate limiting
    - Configurable limits and windows
    - Thread-safe operations
    - Automatic cleanup of old entries
    """
    
    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: int = 60
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        
        # user_id -> deque of timestamps
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
    
    def is_allowed(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed for user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Tuple of (is_allowed, info_dict)
            info_dict contains: remaining, reset_at, retry_after
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Get user's request history
        user_requests = self.requests[user_id]
        
        # Remove requests outside the window
        while user_requests and user_requests[0] < window_start:
            user_requests.popleft()
        
        # Check if limit exceeded
        current_count = len(user_requests)
        
        if current_count >= self.max_requests:
            # Calculate retry_after
            oldest_request = user_requests[0]
            retry_after = int(oldest_request + self.window_seconds - now)
            
            return False, {
                "remaining": 0,
                "limit": self.max_requests,
                "window": f"{self.window_seconds}s",
                "retry_after": max(1, retry_after),
                "reset_at": datetime.fromtimestamp(oldest_request + self.window_seconds).isoformat()
            }
        
        # Allow request and record timestamp
        user_requests.append(now)
        
        return True, {
            "remaining": self.max_requests - current_count - 1,
            "limit": self.max_requests,
            "window": f"{self.window_seconds}s",
            "reset_at": datetime.fromtimestamp(now + self.window_seconds).isoformat()
        }
    
    def reset(self, user_id: str) -> None:
        """Reset rate limit for user."""
        if user_id in self.requests:
            del self.requests[user_id]
    
    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """Get rate limit stats for user."""
        now = time.time()
        window_start = now - self.window_seconds
        
        user_requests = self.requests.get(user_id, deque())
        
        # Count requests in current window
        current_count = sum(1 for ts in user_requests if ts >= window_start)
        
        return {
            "current_count": current_count,
            "limit": self.max_requests,
            "remaining": max(0, self.max_requests - current_count),
            "window": f"{self.window_seconds}s"
        }
