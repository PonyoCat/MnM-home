# MnM dashboard

A full-stack web application for tracking League of Legends team performance, draft notes, and statistics.
This was made for my hobby league team Meeps and Maniacs to help keep organisation and management out of discord and stored in a better and more permanent way.





## Project Overview

MnM dashboard is a small full-stack app for a five-player League of Legends team. It provides four key features:
- **Session Review Notes** - Shared notes for post-game analysis
- **Weekly Champions Checklist** - Track which champions each player has mastered each week
- **Draft Notes** - Strategic notes for draft phase
- **First Pick Statistics** - Win/loss tracking for first-pick champions

## Tech Stack

### Backend
- FastAPI (Python web framework)
- SQLAlchemy (async ORM)
- PostgreSQL via Neon (cloud database)
- asyncpg (async PostgreSQL driver)

### Frontend
- React + Vite + TypeScript
- Tailwind CSS
- Radix UI primitives
- Lucide React icons

## Prerequisites

- **Python 3.9+** (for backend)
- **Node.js 18+** (for frontend)
- **Neon PostgreSQL database** (free tier available at https://neon.tech)

## Quick Start

**Note:** This project uses PowerShell commands for Windows. If you're on Mac/Linux, use bash equivalents.

### 1. Clone the Repository

```powershell
git clone <your-repo-url>
cd MnM-home
```

### 2. Backend Setup

#### Install Python Dependencies

```powershell
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (PowerShell)
.\venv\Scripts\Activate.ps1

# If you get an execution policy error, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Install dependencies
pip install -r requirements.txt
```

#### Configure Database

1. Create a free PostgreSQL database at [Neon](https://neon.tech)
2. Copy your connection string (it should look like: `postgresql://user:password@host/dbname?sslmode=require`)
3. Create a `.env` file in the `backend/` directory:

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://your_user:your_password@your_host/your_db?sslmode=require
```

**Important:** Make sure to use `postgresql+asyncpg://` as the scheme (not just `postgresql://`).

#### Test Database Connection (Optional)

```powershell
# Make sure you're in the backend directory with venv activated
python test_connection.py
```

You should see: `SUCCESS: Connected to Neon database!`

#### Initialize Database

```powershell
# Make sure you're in the backend directory with venv activated
python init_db.py
```

This script will:
- Create all necessary tables
- Seed initial data (one session review row, one draft note row)

#### Start Backend Server

```powershell
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

You can test the API at http://localhost:8000/docs (Swagger UI)

### 3. Frontend Setup

Open a new PowerShell window:

```powershell
cd frontend

# Install dependencies
npm install

# Create environment file
# Copy .env.example to .env.local if it doesn't exist
# The default should work for local development:
# VITE_API_URL=http://localhost:8000
```

#### Start Frontend Dev Server

```powershell
npm run dev
```

The frontend will be available at http://localhost:5173

### 4. Verify Everything Works

1. Open http://localhost:5173 in your browser
2. You should see four dashboard cards
3. Try adding a session review note and clicking "Save Notes"
4. Check the Weekly Champions checklist
5. Add some first-pick statistics

## Project Structure

```
MnM-home/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── database.py        # Database connection
│   │   ├── models.py          # SQLAlchemy ORM models
│   │   ├── schemas.py         # Pydantic validation schemas
│   │   ├── crud.py            # Database operations
│   │   └── routers/           # API route handlers
│   │       ├── session_review.py
│   │       ├── weekly_champions.py
│   │       ├── draft_notes.py
│   │       └── pick_stats.py
│   ├── init_db.py             # Database initialization script
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables (create this)
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # Dashboard components
│   │   │   ├── SessionReview.tsx
│   │   │   ├── WeeklyChampions.tsx
│   │   │   ├── DraftNotes.tsx
│   │   │   ├── PickStats.tsx
│   │   │   └── ui/            # Reusable UI components
│   │   ├── lib/
│   │   │   ├── api.ts         # API client
│   │   │   └── utils.ts       # Utility functions
│   │   ├── types/
│   │   │   └── api.types.ts   # TypeScript interfaces
│   │   ├── App.tsx            # Main app layout
│   │   └── main.tsx           # React entry point
│   ├── package.json           # Node dependencies
│   └── .env.local             # Environment variables (create this)
│
└── PRPs/                       # Project planning documents
    ├── league-dashboard.md
    └── frontend-shadcn-completion.md
```

## API Endpoints

The backend exposes the following REST API endpoints:

### Session Review
- `GET /api/session-review` - Get session review notes
- `PUT /api/session-review` - Update session review notes

### Weekly Champions
- `GET /api/weekly-champions?week_start=YYYY-MM-DD` - Get champions for a week
- `POST /api/weekly-champions` - Add a completed champion for a player

### Draft Notes
- `GET /api/draft-notes` - Get draft notes
- `PUT /api/draft-notes` - Update draft notes

### Pick Statistics
- `GET /api/pick-stats` - Get all first-pick statistics (sorted by win rate)
- `POST /api/pick-stats` - Add a new champion stat
- `PATCH /api/pick-stats/{id}/win` - Increment wins for a champion
- `PATCH /api/pick-stats/{id}/loss` - Increment losses for a champion
- `DELETE /api/pick-stats/{id}` - Delete a champion stat

Full API documentation is available at http://localhost:8000/docs when the backend is running.

## Development

### Backend Development

```powershell
cd backend
.\venv\Scripts\Activate.ps1

# Run with auto-reload
uvicorn app.main:app --reload

# Run on custom port
uvicorn app.main:app --reload --port 8001
```

### Frontend Development

```powershell
cd frontend

# Development server with hot reload
npm run dev

# TypeScript type checking
npm run build

# Linting
npm run lint
```


## Additional Documentation

- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current implementation status
- **[INITIAL.md](INITIAL.md)** - Original feature request
- **[PRPs/league-dashboard.md](PRPs/league-dashboard.md)** - Full project specification
- **[backend/README.md](backend/README.md)** - Backend-specific documentation
- **[CLAUDE.md](CLAUDE.md)** - AI development instructions

## License

Private project for internal team use.
