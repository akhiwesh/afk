import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.core.database import init_db
from backend.app.core.seed import seed_data
from backend.app.core.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables; demo seed only when AFK_SEED_DEMO=true.
    init_db()
    seed_data()
    yield
    # Shutdown: nothing to clean up yet.

app = FastAPI(
    title="AFK Growth Platform API",
    description="Venture-grade AI Growth & Execution Platform backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    # Explicit origins from settings. Wildcard origins combined with
    # allow_credentials=True are rejected by browsers and unsafe.
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers (to be created next)
from backend.app.api.auth import router as auth_router
from backend.app.api.crm import router as crm_router
from backend.app.api.projects import router as projects_router
from backend.app.api.ai import router as ai_router
from backend.app.api.automation import router as automation_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.finance import router as finance_router
from backend.app.api.admin import router as admin_router
from backend.app.api.intelligence import router as intelligence_router
from backend.app.api.evidence import router as evidence_router
from backend.app.api.knowledge import router as knowledge_router
from backend.app.api.cases import router as cases_router

# Include API Routers under /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(intelligence_router, prefix="/api")
app.include_router(evidence_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(cases_router, prefix="/api")
app.include_router(crm_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(automation_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(finance_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

# Serve SPA static files
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
frontend_dir = os.path.join(base_dir, "frontend")

# Serve API docs or root router fallback
@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "AFK Growth Platform"}

# If frontend files exist, mount it to the root path.
# We mount static directory files, but route unknown paths to index.html to support SPA routing!
if os.path.exists(frontend_dir):
    app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")
    
    # Optional assets mount if directory exists
    assets_dir = os.path.join(frontend_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # Unknown API/docs paths are real 404s — never swallow them
        # into the SPA shell or return a bare 200/null.
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(os.path.join(frontend_dir, "index.html"))
else:
    @app.get("/")
    def root():
        return {"message": "AFK API Online. Frontend static files not found."}
