# Database Schema Documentation

## Overview

The MnM Dashboard uses a PostgreSQL database hosted on Neon (eu-central-1, PostgreSQL 17) to persist team data for a five-player League of Legends team. The schema supports session tracking, champion management, draft strategy, and performance statistics.

**Database Connection:**
- Host: Neon PostgreSQL (eu-central-1)
- Driver: asyncpg (async SQLAlchemy)
- Connection format: `postgresql+asyncpg://user:pass@host/db?ssl=require`

**Players:**
- Alex
- Hans
- Elias
- Mikkel
- Sinus

---

## Table Schemas

### 1. session_reviews

**Purpose:** Stores the team's current session review notes (singleton table - only 1 active row).

**Fields:**
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO INCREMENT | Unique identifier |
| notes | Text | NOT NULL, DEFAULT '' | Session review content |
| last_updated | DateTime(TZ) | AUTO UPDATE | Timestamp of last modification |
| created_at | DateTime(TZ) | AUTO SET | Timestamp of creation |

**Indexes:**
- Primary key on `id`

**Usage Pattern:**
- Single row maintained via upsert (update if exists, create if not)
- Notes updated via PUT endpoint
- Frontend displays current notes in read/write textarea

**CRUD Operations:**
- `get_session_review()` - Fetch current notes
- `update_session_review(notes)` - Update or create notes

**Related Tables:**
- `session_review_archives` - Historical versions

---

### 2. weekly_champions

**Purpose:** Tracks which champions each player practiced during a specific week (Monday-Sunday).

**Fields:**
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO INCREMENT | Unique identifier |
| player_name | String(255) | NOT NULL | Player name (Alex/Hans/Elias/Mikkel/Sinus) |
| champion_name | String(255) | NOT NULL | League of Legends champion name |
| played | Boolean | DEFAULT FALSE | Whether the champion was played this week |
| week_start_date | Date | NOT NULL, INDEX | Monday of the week |
| created_at | DateTime(TZ) | AUTO SET | Timestamp of creation |
| archived_at | DateTime(TZ) | NULLABLE, INDEX | Timestamp when archived (NULL = active) |

**Indexes:**
- Primary key on `id`
- Index on `week_start_date`
- Index on `archived_at`
- Composite index on `(week_start_date, player_name, champion_name, archived_at)`

**Usage Pattern:**
- Multiple rows per player/champion/week combination allowed (to track multiple games)
- `played=TRUE` indicates a game was played on this champion
- `played=FALSE` rows serve as templates/checklist entries
- Current week rows have `archived_at=NULL`
- Historical weeks have `archived_at` timestamp and are excluded from active queries

**Week Lifecycle:**
1. **Week Start:** Champions copied from previous week with `played=FALSE`
2. **During Week:** Games marked by creating/updating rows with `played=TRUE`
3. **Week End:** Archive process aggregates play counts, marks rows as archived, recreates for next week

**CRUD Operations:**
- `get_weekly_champions(week_start)` - Fetch week's champions (excludes archived if current week)
- `upsert_weekly_champion(data)` - Create new or update existing
- `delete_weekly_champion(player, champion, week_start)` - Delete all instances
- `delete_one_weekly_champion_instance(player, champion, week_start, played)` - Delete single instance

**Related Tables:**
- `weekly_champion_archives` - Aggregated weekly statistics
- `champion_pools` - Source of truth for each player's champion roster

---

### 3. draft_notes

**Purpose:** Stores the team's current draft strategy notes (singleton table - only 1 active row).

**Fields:**
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO INCREMENT | Unique identifier |
| notes | Text | NOT NULL, DEFAULT '' | Draft strategy content |
| last_updated | DateTime(TZ) | AUTO UPDATE | Timestamp of last modification |
| created_at | DateTime(TZ) | AUTO SET | Timestamp of creation |

**Indexes:**
- Primary key on `id`

**Usage Pattern:**
- Single row maintained via upsert
- Notes updated via PUT endpoint
- Frontend displays current notes in read/write textarea

**CRUD Operations:**
- `get_draft_note()` - Fetch current notes
- `update_draft_note(notes)` - Update or create notes

**Related Tables:** None

---

### 4. pick_stats

**Purpose:** Tracks first-pick performance statistics for champions with win/loss records.

**Fields:**
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO INCREMENT | Unique identifier |
| champion_name | String(255) | UNIQUE, NOT NULL, INDEX | League of Legends champion name |
| first_pick_games | Integer | DEFAULT 0 | Total games first-picked |
| first_pick_wins | Integer | DEFAULT 0 | Games won when first-picked |
| created_at | DateTime(TZ) | AUTO SET | Timestamp of creation |
| updated_at | DateTime(TZ) | AUTO UPDATE | Timestamp of last modification |

**Computed Fields (not stored):**
- `win_rate` (Float) - Calculated as `(first_pick_wins / first_pick_games) * 100` if games > 0, else 0.0

**Indexes:**
- Primary key on `id`
- Unique index on `champion_name`

**Usage Pattern:**
- One row per champion (enforced by UNIQUE constraint)
- Frontend displays sorted by `win_rate` (descending)
- Win/loss buttons increment counters via PATCH endpoints

**CRUD Operations:**
- `get_pick_stats()` - Fetch all stats with computed win_rate
- `create_pick_stat(champion_data)` - Add new champion
- `add_win(stat_id)` - Increment both games and wins (+1/+1)
- `add_loss(stat_id)` - Increment only games (+1/+0)
- `delete_pick_stat(stat_id)` - Remove champion
- `update_pick_stat_champion(stat_id, new_name)` - Rename champion (checks uniqueness)

**Related Tables:** None

---

### 5. session_review_archives

**Purpose:** Historical storage for past session reviews.

**Fields:**
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO INCREMENT | Unique identifier |
| title | String(255) | NOT NULL | Descriptive title for archived session |
| notes | Text | NOT NULL, DEFAULT '' | Session review content |
| archived_at | DateTime(TZ) | AUTO SET | Timestamp when archived |
| original_date | Date | NULLABLE | Original date of session (if applicable) |

**Indexes:**
- Primary key on `id`

**Usage Pattern:**
- Archives created manually or automatically
- Ordered by `archived_at DESC` for display
- Supports future feature: browsing historical session reviews

**CRUD Operations:**
- `create_session_review_archive(title, notes, original_date)` - Create archive entry
- `get_session_review_archives()` - Fetch all archives (newest first)
- `get_session_review_archive_by_id(archive_id)` - Fetch single archive
- `update_session_review_archive(archive_id, title, notes)` - Update archive

**Related Tables:**
- `session_reviews` - Source of current notes

---

### 6. weekly_champion_archives

**Purpose:** Aggregated historical statistics for weekly champion practice (for future graphs/analytics).

**Fields:**
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO INCREMENT | Unique identifier |
| player_name | String(255) | NOT NULL, INDEX | Player name |
| champion_name | String(255) | NOT NULL | Champion name |
| times_played | Integer | DEFAULT 0 | Number of games played this week |
| week_start_date | Date | NOT NULL, INDEX | Monday of the week |
| week_end_date | Date | NOT NULL | Sunday of the week |
| archived_at | DateTime(TZ) | AUTO SET | Timestamp when archived |

**Indexes:**
- Primary key on `id`
- Index on `player_name`
- Index on `week_start_date`

**Usage Pattern:**
- Created during weekly archive process
- Aggregates play counts per player/champion combination
- One row per player/champion/week with total play count
- Used for future analytics and historical trend graphs

**Archive Process:**
1. Query all `weekly_champions` for target week
2. Group by (player_name, champion_name) and count `played=TRUE`
3. Create archive records with aggregated counts
4. Mark source `weekly_champions` rows with `archived_at` timestamp
5. Recreate champion entries for next week with `played=FALSE`

**CRUD Operations:**
- `archive_weekly_champions(week_start)` - Archive week and create aggregated records
- `get_weekly_champion_archives(player_name?)` - Fetch archives (optional player filter)

**Related Tables:**
- `weekly_champions` - Source data for archiving

---

### 7. champion_pools

**Purpose:** Defines each player's champion roster with strategic notes.

**Fields:**
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO INCREMENT | Unique identifier |
| player_name | String(255) | NOT NULL, INDEX | Player name (Alex/Hans/Elias/Mikkel/Sinus) |
| champion_name | String(255) | NOT NULL | League of Legends champion name |
| description | Text | NOT NULL, DEFAULT '' | When/why to pick this champion |
| pick_priority | Text | NOT NULL, DEFAULT '' | Pick strategy notes (early/late, flex, etc.) |
| created_at | DateTime(TZ) | AUTO SET | Timestamp of creation |
| updated_at | DateTime(TZ) | AUTO UPDATE | Timestamp of last modification |

**Indexes:**
- Primary key on `id`
- Index on `player_name`

**Usage Pattern:**
- Multiple rows per player (one per champion in their pool)
- No UNIQUE constraint - players can have duplicate champions if needed
- Used as source of truth for weekly champion generation
- Displayed on Champion Pool page with filters per player

**CRUD Operations:**
- `get_champion_pools(player_name?)` - Fetch all pools (optional player filter)
- `create_champion_pool(pool_data)` - Add new champion to player's pool
- `update_champion_pool(pool_id, pool_data)` - Update champion notes
- `delete_champion_pool(pool_id)` - Remove champion from pool

**Related Tables:**
- `weekly_champions` - Weekly practice tracking
- Accountability check relies on this table to determine expected champions

---

### 8. weekly_messages

**Purpose:** Stores a shared weekly message displayed to all users (singleton table - only 1 active row).

**Fields:**
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | Integer | PRIMARY KEY, AUTO INCREMENT | Unique identifier (always 1) |
| message | Text | NOT NULL, DEFAULT '' | Weekly message content |
| last_updated | DateTime(TZ) | AUTO UPDATE | Timestamp of last modification |
| created_at | DateTime(TZ) | AUTO SET | Timestamp of creation |

**Indexes:**
- Primary key on `id`

**Usage Pattern:**
- Single row with `id=1` (enforced in CRUD operations)
- Auto-created if doesn't exist
- Updated via dedicated endpoint
- Displayed prominently on homepage

**CRUD Operations:**
- `get_weekly_message()` - Fetch current message (creates if missing)
- `update_weekly_message(message)` - Update message content

**Related Tables:** None

---

## Data Relationships

### Champion Pool → Weekly Champions
```
champion_pools (source of truth)
    ↓
weekly_champions (weekly tracking)
    ↓
weekly_champion_archives (historical aggregates)
```

**Flow:**
1. Players define their champion pool in `champion_pools`
2. Each week, champions are copied to `weekly_champions` with `played=FALSE`
3. As games are played, `played=TRUE` entries are created
4. At week end, data is aggregated into `weekly_champion_archives`
5. Active `weekly_champions` rows are marked with `archived_at` timestamp
6. New week starts with fresh `played=FALSE` entries

### Session Reviews
```
session_reviews (current active)
    ↓ (manual archive)
session_review_archives (historical versions)
```

---

## Computed Fields & Logic

### Win Rate (pick_stats)
```python
if first_pick_games > 0:
    win_rate = round((first_pick_wins / first_pick_games) * 100, 1)
else:
    win_rate = 0.0
```
- Computed in backend CRUD layer
- NOT stored in database
- Returned in API responses

### Week Start Date Calculation
```python
def _get_week_start(target_date: Optional[date] = None) -> date:
    """Return the Monday of the target date's week."""
    if target_date is None:
        target_date = datetime.now().date()
    return target_date - timedelta(days=target_date.weekday())
```
- Used throughout application
- Ensures consistent week boundaries (Monday = day 0)

### Accountability Check Logic
**Purpose:** Verify each player has played ≥1 game on ALL their champions this week.

**Algorithm:**
```python
FOR each player in [Alex, Hans, Elias, Mikkel, Sinus]:
    champions = SELECT * FROM champion_pools WHERE player_name = player

    IF champions is empty:
        RETURN {
            player_name: player,
            all_champions_played: False,
            total_champions: 0,
            champions_played: 0,
            missing_champions: []
        }

    FOR each champion in champions:
        games = SELECT * FROM weekly_champions WHERE
            player_name = player AND
            champion_name = champion.champion_name AND
            week_start_date = current_week_start AND
            played = TRUE AND
            archived_at IS NULL

        IF games.count > 0:
            champions_played += 1
        ELSE:
            missing_champions.append(champion.champion_name)

    all_champions_played = (missing_champions.count == 0)
```

**Key Points:**
- **Always returns all 5 players** (even if no champion pool data)
- Checks `weekly_champions` table for current week
- Only counts `played=TRUE` entries
- Excludes archived rows (`archived_at IS NULL`)
- Provides detailed breakdown per champion

---

## Performance Considerations

### Indexes

**weekly_champions:**
- Composite index on `(week_start_date, player_name, champion_name, archived_at)` - Optimizes weekly queries with player/champion filters
- Index on `week_start_date` - Fast week-based filtering
- Index on `archived_at` - Efficient active vs. archived separation

**champion_pools:**
- Index on `player_name` - Fast player-based filtering

**pick_stats:**
- Unique index on `champion_name` - Enforces constraint and fast lookups

**weekly_champion_archives:**
- Index on `player_name` - Fast player-based historical queries
- Index on `week_start_date` - Efficient time-range queries

### Query Patterns

**Most Frequent Queries:**
1. `SELECT * FROM weekly_champions WHERE week_start_date = ? AND archived_at IS NULL` - Used on homepage
2. `SELECT * FROM champion_pools WHERE player_name = ?` - Used on Champion Pool page and accountability check
3. `SELECT * FROM pick_stats ORDER BY win_rate DESC` - Used on Pick Stats page

**Optimization Strategies:**
- Async SQLAlchemy with asyncpg for connection pooling
- Composite indexes cover common WHERE clauses
- Singleton tables (session_reviews, draft_notes, weekly_messages) have constant-time access
- Archive process uses bulk operations with single commit

---

## Data Lifecycle

### Weekly Champion Workflow

```
Week N Start (Monday)
├─ Champions exist from Week N-1 with played=FALSE
├─ Players mark champions as played (creates played=TRUE entries)
└─ Week N End (Sunday)
    ├─ Archive process runs
    ├─ Aggregate play counts
    ├─ Create weekly_champion_archives records
    ├─ Mark all Week N rows with archived_at timestamp
    └─ Create Week N+1 entries with played=FALSE
```

### Archive Process Details

**Trigger:** Manual or scheduled (currently manual)

**Steps:**
1. **Query:** Fetch all `weekly_champions` for target week where `archived_at IS NULL`
2. **Aggregate:** Group by (player, champion) and count `played=TRUE`
3. **Archive:** Create `weekly_champion_archives` records with aggregated counts
4. **Mark:** Update all source rows with `archived_at = NOW()`
5. **Recreate:** Insert new `weekly_champions` rows for next week with `played=FALSE`
6. **Commit:** Single transaction ensures consistency

**Preservation:**
- Original `weekly_champions` rows are NEVER deleted
- Historical data remains queryable via `archived_at` filter
- Aggregated stats stored separately for performance

---

## Common Operations

### Add a New Champion to Player Pool
```sql
INSERT INTO champion_pools (player_name, champion_name, description, pick_priority)
VALUES ('Sinus', 'Ahri', 'Safe blind pick, good waveclear', 'Early pick priority');
```

### Mark Champion as Played This Week
```python
# Creates a new played=TRUE entry for current week
await upsert_weekly_champion(
    db,
    WeeklyChampionCreate(
        player_name='Sinus',
        champion_name='Ahri',
        played=True,
        week_start_date=get_week_start()
    )
)
```

### Record a First-Pick Win
```sql
UPDATE pick_stats
SET first_pick_games = first_pick_games + 1,
    first_pick_wins = first_pick_wins + 1,
    updated_at = NOW()
WHERE champion_name = 'Ahri';
```

### Archive Last Week
```python
# Calculate last Monday
last_week_start = get_week_start() - timedelta(days=7)

# Run archive process
archives = await archive_weekly_champions(db, last_week_start)
```

### Check Accountability for Current Week
```python
accountability_data = await get_accountability_check(db)

# Returns list of dicts for all 5 players:
# [
#   {
#     "player_name": "Sinus",
#     "all_champions_played": True,
#     "missing_champions": [],
#     "total_champions": 5,
#     "champions_played": 5,
#     "champion_details": [...]
#   },
#   ...
# ]
```

---

## Database Initialization

**Script:** `backend/init_db.py`

**Process:**
1. Drop all tables (if `--drop` flag provided)
2. Create all tables via SQLAlchemy metadata
3. Seed singleton tables:
   - `session_reviews` - Empty notes
   - `draft_notes` - Empty notes
   - `weekly_messages` - Empty message

**Usage:**
```powershell
cd backend
python init_db.py  # Create tables and seed
python init_db.py --drop  # Drop and recreate
```

---

## Migration Strategy

**Current State:** No migration framework (Alembic not configured)

**Schema Changes:**
1. Modify `backend/app/models.py`
2. Update corresponding Pydantic schemas in `backend/app/schemas.py`
3. Use Neon MCP tools for safe migrations:
   - `prepare_database_migration` - Test on temporary branch
   - `complete_database_migration` - Apply to main branch
4. Update CRUD operations in `backend/app/crud.py`
5. Update API routers if endpoint contracts change

**Best Practice:**
- Use Neon branching for testing schema changes
- Always backup production data before migrations
- Test migrations on temporary branch first
- Use zero-downtime migration techniques (see CLAUDE.md)

---

## Backup & Recovery

**Neon Features:**
- Automated backups (Neon handles this)
- Point-in-time restore available
- Branching for safe testing

**Manual Test Backup:**
- Test archive system for `champion_pools` table
- See `TEST-ARCHIVE-README.md` for details
- PowerShell scripts: `test-archive.ps1`, `test-restore.ps1`
- SQL scripts: `test-archive-champions.sql`, `test-restore-champions.sql`

---

## Security Considerations

### Connection Security
- TLS required: `ssl=require` in connection string
- Environment variable for `DATABASE_URL` (not committed to git)
- Separate `.env.example` files for reference

### SQL Injection Prevention
- SQLAlchemy ORM with parameterized queries
- Pydantic validation on all inputs
- No raw SQL except in specific CRUD operations (still parameterized)

### Data Privacy
- No sensitive personal data stored
- Game statistics only
- Public deployment (no authentication required for MVP)

---

## Troubleshooting

### Common Issues

**1. Connection Errors**
```
asyncpg.exceptions.InvalidParameterValueError: channel_binding
```
**Solution:** Use `ssl=require`, NOT `sslmode=require` or `channel_binding=require`

**2. Duplicate Weekly Champions**
```
Multiple entries for same player/champion/week with played=TRUE
```
**Expected Behavior:** System allows multiple played entries to track multiple games

**3. Missing Players in Accountability Check**
```
Only 2 players shown instead of 5
```
**Fix Applied:** Accountability check now always returns all 5 players (fixed Jan 7, 2026)

**4. Win Rate Multiplication Issue**
```
Win rate shows 9500% instead of 95%
```
**Known Issue:** Frontend multiplies by 100, but backend already returns percentage (see CLAUDE.md known issues)

---

## Future Enhancements

### Planned Features
1. **Historical Graphs** - Use `weekly_champion_archives` for trend visualization
2. **Session Review History** - Browse `session_review_archives` in UI
3. **Authentication** - Add user accounts and permissions
4. **Automated Archiving** - Scheduled job to archive weekly champions
5. **Analytics Dashboard** - Player performance metrics over time
6. **Alembic Integration** - Proper database migration management

### Schema Additions
1. **users** table - For authentication
2. **roles** table - For permissions
3. **game_logs** table - Detailed match history
4. **team_stats** table - Overall team performance

---

## References

- **Backend Models:** `backend/app/models.py`
- **Pydantic Schemas:** `backend/app/schemas.py`
- **CRUD Operations:** `backend/app/crud.py`
- **Database Config:** `backend/app/database.py`
- **Project Instructions:** `CLAUDE.md`
- **API Documentation:** `backend/README.md`
- **Neon MCP Guide:** CLAUDE.md (Neon MCP Server Integration section)
