# MnM Home

League Dashboard for a five-player League of Legends team. Track session reviews, weekly champion practice, draft strategy, and first-pick statistics.

## Quick Links

- [Backend Setup](backend/README.md)
- [Detailed Database Schema](documentation/DATABASE_SCHEMA.md)
- [Project Status](PROJECT_STATUS.md)
- [Claude Instructions](CLAUDE.md)

## Tech Stack

**Backend:**
- FastAPI (Python 3.13)
- PostgreSQL 17 (Neon - eu-central-1)
- SQLAlchemy (async) + asyncpg
- Deployed on Render Free Tier

**Frontend:**
- React + Vite + TypeScript
- Tailwind CSS + Radix UI
- Deployed on Render Static Site

**Database Host:** Neon PostgreSQL (eu-central-1)

## Production URLs

- Backend API: https://mnm-home.onrender.com
- Frontend: https://mnm-dashboard-frontend.onrender.com
- API Docs: https://mnm-home.onrender.com/docs

## Database Overview

The MnM Dashboard uses 8 core tables to track team data:

### Core Tables

**Session & Strategy:**
- [session_reviews](documentation/DATABASE_SCHEMA.md#1-session_reviews) - Current team session notes (singleton)
- [draft_notes](documentation/DATABASE_SCHEMA.md#3-draft_notes) - Current draft strategy (singleton)
- [weekly_messages](documentation/DATABASE_SCHEMA.md#8-weekly_messages) - Shared weekly message (singleton)

**Champion Management:**
- [champion_pools](documentation/DATABASE_SCHEMA.md#7-champion_pools) - Each player's champion roster (source of truth)
- [weekly_champions](documentation/DATABASE_SCHEMA.md#2-weekly_champions) - Weekly practice tracking (multiple entries per champion = multiple games)
- [pick_stats](documentation/DATABASE_SCHEMA.md#4-pick_stats) - First-pick win/loss statistics

**Historical Data:**
- [session_review_archives](documentation/DATABASE_SCHEMA.md#5-session_review_archives) - Past session reviews
- [weekly_champion_archives](documentation/DATABASE_SCHEMA.md#6-weekly_champion_archives) - Aggregated weekly statistics

### Key Concepts

**Players:**
- Alex, Hans, Elias, Mikkel, Sinus

**Weekly Champion Tracking:**
1. Champions defined in `champion_pools` (one row per player/champion)
2. Each week, champions copied to `weekly_champions` with `played=FALSE`
3. As games are played, new `played=TRUE` entries are created (multiple entries = multiple games)
4. `archived_at IS NULL` means active week
5. At week end, data aggregated to `weekly_champion_archives` and original rows marked with `archived_at` timestamp

**Accountability Check:**
- Verifies each player has played ≥1 game on ALL their champions this week
- Checks `weekly_champions` for current week
- Always shows all 5 players (even if no champion pool data)
- Expandable UI shows champion-by-champion breakdown

**Archive Process:**
```
Week N End:
  1. Aggregate play counts from weekly_champions
  2. Create weekly_champion_archives records
  3. Mark weekly_champions rows with archived_at timestamp
  4. Create Week N+1 entries with played=FALSE
```

### Data Relationships

```
champion_pools (source of truth)
    ↓
weekly_champions (weekly tracking)
    ↓
weekly_champion_archives (historical aggregates)
```

**Important Notes:**
- Multiple `weekly_champions` entries for same player/champion/week are allowed (tracks multiple games)
- `played=TRUE` entries count as games played
- `played=FALSE` entries serve as checklist templates
- Archive process preserves all historical data (non-destructive)

See [documentation/DATABASE_SCHEMA.md](documentation/DATABASE_SCHEMA.md) for detailed schema, indexes, CRUD operations, and SQL examples.
