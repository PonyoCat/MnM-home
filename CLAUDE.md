## SECTION 1: CLAUDE CODE INSTRUCTIONS

### Read This First

**IMPORTANT:** If `.claude/project_context.md` exists, read it first for current state and known issues. It is not present in this repo right now.

**Primary Documentation (current repo):**
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Current implementation status and next steps
- **[INITIAL.md](INITIAL.md)** - Original feature request and goals
- **[PRPs/league-dashboard.md](PRPs/league-dashboard.md)** - Full spec, implementation blueprint, and validation steps
- **[PRPs/frontend-shadcn-completion.md](PRPs/frontend-shadcn-completion.md)** - Frontend completion guide
- **[PRPs/ui-enhancements.md](PRPs/ui-enhancements.md)** - Multi-page navigation, dark mode toggle, and archive fix
- **[backend/README.md](backend/README.md)** - Backend setup and API summary
- **[COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md)** - High-level completion notes

**Specialized Documentation:**
- **[PRPs/templates/prp_base.md](PRPs/templates/prp_base.md)** - PRP template
- **[.claude/commands/execute-prp.md](.claude/commands/execute-prp.md)** - PRP execution command
- **[.claude/commands/generate-prp.md](.claude/commands/generate-prp.md)** - PRP generation command



---

### How to work with this codebase

#### Development Workflow

**Environment:**
- **Operating System**: Windows 11
- **Shell**: PowerShell (use PowerShell commands, NOT bash)
- **Python**: 3.13
- **Node.js**: 18+

**Before Making Changes:**
1. Read `PROJECT_STATUS.md` and `INITIAL.md` for current state and goals
2. Review `PRPs/league-dashboard.md` for architecture, API contracts, and remaining tasks
3. Check `backend/README.md` for backend setup and environment requirements

**For Specific Tasks:**
- **Architecture questions**: `PRPs/league-dashboard.md`, `PROJECT_STATUS.md`
- **Backend setup**: `backend/README.md`, `backend/.env.example`
- **Frontend setup**: `frontend/README.md`, `frontend/.env.example`
- **PRP execution**: `.claude/commands/execute-prp.md`
- **PRP generation**: `.claude/commands/generate-prp.md`

#### Development Standards & Best Practices
 
**From User's Global Instructions (MUST FOLLOW):**
- **Minimize new files**: Always add changes to existing files - minimize creating new temporary files or scripts
- **No emoji in code**: Never use emoji characters when generating documents or code
- **Update CLAUDE.md**: Record significant findings or progress here
- **Clean project structure**: If making a temporary file or script, remove it after use - maintain clean structured projects
- **Document learnings**: Update `PROJECT_STATUS.md` or `COMPLETION_SUMMARY.md` when fixes change status or behavior
- **Move PRPs to implemented, after run**: After successfully implementing a PRP, move it to subfolder implemented.
 
**Project Awareness & Context**
- **Before starting work**: Read `PROJECT_STATUS.md` and `INITIAL.md` for state and goals, then `PRPs/league-dashboard.md` for the full spec
- **Understanding system state**: Backend and frontend are implemented; database config and deployment are pending (see `PROJECT_STATUS.md`)
- **Verify first, code second**: Confirm file paths, imports, and env vars before changes

**Code Structure & Modularity**
- **Backend layout**: `backend/app` holds the FastAPI app, models, schemas, CRUD, and routers
- **Frontend layout**: `frontend/src` holds App, components, UI primitives, and the API client
- **Imports**: Use relative imports inside the backend package; use `@/` alias in the frontend

**Testing & Reliability**
- **Automated tests**: None in the repo currently
- **Manual validation**: Use FastAPI `/docs` and the frontend UI; use `npm run build` for a TypeScript check
- **Database checks**: Run `python test_connection.py` to verify Neon connection, then `python init_db.py` after setting `DATABASE_URL`
- **PowerShell commands**: Use `.\venv\Scripts\Activate.ps1` to activate virtual environment

**Task Completion & Tracking**
- **Documentation updates**: Update `PROJECT_STATUS.md` when status changes; update PRPs when scope shifts
- **Definition of done**: Backend and frontend run locally, endpoints respond, and data persists

**Style & Conventions**
- **Python**: Follow PEP 8, use type hints, descriptive variable names (Danish terms OK: sagsnummer, planloesning, koekken_alrum)
- **FastAPI**: Use Pydantic models for validation, write docstrings, leverage dependency injection, handle CORS properly
- **Pydantic**: Be explicit about required/optional fields, use Field() for metadata, avoid default=False for required booleans, use Literal for choice fields
- **Naming conventions**: snake_case for files/functions, PascalCase for classes, UPPER_SNAKE_CASE for constants
- **Docstrings**: Use Google style for all functions/classes
- **Format**: Use black for code formatting (optional but recommended)
 
**AI Behavior Rules**
- **NEVER RUN PURGE COMMANDS UNLESS ABSOLUTELY NECESSARY. AND ALWAYS REMIND THE USER THAT THIS WILL PURGE EVERYTHING**
- **Path verification**: Always verify file paths exist before referencing them, use absolute paths in examples, handle Windows path separators correctly
- **No assumptions**: Read files before modifying, check database schema before migrations, verify API endpoints exist before documenting
- **Error handling**: Handle Danish Unicode characters (ø, æ, å, ²), add try-catch for external APIs (SharePoint, Azure OpenAI), log errors with context, fail gracefully with user-friendly messages
- **Verification steps**: Read existing code → Check dependencies → Test locally → Validate with real data (PDFs, database queries)
- **Never hallucinate**: Only reference verified Python packages, confirmed file paths, and documented API endpoints
 
#### Important Project Context

**Current System State (Updated: January 5, 2026):**
- Backend and frontend are fully implemented and deployed
- Database is configured and connected to Neon PostgreSQL (verified working)
- Deployment is COMPLETE and LIVE
- Status details are tracked in `PROJECT_STATUS.md`

**Production Deployment:**
- Backend: https://mnm-home.onrender.com (Render Free Tier)
- Frontend: https://mnm-dashboard-frontend.onrender.com (Render Static Site)
- Database: Neon PostgreSQL 17 (eu-central-1, Project: MnM)
- All API endpoints tested and working correctly

**Tech Stack:**
- FastAPI, SQLAlchemy (async), asyncpg, PostgreSQL (Neon)
- React, Vite, TypeScript, Tailwind CSS, Radix UI

**Key Features:**
- Session review notes
- Weekly champions checklist
- Draft notes
- First-pick stats with win/loss tracking

**Recent Fixes (January 5, 2026):**
- Fixed DATABASE_URL for asyncpg compatibility (removed `channel_binding` and changed `sslmode` to `ssl`)
- Correct connection string format: `postgresql+asyncpg://user:pass@host/db?ssl=require`
- See [PRPs/implemented/render-backend-database-connection-fix.md](PRPs/implemented/render-backend-database-connection-fix.md)

**Known Issues:**
- Production CORS is configured with wildcard for testing (should be tightened for production)
- `frontend/src/components/PickStats.tsx` multiplies `win_rate` by 100 although the backend already returns a percent

#### Neon MCP Server Integration

**Connection Status:**
- Neon MCP server is configured and active
- Project: MnM (round-dust-39089624)
- Database: neondb (PostgreSQL 17, eu-central-1)
- Connection string configured in `backend/.env`

**Available Capabilities:**

**Project & Organization Management:**
- List and search organizations
- List, create, describe, and delete projects
- Get connection strings for any project/branch

**Database Operations:**
- Run SQL queries and transactions
- Get table lists and describe table schemas
- Execute EXPLAIN for query analysis
- List slow queries for performance monitoring

**Schema Management:**
- Prepare and complete database migrations (safe two-step process)
- Compare schemas between branches
- Generate zero-downtime migration SQL

**Query Performance Tuning:**
- Prepare query tuning (analyze execution plans, suggest indexes)
- Complete query tuning (apply optimizations)
- Automatic index recommendations based on query patterns

**Branching & Development:**
- Create branches for development/staging
- Delete branches
- Reset branch from parent
- Describe branch contents (all objects)
- Compare database schemas between branches

**Authentication:**
- Provision Neon Auth for branch (managed auth service)

**Advanced Features:**
- Search across all resources (orgs, projects, branches)
- Fetch detailed resource information
- List branch computes (endpoints)
- Load documentation resources

**Common Workflows:**

1. **Safe Schema Changes:**
   - Use `prepare_database_migration` to test changes on temporary branch
   - Review and verify changes
   - Use `complete_database_migration` to apply to main branch

2. **Query Optimization:**
   - Use `list_slow_queries` to identify performance issues
   - Use `prepare_query_tuning` to analyze and get index suggestions
   - Test changes on temporary branch
   - Use `complete_query_tuning` to apply optimizations

3. **Development Branching:**
   - Create branch for feature development
   - Test schema changes on branch
   - Compare schemas with parent before merging
   - Reset or delete branch when done

**Best Practices:**
- Always use migration tools for schema changes (never modify main branch directly)
- Test queries on temporary branches before applying to production
- Use `compare_database_schema` before merging branches
- Leverage `explain_sql_statement` to understand query performance
- Use Neon's branching feature for development/staging environments

---
 
## SECTION 2: TECHNICAL REFERENCE

**NOTE:** Root `README.md` and `CHANGELOG.md` are not present in this repo. Use `PROJECT_STATUS.md` and the PRPs as the source of truth.

---

## Project Overview
League Dashboard is a small full-stack web app for a five-player League of Legends team. The React (Vite) frontend provides four dashboards, and the FastAPI backend persists shared data in PostgreSQL (Neon).

## Architecture
**Backend**: FastAPI app in `backend/app/main.py` with CORS enabled and feature routers mounted from `backend/app/routers/`. Database connectivity uses async SQLAlchemy in `backend/app/database.py`, with ORM models in `backend/app/models.py` and Pydantic schemas in `backend/app/schemas.py`. CRUD logic lives in `backend/app/crud.py`.

**Frontend**: Vite React app in `frontend/` using Tailwind for styling. `frontend/src/App.tsx` lays out the four feature cards. Each feature component (`SessionReview`, `WeeklyChampions`, `DraftNotes`, `PickStats`) calls the API client in `frontend/src/lib/api.ts`. Shared UI primitives live under `frontend/src/components/ui/`.

**Database**: PostgreSQL with tables created by `backend/init_db.py`, which also seeds initial session review and draft note rows.

### Core Components
- Backend API: routers, CRUD, models, and schemas under `backend/app/`
- Frontend UI: feature components and UI primitives under `frontend/src/`
- Planning docs: PRPs under `PRPs/` and status updates in `PROJECT_STATUS.md`
- CLI helpers: PRP commands under `.claude/commands/`

### Data Flow
1. User interacts with React components in `frontend/src/components/`.
2. Components call `frontend/src/lib/api.ts`, which reads `VITE_API_URL`.
3. FastAPI routers call CRUD functions using async SQLAlchemy sessions.
4. PostgreSQL persists and returns data to the client.

### Repository Tree (key files)
```text
MnM-home/
  .claude/
    commands/
      execute-prp.md
      generate-prp.md
      ultimate_validate_command.md
    settings.local.json
  backend/
    app/
      __init__.py
      main.py
      database.py
      models.py
      schemas.py
      crud.py
      routers/
        __init__.py
        session_review.py
        weekly_champions.py
        draft_notes.py
        pick_stats.py
    init_db.py
    requirements.txt
    README.md
    .env.example
  frontend/
    src/
      App.tsx
      App.css
      main.tsx
      index.css
      lib/
        api.ts
        utils.ts
      types/
        api.types.ts
      components/
        SessionReview.tsx
        WeeklyChampions.tsx
        DraftNotes.tsx
        PickStats.tsx
        ui/
          button.tsx
          card.tsx
          checkbox.tsx
          input.tsx
          textarea.tsx
          table.tsx
    public/
      vite.svg
    index.html
    package.json
    eslint.config.js
    vite.config.ts
    tailwind.config.js
    postcss.config.js
    tsconfig.json
    tsconfig.app.json
    tsconfig.node.json
    .env.example
    .env.local
  PRPs/
    league-dashboard.md
    frontend-shadcn-completion.md
    keep-alive-service.md
    templates/
      prp_base.md
    EXAMPLE_multi_agent_prp.md
  PROJECT_STATUS.md
  INITIAL.md
  COMPLETION_SUMMARY.md
  CLAUDE.md
  CLAUDE-example.md
```

## Key Commands
Use code blocks for the text.

### Setup
```bash
# Backend
cd backend
python -m venv venv
venv\Scriptsctivate  # Windows
pip install -r requirements.txt
# Set DATABASE_URL in backend/.env (see backend/.env.example)

# Frontend
cd frontend
npm install
```

### Development
```bash
# Backend
cd backend
python init_db.py
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

### Testing
```bash
# Backend API docs
# http://localhost:8000/docs

# Frontend typecheck + build
cd frontend
npm run build
```

## API Endpoints
- `GET /api/session-review`
- `PUT /api/session-review`
- `GET /api/weekly-champions?week_start=YYYY-MM-DD`
- `POST /api/weekly-champions`
- `GET /api/draft-notes`
- `PUT /api/draft-notes`
- `GET /api/pick-stats`
- `POST /api/pick-stats`
- `PATCH /api/pick-stats/{id}/win`
- `PATCH /api/pick-stats/{id}/loss`
- `DELETE /api/pick-stats/{id}`

## Important Implementation Details
- `DATABASE_URL` must use the async driver scheme (`postgresql+asyncpg://`).
- **CRITICAL for asyncpg**: Connection string must use `ssl=require` (NOT `sslmode=require` or `channel_binding=require`)
  - Correct format: `postgresql+asyncpg://user:pass@host/db?ssl=require`
  - asyncpg does NOT support `sslmode` or `channel_binding` query parameters
- `backend/init_db.py` creates tables and seeds one session review and one draft note row.
- CORS is configured in `backend/app/main.py` with wildcard for production testing.
- `WeeklyChampions.tsx` uses hardcoded player/champion lists and computes the current week start on Monday.
- `PickStats.tsx` sorts by `win_rate`; the backend already returns `win_rate` as a percent value.

## Documentation Hierarchy
```
Idea/requirements -> INITIAL.md
Plan/spec        -> PRPs/league-dashboard.md, PRPs/frontend-shadcn-completion.md
Implementation   -> backend/, frontend/
Status           -> PROJECT_STATUS.md, COMPLETION_SUMMARY.md
```

## File Organization
- `backend/` houses the FastAPI service and DB models.
- `frontend/` houses the Vite React app and UI components.
- `PRPs/` holds planning documents and templates.
- `.claude/` holds command helpers for PRP workflows.

## Environment Variables
- `backend/.env`: `DATABASE_URL` for the PostgreSQL connection string
- `frontend/.env.local`: `VITE_API_URL` for the backend base URL

---

## Additional Resources
- `PROJECT_STATUS.md` - project status and remaining tasks
- `PRPs/league-dashboard.md` - full specification and validation steps
- `PRPs/frontend-shadcn-completion.md` - focused frontend completion guide
- `backend/README.md` - backend setup guide and endpoint summary
- `COMPLETION_SUMMARY.md` - implementation notes
- `.claude/commands/execute-prp.md` - PRP execution helper
- `PRPs/templates/prp_base.md` - PRP template
