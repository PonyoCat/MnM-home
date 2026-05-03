"""Player CRUD + Riot API sync + excluded-friends endpoints."""
from __future__ import annotations

import asyncio
import logging
from datetime import date
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, schemas
from ..database import AsyncSessionLocal, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/players", tags=["players"])


def _http_error_for_riot(exc: httpx.HTTPStatusError) -> HTTPException:
    """Translate a Riot API HTTPStatusError into a user-actionable HTTPException."""
    if exc.response is not None:
        riot_status = exc.response.status_code
        if riot_status in (401, 403):
            return HTTPException(
                status_code=502,
                detail="Riot API key is invalid or expired. Update RIOT_API_KEY on the server.",
            )
        if riot_status == 404:
            return HTTPException(status_code=404, detail="Riot ID not found")
        if riot_status == 429:
            return HTTPException(
                status_code=429,
                detail="Riot API rate limit exceeded. Try again in a minute.",
            )
    return HTTPException(status_code=502, detail=f"Riot API error: {exc}")


@router.get("/last-sync", response_model=schemas.LastSync)
async def get_last_sync(db: AsyncSession = Depends(get_db)):
    """Return the timestamp of the most recent successful sync (or null)."""
    last = await crud.get_last_successful_sync(db)
    return schemas.LastSync(last_synced_at=last)


@router.post("/sync-all", response_model=schemas.SyncAllResult)
async def sync_all(
    request: Request,
    week_start: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a manual sync for every roster player with a riot_id set.

    Returns 409 if a sync is already in progress (lock held by scheduler or another click).
    """
    sync_lock = getattr(request.app.state, "sync_lock", None)
    if sync_lock is None:
        # Lock should be initialized in lifespan, but fail safe just in case.
        return await crud.sync_all_players(db, trigger="manual", week_start=week_start)

    if sync_lock.locked():
        raise HTTPException(status_code=409, detail="Sync already in progress")

    async with sync_lock:
        try:
            return await crud.sync_all_players(
                db, trigger="manual", week_start=week_start
            )
        except httpx.HTTPStatusError as exc:
            raise _http_error_for_riot(exc) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/full-sync", response_model=schemas.FullSyncStarted, status_code=202)
async def full_sync_all(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Start a full historical sync for every roster player as a background task.

    Returns immediately with a run_id (202 Accepted).  Poll
    GET /api/players/full-sync/status/{run_id} to track progress.

    Returns 409 if a full sync is already running.
    """
    # Check if any full_manual sync is currently running in the DB.
    running = await crud.get_running_full_sync(db)
    if running:
        raise HTTPException(
            status_code=409,
            detail=f"Full sync already in progress (run_id={running.run_id})",
        )

    # Create the SyncRun row immediately so we can return the run_id.
    run_id = await crud.create_full_sync_run(db)

    # Fire the sync in the background -- returns immediately to the client.
    asyncio.create_task(
        _run_full_sync_background(request.app, run_id)
    )

    return schemas.FullSyncStarted(
        run_id=run_id,
        status="running",
        message="Full sync started. Poll /api/players/full-sync/status/{run_id} for progress.",
    )


@router.get("/full-sync/status/{run_id}", response_model=schemas.FullSyncStatus)
async def full_sync_status(run_id: int, db: AsyncSession = Depends(get_db)):
    """Return the current status and progress of a full sync run."""
    status = await crud.get_full_sync_status(db, run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Sync run not found")
    return status


async def _run_full_sync_background(app: FastAPI, run_id: int) -> None:
    """Background task: runs the full sync and updates the SyncRun row."""
    sync_lock = getattr(app.state, "sync_lock", None)

    async def _do_sync() -> None:
        async with AsyncSessionLocal() as db:
            try:
                await crud.full_sync_all_players(
                    db, trigger="full_manual", run_id=run_id
                )
            except Exception as exc:
                logger.exception("Background full sync failed: %s", exc)
                await crud.mark_full_sync_run_failed(db, run_id, str(exc))

    if sync_lock is None:
        await _do_sync()
        return

    # Always wait for the lock -- never bail on locked().
    # A 30-min scheduled sync may be in-flight at startup recovery time; the
    # full sync must queue behind it, not fail permanently.
    async with sync_lock:
        await _do_sync()


@router.get("/", response_model=List[schemas.Player])
async def list_players(db: AsyncSession = Depends(get_db)):
    """Return all roster players."""
    return await crud.get_players(db)


@router.get("/{player_name}", response_model=schemas.Player)
async def get_player(player_name: str, db: AsyncSession = Depends(get_db)):
    """Return a single player by name."""
    player = await crud.get_player_by_name(db, player_name)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.patch("/{player_name}", response_model=schemas.Player)
async def patch_player(
    player_name: str,
    update_data: schemas.PlayerUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a player's riot_id or region. Clears cached PUUID if riot_id changes."""
    player = await crud.update_player(db, player_name, update_data)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.get("/{player_name}/matches", response_model=List[schemas.MatchHistory])
async def list_player_matches(
    player_name: str,
    week_start: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return match history rows for a player (optionally filtered to a single week)."""
    player = await crud.get_player_by_name(db, player_name)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return await crud.get_match_history(db, player_name=player_name, week_start=week_start)


@router.delete(
    "/{player_name}/matches/{match_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def exclude_match(
    player_name: str,
    match_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Exclude a match from weekly accountability tracking.

    Sets user_excluded=True so re-syncs do not re-add it, and removes any
    weekly_champions entry linked to this match.
    """
    removed = await crud.exclude_match(db, match_id, player_name)
    if not removed:
        raise HTTPException(status_code=404, detail="Match not found")
    return None


# --- Excluded Friends --------------------------------------------------------


@router.get(
    "/{player_name}/excluded-friends",
    response_model=List[schemas.ExcludedFriend],
)
async def list_excluded_friends(
    player_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Return the excluded-friends list for a roster player."""
    player = await crud.get_player_by_name(db, player_name)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return await crud.get_excluded_friends(db, player_name)


@router.post(
    "/{player_name}/excluded-friends",
    response_model=schemas.ExcludedFriend,
    status_code=status.HTTP_201_CREATED,
)
async def add_excluded_friend(
    player_name: str,
    body: schemas.ExcludedFriendCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add an excluded friend (PUUID resolved lazily on next sync)."""
    player = await crud.get_player_by_name(db, player_name)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    if "#" not in body.riot_id:
        raise HTTPException(
            status_code=400,
            detail="riot_id must be in 'Name#Tag' format",
        )
    try:
        return await crud.add_excluded_friend(
            db,
            player_name=player_name,
            riot_id=body.riot_id,
            region=body.region,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=409,
            detail=f"Could not add excluded friend: {exc}",
        ) from exc


@router.delete(
    "/{player_name}/excluded-friends/{friend_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_excluded_friend(
    player_name: str,
    friend_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Remove an excluded friend by id (scoped to the owning player)."""
    removed = await crud.remove_excluded_friend(db, player_name, friend_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Excluded friend not found")
    return None
