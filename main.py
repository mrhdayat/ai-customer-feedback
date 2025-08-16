#!/usr/bin/env python3
"""
Railway deployment entry point for Customer Feedback Dashboard Backend
"""
import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Import the FastAPI app from backend
try:
    from main import app
    print("✅ Successfully imported FastAPI app from backend/main.py")
except ImportError as e:
    print(f"❌ Failed to import app: {e}")
    sys.exit(1)

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Railway sets this)
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🚀 Starting Customer Feedback Dashboard Backend")
    print(f"📡 Host: {host}:{port}")
    print(f"🌍 Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'development')}")
    
    # Start the server
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info",
        access_log=True
    )
