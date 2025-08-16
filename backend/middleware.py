from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
import logging
from config import settings

logger = logging.getLogger(__name__)

# Initialize Redis for rate limiting
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Rate limiting will use in-memory storage.")
    redis_client = None

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url if redis_client else "memory://",
    default_limits=[f"{settings.rate_limit_per_minute}/minute"]
)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit exceeded handler"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "message": "Rate limit exceeded. Please try again later.",
            "detail": str(exc.detail)
        }
    )


class SecurityMiddleware:
    """Security middleware for headers and validation"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Add security headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    
                    # Security headers
                    security_headers = {
                        b"x-content-type-options": b"nosniff",
                        b"x-frame-options": b"DENY",
                        b"x-xss-protection": b"1; mode=block",
                        b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                        b"content-security-policy": (
                            b"default-src 'self'; "
                            b"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                            b"style-src 'self' 'unsafe-inline'; "
                            b"img-src 'self' data: https:; "
                            b"connect-src 'self' https://api-inference.huggingface.co "
                            b"https://*.supabase.co https://replicate.com "
                            b"https://*.watson.cloud.ibm.com https://dl.watson-orchestrate.ibm.com; "
                            b"font-src 'self' data:; "
                            b"frame-ancestors 'none';"
                        )
                    }
                    
                    headers.update(security_headers)
                    message["headers"] = list(headers.items())
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


async def log_request_middleware(request: Request, call_next):
    """Middleware to log requests"""
    start_time = time.time()
    
    # Log request
    logger.info(f"{request.method} {request.url.path} - {request.client.host}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response {response.status_code} - {process_time:.3f}s")
    
    return response


import time
