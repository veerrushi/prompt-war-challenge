"""
RainReady AI – FastAPI application entry point.

Configures middleware, routers, static-file serving, and exception handlers.
"""

import logging
import logging.config
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import chat
from app.core.config import get_settings
from app.core.limiter import limiter

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s – %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).parent.parent / "static"

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

settings = get_settings()

app = FastAPI(
    title="RainReady AI",
    description="GenAI Assistant for Monsoon Preparedness & Citizen Assistance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# -- Rate limiting -----------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# -- CORS --------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Routers -----------------------------------------------------------------
app.include_router(chat.router, prefix="/api", tags=["Chat"])

# -- Static files ------------------------------------------------------------
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    logger.info("Static files mounted from %s", STATIC_DIR)
else:
    logger.warning(
        "Static directory not found at %s – UI will be unavailable", STATIC_DIR
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/", include_in_schema=False)
async def serve_ui() -> FileResponse:
    """Serve the single-page frontend."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    logger.warning("index.html not found at %s", index_path)
    return JSONResponse(status_code=404, content={"detail": "Frontend not found."})


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Liveness probe – returns service status."""
    return {"status": "ok"}
