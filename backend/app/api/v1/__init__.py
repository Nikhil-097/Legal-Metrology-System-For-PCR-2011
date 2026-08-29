"""
API Version 1 (v1) Endpoints Package.
Exposes modular routers for scans, authentication, rules, reports, and analytics.
"""

from app.api.v1.auth import router as auth_router
from app.api.v1.scans import router as scans_router
from app.api.v1.rules import router as rules_router
from app.api.v1.reports import router as reports_router
from app.api.v1.analytics import router as analytics_router

__all__ = [
    "auth_router",
    "scans_router",
    "rules_router",
    "reports_router",
    "analytics_router",
]