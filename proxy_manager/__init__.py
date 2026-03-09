"""
Proxy Manager
=============

HAProxy configuration management service with web UI.
"""

import os
from pathlib import Path

__version__: str = "1.5.0"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

app.state.limiter = limiter

_cors_origins_raw = os.environ.get("PM_CORS_ORIGINS", "*")
_cors_origins: list[str] = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials="*" not in _cors_origins,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(_BASE_DIR / "static")), name="static")
app.include_router(router)

__all__ = ["app", "__version__"]
