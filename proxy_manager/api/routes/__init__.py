"""
API routes package
==================
"""

from fastapi import APIRouter

from proxy_manager.api.routes.admin import router as admin_router
from proxy_manager.api.routes.auth import router as auth_router
from proxy_manager.api.routes.backends import router as backends_router
from proxy_manager.api.routes.caches import router as caches_router
from proxy_manager.api.routes.config_io import router as config_io_router
from proxy_manager.api.routes.frontends import router as frontends_router
from proxy_manager.api.routes.http_errors import router as http_errors_router
from proxy_manager.api.routes.listen import router as listen_router
from proxy_manager.api.routes.mailers import router as mailers_router
from proxy_manager.api.routes.peers import router as peers_router
from proxy_manager.api.routes.resolvers import router as resolvers_router
from proxy_manager.api.routes.settings import router as settings_router
from proxy_manager.api.routes.ssl_certificates import router as ssl_router
from proxy_manager.api.routes.userlists import router as userlists_router

router = APIRouter()

router.include_router(admin_router)
router.include_router(auth_router)
router.include_router(settings_router)
router.include_router(userlists_router)
router.include_router(frontends_router)
router.include_router(backends_router)
router.include_router(listen_router)
router.include_router(resolvers_router)
router.include_router(peers_router)
router.include_router(mailers_router)
router.include_router(http_errors_router)
router.include_router(caches_router)
router.include_router(ssl_router)
router.include_router(config_io_router)
