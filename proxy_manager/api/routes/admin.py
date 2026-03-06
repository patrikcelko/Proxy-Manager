"""
Admin dashboard route
=====================
"""

from pathlib import Path

from fastapi import APIRouter, Request, Response
from fastapi.templating import Jinja2Templates

from proxy_manager import __version__

router = APIRouter()

_BASE_DIR = Path(__file__).parent.parent.parent
templates = Jinja2Templates(directory=str(_BASE_DIR / "static" / "templates"))


@router.get("/", include_in_schema=False)
@router.get("/admin", include_in_schema=False)
async def admin_dashboard(request: Request) -> Response:
    """Serve the admin dashboard SPA."""

    return templates.TemplateResponse(request, "admin.html", {"version": __version__})
