from fastapi import Request, HTTPException
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import asyncio


class RateLimiter:
    """
    In-memory rate limiter for API endpoints
    Tracks requests per user/IP and enforces limits
    """
    
    def __init__(self):
        # Format: {identifier: [(timestamp, count)]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()
    
    async def is_allowed(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        Check if request is allowed under rate limit
        
        Args:
            identifier: User ID or IP address
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        async with self.lock:
            now = datetime.now()
            cutoff_time = now - timedelta(seconds=window_seconds)
            
            # Clean old requests
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff_time
            ]
            
            current_count = len(self.requests[identifier])
            
            if current_count >= max_requests:
                return False, 0
            
            # Add current request
            self.requests[identifier].append(now)
            remaining = max_requests - current_count - 1
            
            return True, remaining
    
    async def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """
        Clean up entries older than max_age_seconds
        Should be called periodically
        """
        async with self.lock:
            cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
            
            identifiers_to_remove = []
            for identifier, requests in self.requests.items():
                # Remove old requests
                self.requests[identifier] = [
                    req_time for req_time in requests
                    if req_time > cutoff_time
                ]
                
                # Mark empty identifiers for removal
                if not self.requests[identifier]:
                    identifiers_to_remove.append(identifier)
            
            # Remove empty identifiers
            for identifier in identifiers_to_remove:
                del self.requests[identifier]


# Global rate limiter instance
rate_limiter = RateLimiter()


async def rate_limit_dependency(
    request: Request,
    max_requests: int = 10,
    window_seconds: int = 60
):
    """
    FastAPI dependency for rate limiting
    
    Usage:
        @router.post("/endpoint")
        async def endpoint(rate_limit: None = Depends(lambda r: rate_limit_dependency(r, 5, 60))):
            ...
    """
    # Try to get user identifier from auth
    user_id = None
    if hasattr(request.state, 'user'):
        user_id = request.state.user.id
    
    # Fall back to IP address
    identifier = user_id or request.client.host
    
    allowed, remaining = await rate_limiter.is_allowed(
        identifier,
        max_requests,
        window_seconds
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {window_seconds} seconds.",
            headers={"Retry-After": str(window_seconds)}
        )
    
    # Add rate limit headers to response
    request.state.rate_limit_remaining = remaining
    request.state.rate_limit_limit = max_requests
