# MnM Dashboard Backend

Python FastAPI backend for the League of Legends team dashboard.

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database

1. Create a free PostgreSQL database at [Neon](https://neon.tech)
2. Copy the connection string
3. Create `.env` file in the `backend/` directory:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database?sslmode=require
```

### 5. Initialize Database

```bash
python init_db.py
```

### 6. Run Development Server

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI (Interactive Docs): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Session Review
- `GET /api/session-review` - Get session notes
- `PUT /api/session-review` - Update session notes

### Weekly Champions
- `GET /api/weekly-champions?week_start=YYYY-MM-DD` - Get champions for week
- `POST /api/weekly-champions` - Update champion played status

### Draft Notes
- `GET /api/draft-notes` - Get draft notes
- `PUT /api/draft-notes` - Update draft notes

### Pick Stats
- `GET /api/pick-stats` - Get all pick statistics
- `POST /api/pick-stats` - Add new champion to track
- `PATCH /api/pick-stats/{id}/win` - Record a win
- `PATCH /api/pick-stats/{id}/loss` - Record a loss
- `DELETE /api/pick-stats/{id}` - Delete champion stats

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── database.py      # Database connection
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic schemas
│   ├── crud.py          # Database operations
│   └── routers/         # API endpoints
│       ├── session_review.py
│       ├── weekly_champions.py
│       ├── draft_notes.py
│       └── pick_stats.py
├── init_db.py          # Database initialization script
├── requirements.txt    # Python dependencies
└── .env               # Environment variables (not in git)
```

## Deployment

See main README.md for deployment instructions to Render.
