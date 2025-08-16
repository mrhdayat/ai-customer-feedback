import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import settings
from middleware import limiter, SecurityMiddleware, rate_limit_handler, log_request_middleware
from routers import auth, projects, feedbacks, orchestrate
from models import HealthResponse
from services.analysis_pipeline import process_orchestrate_jobs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Background task for orchestrate job processing
background_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global background_task
    
    logger.info("Starting Customer Feedback Dashboard API")
    
    # Start background task for orchestrate job processing
    background_task = asyncio.create_task(process_orchestrate_jobs())
    logger.info("Started orchestrate job processor")
    
    yield
    
    # Cleanup
    if background_task:
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Customer Feedback Dashboard API stopped")


# Create FastAPI app
app = FastAPI(
    title="Customer Feedback Dashboard API",
    description="""
    AI-powered customer feedback analysis system supporting Indonesian and international languages.
    
    ## Features
    
    - **Multi-language Sentiment Analysis** (Indonesian & English)
    - **Zero-shot Topic Classification** 
    - **Entity/Concept Extraction** via IBM Watson NLU
    - **AI-powered Summary & Recommendations** via IBM Granite 3.3-8B
    - **Automated Follow-up Actions** via IBM Orchestrate
    - **Role-based Access Control** (Demo, Member, Admin)
    
    ## Authentication
    
    Use the `/api/auth/login` endpoint with demo credentials:
    - Demo: `demo@cfd.app` / `demo12345` (read-only)
    - Member: `member@cfd.app` / `member12345` (full features)
    - Admin: `admin@cfd.app` / `admin12345` (admin features)
    
    ## Rate Limiting
    
    API requests are rate-limited to prevent abuse. Current limits:
    - General: 60 requests per minute per IP
    - Specific endpoints may have additional limits
    """,
    version="1.0.0",
    contact={
        "name": "Customer Feedback Dashboard Support",
        "email": "support@cfd.app"
    },
    lifespan=lifespan
)

# Add security middleware
app.add_middleware(SecurityMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Add request logging middleware
app.middleware("http")(log_request_middleware)

# Include routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(feedbacks.router)
app.include_router(orchestrate.router)


@app.get("/", response_model=dict)
async def root():
    """Root endpoint"""
    return {
        "message": "Customer Feedback Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    
    # Check service status
    services = {
        "api": "healthy",
        "database": "healthy",  # Could add actual DB health check
        "redis": "healthy",     # Could add actual Redis health check
        "ai_services": "healthy"  # Could add actual AI service health checks
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        services=services
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "message": "Endpoint not found",
            "detail": f"The endpoint {request.url.path} does not exist"
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later."
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level="info"
    )
