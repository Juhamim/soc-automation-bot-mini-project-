from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.models import HealthResponse
from app.api.routes import router
from app.core.config import settings
from contextlib import asynccontextmanager
import asyncio
from app.core.websockets import manager

# Configure structured logging
logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(manager.listen_to_redis())
    yield
    task.cancel()

app = FastAPI(
    lifespan=lifespan,
    title="SOC Automation Bot API",
    description=(
        "A SOAR-based Security Incident Automation System. "
        "Ingests security alerts, enriches them with threat intelligence, "
        "scores risk, and executes automated response playbooks."
    ),
    version="1.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────
app.include_router(router, prefix="/api/v1")

import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import ResponseValidationError

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    err_msg = traceback.format_exc()
    logging.error(f"Global exception: {err_msg}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "traceback": err_msg}
    )

@app.exception_handler(ResponseValidationError)
async def validation_exception_handler(request: Request, exc: ResponseValidationError):
    logging.error(f"Response validation error: {exc.errors()}")
    return JSONResponse(
        status_code=500,
        content={"detail": exc.errors()}
    )

# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    return HealthResponse(
        status="ok",
        version="1.2.0",
        environment=settings.APP_ENV,
    )


@app.get("/", tags=["System"])
async def root():
    return {
        "service": "SOC Automation Bot",
        "version": "1.2.0",
        "docs": "/docs",
        "health": "/health",
    }
