# Author: Jerry Onyango
# Contribution: Boots the FastAPI application, registers domain routers, and serves health and contract endpoints.
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core import configure_logging, load_settings
from .routers import alerts, auth, control_loop, edge, roi, users

app = FastAPI(
    title="Energy Allocation API",
    version="1.0.0",
    description="FastAPI scaffold for Energy Allocation v1 contract",
)

cors_origins = [
    origin.strip()
    for origin in os.getenv("EA_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
allow_all_origins = len(cors_origins) == 1 and cors_origins[0] == "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(control_loop.router)
app.include_router(alerts.router)
app.include_router(edge.router)
app.include_router(roi.router)
app.include_router(users.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def run() -> None:
    import uvicorn

    settings = load_settings()
    configure_logging()
    uvicorn.run("energy_api.main:app", host=settings.api_host, port=settings.api_port, reload=settings.env == "development")
