from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import session_review, weekly_champions, draft_notes, pick_stats, champion_pool
from contextlib import asynccontextmanager
from .database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    try:
        # Create all tables on startup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables initialized successfully")
    except Exception as e:
        print(f"ERROR: Failed to initialize database: {e}")
        print(f"Database URL configured: {engine.url}")
        # Don't fail startup - let the app start even if DB init fails
        # This allows you to see error logs
    yield
    # Cleanup on shutdown (if needed)

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

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "MnM Dashboard API", "status": "running", "version": "1.0.0"}
