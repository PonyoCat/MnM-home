from datetime import date
from io import BytesIO
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, database
from ..services.charting import (
    PLAYERS,
    build_chart_json_data,
    build_games_dataframe,
    get_data_date_bounds,
    render_bar_chart,
    render_line_chart,
    render_pie_chart,
)

router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"]
)


def _parse_iso_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}. Expected YYYY-MM-DD.") from exc


def _parse_top_n(value: Optional[str], default: int) -> int:
    if value is None or value == "":
        return default
    try:
        top_n = int(value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="top_n must be a positive integer.") from exc

    if top_n <= 0:
        raise HTTPException(status_code=400, detail="top_n must be a positive integer.")
    return top_n


def _validate_mode(mode: Optional[str]) -> str:
    if not mode:
        raise HTTPException(status_code=400, detail="mode is required.")

    normalized = mode.strip().lower()
    if normalized not in {"all", "player"}:
        raise HTTPException(status_code=400, detail="mode must be 'all' or 'player'.")
    return normalized


def _validate_player(player_name: Optional[str], required: bool = False) -> Optional[str]:
    if not player_name:
        if required:
            raise HTTPException(status_code=400, detail="player_name is required for this mode.")
        return None

    normalized = player_name.strip()
    if normalized not in PLAYERS:
        raise HTTPException(status_code=400, detail=f"player_name must be one of: {', '.join(PLAYERS)}.")
    return normalized


def _parse_date_range(start_date: Optional[str], end_date: Optional[str]) -> tuple[date, date]:
    if not start_date or not end_date:
        raise HTTPException(status_code=400, detail="start_date and end_date are required.")

    parsed_start = _parse_iso_date(start_date, "start_date")
    parsed_end = _parse_iso_date(end_date, "end_date")

    if parsed_start > parsed_end:
        raise HTTPException(status_code=400, detail="start_date cannot be after end_date.")

    return parsed_start, parsed_end


@router.get("/weekly-trends")
async def get_weekly_trends(
    start_date: date,
    end_date: date,
    player_name: Optional[str] = None,
    db: AsyncSession = Depends(database.get_db)
):
    """Get aggregated weekly data for trends"""
    return await crud.get_weekly_trends(db, start_date, end_date, player_name)

@router.get("/practice-vs-winrate")
async def get_practice_vs_winrate(
    db: AsyncSession = Depends(database.get_db)
):
    """Get practice volume vs win rate data"""
    return await crud.get_practice_vs_winrate_data(db)

@router.get("/pool-coverage")
async def get_pool_coverage(
    week_start: date,
    db: AsyncSession = Depends(database.get_db)
):
    """Get champion pool coverage stats for a specific week"""
    return await crud.get_pool_coverage(db, week_start)


@router.get("/charts/date-bounds")
async def get_chart_date_bounds(
    db: AsyncSession = Depends(database.get_db),
):
    try:
        earliest, latest = await get_data_date_bounds(db)
        return {
            "earliest_date": earliest.isoformat() if earliest else None,
            "latest_date": latest.isoformat() if latest else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to get chart date bounds.") from exc


@router.get("/charts/json-data")
async def get_chart_json_data(
    mode: Optional[str] = Query(None, description="all or player"),
    player_name: Optional[str] = Query(None, description="Player for player mode and pie chart"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(database.get_db),
):
    """Return all chart data as JSON for interactive frontend charts."""
    try:
        parsed_mode = _validate_mode(mode)
        parsed_player = _validate_player(player_name, required=parsed_mode == "player")
        parsed_start, parsed_end = _parse_date_range(start_date, end_date)

        df = await build_games_dataframe(
            db=db,
            start_date=parsed_start,
            end_date=parsed_end,
            player_name=parsed_player if parsed_mode == "player" else None,
        )
        return build_chart_json_data(df, parsed_mode, parsed_player)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to generate chart data.") from exc


@router.get("/charts/bar")
async def get_bar_chart(
    mode: Optional[str] = Query(None, description="all or player"),
    player_name: Optional[str] = Query(None, description="Required when mode=player"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    top_n: Optional[str] = Query(None, description="Top champions to show. Default 10"),
    db: AsyncSession = Depends(database.get_db),
):
    try:
        parsed_mode = _validate_mode(mode)
        parsed_player = _validate_player(player_name, required=parsed_mode == "player")
        parsed_start, parsed_end = _parse_date_range(start_date, end_date)
        parsed_top_n = _parse_top_n(top_n, default=10)

        df = await build_games_dataframe(
            db=db,
            start_date=parsed_start,
            end_date=parsed_end,
            player_name=parsed_player if parsed_mode == "player" else None,
        )
        image_bytes = render_bar_chart(df, parsed_mode, parsed_player, parsed_top_n)
        return StreamingResponse(BytesIO(image_bytes), media_type="image/png")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to generate bar chart.") from exc


@router.get("/charts/pie")
async def get_pie_chart(
    player_name: Optional[str] = Query(None, description="Player name"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    top_n: Optional[str] = Query(None, description="Top champions to show. Default 8"),
    db: AsyncSession = Depends(database.get_db),
):
    try:
        parsed_player = _validate_player(player_name, required=True)
        parsed_start, parsed_end = _parse_date_range(start_date, end_date)
        parsed_top_n = _parse_top_n(top_n, default=8)

        df = await build_games_dataframe(
            db=db,
            start_date=parsed_start,
            end_date=parsed_end,
            player_name=parsed_player,
        )
        image_bytes = render_pie_chart(df, parsed_player, parsed_top_n)
        return StreamingResponse(BytesIO(image_bytes), media_type="image/png")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to generate pie chart.") from exc


@router.get("/charts/line")
async def get_line_chart(
    mode: Optional[str] = Query(None, description="all or player"),
    player_name: Optional[str] = Query(None, description="Required when mode=player"),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    top_n: Optional[str] = Query(None, description="Top champions to show. Default 8"),
    db: AsyncSession = Depends(database.get_db),
):
    try:
        parsed_mode = _validate_mode(mode)
        parsed_player = _validate_player(player_name, required=parsed_mode == "player")
        parsed_start, parsed_end = _parse_date_range(start_date, end_date)
        parsed_top_n = _parse_top_n(top_n, default=8)

        df = await build_games_dataframe(
            db=db,
            start_date=parsed_start,
            end_date=parsed_end,
            player_name=parsed_player if parsed_mode == "player" else None,
        )
        image_bytes = render_line_chart(
            df=df,
            mode=parsed_mode,
            player_name=parsed_player,
            top_n=parsed_top_n,
            start_date=parsed_start,
            end_date=parsed_end,
        )
        return StreamingResponse(BytesIO(image_bytes), media_type="image/png")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to generate line chart.") from exc
