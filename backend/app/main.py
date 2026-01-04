from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import session_review, weekly_champions, draft_notes, pick_stats

app = FastAPI(
    title="League Dashboard API",
    description="Backend API for League of Legends team dashboard",
    version="1.0.0",
)

# CORS middleware - Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173",
        "https://*.vercel.app",  # Vercel production (will be updated with actual domain)
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

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "League Dashboard API", "status": "running", "version": "1.0.0"}
