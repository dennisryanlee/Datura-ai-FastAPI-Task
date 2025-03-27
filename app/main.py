from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.tasks import router as tasks_router
from app.api.routes.history import router as history_router
import time
import asyncio

from app.core.config import settings
from app.api.routes.dividends import router as dividends_router
from app.db.database import init_db

description = """
# Bittensor Dividends API

This API provides access to Tao dividends data from the Bittensor blockchain.

## Features

* **Tao Dividends**: Query dividend data for a specific hotkey and subnet
* **Sentiment Analysis**: Analyze Twitter sentiment for a subnet (when trade=true)
* **Automatic Staking**: Stake or unstake based on sentiment (when trade=true)

All data is cached for 2 minutes for optimal performance.
"""

app = FastAPI(
    title="Bittensor API",
    description="API for querying Bittensor blockchain data and performing sentiment-based staking",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers for startup and shutdown
@app.on_event("startup")
async def startup_event():
    # Initialize database
    await init_db()

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# Include routers
app.include_router(
    dividends_router,
    prefix=settings.API_V1_STR,
    tags=["dividends"]
)

app.include_router(
    tasks_router,
    prefix=f"{settings.API_V1_STR}/tasks",
    tags=["tasks"]
)

app.include_router(
    history_router,
    prefix=f"{settings.API_V1_STR}/history",
    tags=["history"]
)

@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/", tags=["root"])
async def root():
    """Redirect to API documentation"""
    return {"message": "Welcome to Bittensor Dividends API. See /docs for documentation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)