from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import session_review, weekly_champions, draft_notes, pick_stats, champion_pool

app = FastAPI(
    title="MnM Dashboard API",
    description="Backend API for League of Legends team dashboard",
    version="1.0.0",
)

# CORS middleware - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server (local development)
        "http://127.0.0.1:5173",  # Vite dev server (local development)
        # "https://your-app-name.vercel.app",  # TODO: Replace with your actual Vercel domain after deployment
        # "https://your-custom-domain.com",    # Optional: Add custom domain if configured
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
