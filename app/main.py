import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes import router
from app.core.config import settings
from app.db import init_db


# ============================================================
# LIFESPAN (Replaces Deprecated Startup Event)
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Execute startup logic
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.report_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    
    yield  # Hand control back to the application
    
    # Any shutdown/cleanup logic would go here


# ============================================================
# FASTAPI APPLICATION
# ============================================================
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-assisted packaged-commodity label compliance verification API",
    version="1.0.0",
    lifespan=lifespan  # Attach the lifespan context manager
)


# ============================================================
# CORS
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API ROUTES
# ============================================================
app.include_router(
    router,
    prefix="/api/v1"
)


# ============================================================
# HEALTH CHECK
# ============================================================
@app.get("/health", tags=["system"])
def health():
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }


# ============================================================
# HTML PAGE ROUTES
# ============================================================
@app.get("/")
async def read_login():
    login_file = os.path.join(
        str(settings.frontend_dir),
        "login.html"
    )
    return FileResponse(login_file)


@app.get("/dashboard")
async def read_dashboard():
    dashboard_file = os.path.join(
        str(settings.frontend_dir),
        "index.html"
    )
    return FileResponse(dashboard_file)


# ============================================================
# STATIC FILES (CSS / JAVASCRIPT / IMAGES)
# ============================================================
# Mounted at "/" instead of "/static" so that the browser can correctly
# resolve `<script src="app.js"></script>` and `<link href="style.css">`
app.mount(
    "/",
    StaticFiles(directory=str(settings.frontend_dir)),
    name="static"
)