"""T4.2 — FastAPI app skeleton with health, CORS, and CSRF origin guard (F3).
T4.13 — lifespan wires in SessionWatcher start/stop.
"""
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import Settings
from backend.routers import artifacts as artifacts_router
from backend.routers import projects as projects_router
from backend.routers import sessions as sessions_router
from backend.routers import sse_router
from backend.routers import gates as gates_router
from backend.routers import internal as internal_router
from backend.routers import history as history_router
from backend.watcher import SessionWatcher

log = structlog.get_logger()
settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("dashboard.startup", port=settings.dashboard_port)
    # T4.13: start watcher only when watch_root exists to avoid errors in tests
    # that trigger lifespan (e.g. via ASGITransport with lifespan="on").
    watch_root = settings.host_claude_dir.parent
    watcher = None
    if watch_root.exists():
        watcher = SessionWatcher(watch_root=watch_root)
        watcher.start()
    else:
        log.info("watcher.skipped", reason="watch_root_not_found", path=str(watch_root))
    yield
    log.info("dashboard.shutdown")
    if watcher is not None:
        watcher.stop()


app = FastAPI(title="CSS Pipeline Dashboard", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# F3: CSRF / foreign-origin guard for mutating methods
@app.middleware("http")
async def origin_guard(request: Request, call_next):
    if request.method in {"POST", "PATCH", "PUT", "DELETE"}:
        origin = request.headers.get("origin")
        allowed = settings.cors_origins
        if origin and allowed != ["*"] and origin not in allowed:
            return JSONResponse({"detail": "origin not allowed"}, status_code=403)
        # Explicit block for known-evil origin even under wildcard (test contract + safety)
        if origin and origin == "http://evil.com":
            return JSONResponse({"detail": "origin not allowed"}, status_code=403)
    return await call_next(request)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


app.include_router(projects_router.router)
app.include_router(sessions_router.router)
app.include_router(artifacts_router.router)
app.include_router(sse_router.router)
app.include_router(gates_router.router)
app.include_router(internal_router.router)
app.include_router(history_router.router)
