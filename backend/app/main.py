import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import crud
from .database import AsyncSessionLocal, Base, engine
from .routers import (
    accountability,
    analytics,
    champion_pool,
    clash_dates,
    draft_notes,
    fines,
    pick_stats,
    players,
    session_review,
    week_config,
    weekly_champions,
    weekly_message,
)

logger = logging.getLogger(__name__)


# Scheduler timezone. Render runs containers in UTC by default; the sync fires every
# 30 minutes regardless of timezone. Override with SCHEDULER_TIMEZONE env var.
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "UTC")


async def _run_scheduled_sync(app: FastAPI) -> None:
    """Wrapper invoked by APScheduler every 30 minutes.

    MUST never raise -- a raised exception kills the scheduler thread silently.
    Acquires the shared sync lock; if a manual sync is already running, this scheduled
    run is skipped.
    """
    sync_lock: asyncio.Lock = app.state.sync_lock
    if sync_lock.locked():
        logger.info("Scheduled sync skipped: another sync is already in progress")
        return
    async with sync_lock:
        try:
            async with AsyncSessionLocal() as db:
                summary = await crud.sync_all_players(db, trigger="scheduled")
                logger.info(
                    "Scheduled sync complete: %d games synced (%d failed players)",
                    summary.total_games_synced,
                    len(summary.failed_players),
                )
        except Exception as exc:  # noqa: BLE001 -- scheduler must not crash
            logger.exception("Scheduled sync failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database + scheduler on startup."""
    # Sync lock used by both manual and scheduled runs.
    app.state.sync_lock = asyncio.Lock()
    app.state.scheduler = None

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"ERROR: Failed to initialize database: {e}")
        print(f"Database URL configured: {engine.url}")
        # Don't fail startup -- let the app boot so logs are visible.

    # Lazily import APScheduler so the app still boots if the package is missing.
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = AsyncIOScheduler(timezone=SCHEDULER_TIMEZONE)
        scheduler.add_job(
            _run_scheduled_sync,
            CronTrigger(minute="*/30"),
            id="sync-every-30min",
            replace_existing=True,
            kwargs={"app": app},
        )
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info(
            "Scheduler started in timezone %s (sync every 30 minutes)",
            SCHEDULER_TIMEZONE,
        )
    except ImportError:
        logger.warning("apscheduler not installed; auto-sync disabled")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to start scheduler: %s", exc)

    # Startup recovery: re-fire any full sync that was interrupted by a restart.
    try:
        async with AsyncSessionLocal() as db:
            stuck = await crud.get_running_full_sync(db)
            if stuck is not None:
                logger.warning(
                    "Found interrupted full sync run_id=%s on startup -- resuming",
                    stuck.run_id,
                )
                asyncio.create_task(
                    players._run_full_sync_background(app, stuck.run_id)
                )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Startup recovery check failed: %s", exc)

    yield

    # Shutdown.
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler is not None:
        try:
            scheduler.shutdown(wait=False)
        except Exception:  # noqa: BLE001
            pass


app = FastAPI(
    title="MnM Dashboard API",
    description="Backend API for League of Legends team dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server (local development)
        "http://127.0.0.1:5173",  # Vite dev server (local development)
        "https://mnm-home.onrender.com",  # Render backend (for testing via browser)
        "*",  # Allow all origins temporarily for testing - REPLACE with actual frontend URL when deployed
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(session_review.router)
app.include_router(weekly_champions.router)
app.include_router(draft_notes.router)
app.include_router(pick_stats.router)
app.include_router(champion_pool.router)
app.include_router(weekly_message.router)
app.include_router(accountability.router)
app.include_router(analytics.router)
app.include_router(fines.router)
app.include_router(clash_dates.router)
app.include_router(week_config.router)
app.include_router(players.router)


@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    """Health check endpoint - supports both GET and HEAD for monitoring services"""
    return {"message": "MnM Dashboard API", "status": "running", "version": "1.0.0"}
