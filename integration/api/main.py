"""TaxSaint FastAPI application entry point."""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database_manager.connection import init_db
from integration.api.routes import financial, fraud, tax, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize missing database tables and default tax rules on startup."""
    init_db()
    yield


app = FastAPI(
    title="TaxSaint API",
    version="0.1.0",
    description="Financial analysis, tax calculation, and potential anomaly detection API.",
    lifespan=lifespan,
)

origins = [
    item.strip()
    for item in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173",
    ).split(",")
    if item.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(users.router)
app.include_router(financial.router)
app.include_router(tax.router)
app.include_router(fraud.router)


@app.get("/")
def root():
    return {"name": "TaxSaint API", "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
