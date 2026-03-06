"""
Proxy Manager
=============

HAProxy configuration management service with web UI.
"""

from pathlib import Path

__version__: str = "1.3.0"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles

from proxy_manager.api import router
from proxy_manager.utilities.lifespan import lifespan
from proxy_manager.utilities.rate_limit import limiter

_BASE_DIR = Path(__file__).parent

app = FastAPI(
    title="Proxy Manager",
    version=__version__,
    description="HAProxy configuration management service with web UI.",
    lifespan=lifespan,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(_BASE_DIR / "static")), name="static")
app.include_router(router)

__all__ = ["app", "__version__"]
