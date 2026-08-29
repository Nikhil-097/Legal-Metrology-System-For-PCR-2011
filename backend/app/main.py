import os
import logging
from dotenv import load_dotenv

# Automatically load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import scans, auth, rules, reports, analytics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Legal Metrology Compliance System",
    description="Automated audit and verification for Packaged Commodities Rules 2011",
    version="1.0.0",
)

# CORS Configuration for local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(scans.router, prefix="/api/v1/scans", tags=["Scans"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(rules.router, prefix="/api/v1/rules", tags=["Rules"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])


@app.on_event("startup")
async def startup_event():
    logger.info("[*] Starting Legal Metrology Compliance Verification API v1.0.0")
    rules_path = os.path.join(os.path.dirname(__file__), "..", "data", "legal_metrology_rules.json")
    if os.path.exists(rules_path):
        logger.info(f"[✓] Rule Matrix Seed loaded from: {rules_path}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("[*] Shutting down Legal Metrology Verification Service...")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "legal-metrology-backend"}