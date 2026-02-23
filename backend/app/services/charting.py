from __future__ import annotations

import logging
from datetime import date
from io import BytesIO
from itertools import cycle, islice
from typing import Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from .. import crud, models

logger = logging.getLogger(__name__)
_archive_table_available: Optional[bool] = None

PLAYERS = ["Alex", "Hans", "Elias", "Mikkel", "Sinus"]
PLAYER_COLORS = {
    "Alex": "#1d4ed8",
    "Hans": "#0f766e",
    "Elias": "#7c3aed",
    "Mikkel": "#dc2626",
    "Sinus": "#d97706",
}
PIE_COLORS = [
    "#f5c84c",
    "#5ec4ff",
    "#7ad66f",
    "#ff8f5a",
    "#aa8bff",
    "#ff6b8b",
    "#49d8c5",
    "#9db4ff",
    "#f7a8c4",
    "#d3e27a",
]
# Match UI board/card background (frontend `--card` in dark theme).
CHART_FIGURE_BG = "#071a22"
CHART_AXES_BG = "#071a22"
CHART_TEXT = "#f8fafc"
CHART_MUTED_TEXT = "#cbd5e1"
CHART_GRID = "#2b4e64"
CHART_BORDER = "#0f3f57"


def _figure_to_png_bytes(fig: plt.Figure) -> bytes:
    buffer = BytesIO()
    fig.savefig(
        buffer,
        format="png",
        bbox_inches="tight",
        pad_inches=0.2,
        dpi=120,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    plt.close(fig)
    buffer.seek(0)
    return buffer.getvalue()


def _style_axes(ax) -> None:
    ax.set_facecolor(CHART_AXES_BG)
    ax.tick_params(axis="x", colors=CHART_MUTED_TEXT)
    ax.tick_params(axis="y", colors=CHART_MUTED_TEXT)
    for spine in ax.spines.values():
        spine.set_color(CHART_BORDER)
    ax.title.set_color(CHART_TEXT)
    ax.xaxis.label.set_color(CHART_TEXT)
    ax.yaxis.label.set_color(CHART_TEXT)


def _style_legend(legend) -> None:
    if legend is None:
        return
    legend.get_title().set_color(CHART_TEXT)
    for label in legend.get_texts():
        label.set_color(CHART_MUTED_TEXT)


def _render_empty_chart(title: str, message: str, figsize: tuple[float, float]) -> bytes:
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(CHART_FIGURE_BG)
    _style_axes(ax)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.text(
        0.5,
        0.5,
        message,
        ha="center",
        va="center",
        fontsize=12,
        color=CHART_MUTED_TEXT,
        transform=ax.transAxes,
    )
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return _figure_to_png_bytes(fig)


def _sorted_champion_totals(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("champion_name", as_index=False)["games"]
        .sum()
        .sort_values(["games", "champion_name"], ascending=[False, True])
    )


def _build_week_axis(start_date: date, end_date: date) -> pd.DatetimeIndex:
    week_start = crud._get_week_start(start_date)
    week_end = crud._get_week_start(end_date)
    return pd.date_range(start=week_start, end=week_end, freq="7D")


async def _fetch_archive_rows(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    player_name: Optional[str],
) -> tuple[list[dict], bool]:
    """Read archive rows with raw SQL if table exists. Returns (rows, archive_available)."""
    global _archive_table_available

    if _archive_table_available is False:
        return [], False

    if _archive_table_available is None:
        try:
            await db.execute(text("SELECT 1 FROM weekly_champion_archives LIMIT 1"))
            _archive_table_available = True
        except SQLAlchemyError:
            _archive_table_available = False
            logger.warning("weekly_champion_archives table not found; using weekly_champions only")
            await db.rollback()
            return [], False

    sql = """
    SELECT player_name, champion_name, week_start_date, times_played
    FROM weekly_champion_archives
    WHERE week_start_date >= :start_date
      AND week_start_date <= :end_date
    """

    params: dict[str, object] = {
        "start_date": start_date,
        "end_date": end_date,
    }

    if player_name:
        sql += " AND player_name = :player_name"
        params["player_name"] = player_name

    try:
        rows = (await db.execute(text(sql), params)).mappings().all()
        parsed = [
            {
                "player_name": row["player_name"],
                "champion_name": row["champion_name"],
                "week_start_date": row["week_start_date"],
                "games": int(row["times_played"] or 0),
            }
            for row in rows
            if int(row["times_played"] or 0) > 0
        ]
        return parsed, True
    except SQLAlchemyError:
        logger.exception("Archive table query failed; continuing without archive source")
        _archive_table_available = False
        await db.rollback()
        return [], False


async def _fetch_weekly_rows(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    player_name: Optional[str],
) -> list[models.WeeklyChampion]:
    query = select(models.WeeklyChampion).where(
        models.WeeklyChampion.week_start_date >= start_date,
        models.WeeklyChampion.week_start_date <= end_date,
        models.WeeklyChampion.played.is_(True),
    )
    if player_name:
        query = query.where(models.WeeklyChampion.player_name == player_name)

    try:
        return (await db.execute(query)).scalars().all()
    except SQLAlchemyError:
        logger.exception("Weekly champions query failed")
        await db.rollback()
        return []


async def get_data_date_bounds(db: AsyncSession) -> tuple[Optional[date], Optional[date]]:
    """Return earliest/latest dates from available data sources."""
    archive_rows, archive_available = await _fetch_archive_rows(
        db=db,
        start_date=date(1970, 1, 1),
        end_date=date(2100, 1, 1),
        player_name=None,
    )

    archive_min = min((row["week_start_date"] for row in archive_rows), default=None)
    archive_max = max((row["week_start_date"] for row in archive_rows), default=None)

    weekly_query = select(
        func.min(models.WeeklyChampion.week_start_date),
        func.max(models.WeeklyChampion.week_start_date),
    ).where(models.WeeklyChampion.played.is_(True))

    # If archive table exists, prefer weekly table as "active" source from current week onward.
    if archive_available:
        weekly_query = weekly_query.where(models.WeeklyChampion.week_start_date >= crud._get_week_start())

    try:
        weekly_min, weekly_max = (await db.execute(weekly_query)).one()
    except SQLAlchemyError:
        logger.exception("Weekly bounds query failed")
        await db.rollback()
        weekly_min, weekly_max = None, None

    minimum_candidates = [value for value in (archive_min, weekly_min) if value is not None]
    maximum_candidates = [value for value in (archive_max, weekly_max) if value is not None]

    earliest = min(minimum_candidates) if minimum_candidates else None
    latest = max(maximum_candidates) if maximum_candidates else None
    return earliest, latest


async def build_games_dataframe(
    db: AsyncSession,
    start_date: date,
    end_date: date,
    player_name: Optional[str] = None,
) -> pd.DataFrame:
    records: list[dict] = []

    archive_rows, archive_available = await _fetch_archive_rows(
        db=db,
        start_date=start_date,
        end_date=end_date,
        player_name=player_name,
    )
    records.extend(archive_rows)

    weekly_start = max(start_date, crud._get_week_start()) if archive_available else start_date
    weekly_rows = await _fetch_weekly_rows(db, weekly_start, end_date, player_name)
    for row in weekly_rows:
        records.append(
            {
                "player_name": row.player_name,
                "champion_name": row.champion_name,
                "week_start_date": row.week_start_date,
                "games": 1,
            }
        )

    if not records:
        return pd.DataFrame(columns=["player_name", "champion_name", "week_start_date", "games"])

    df = pd.DataFrame.from_records(records)
    df["week_start_date"] = pd.to_datetime(df["week_start_date"])
    df["games"] = pd.to_numeric(df["games"], downcast="integer")
    return df


def build_chart_json_data(
    df: pd.DataFrame,
    mode: str,
    player_name: Optional[str],
) -> dict:
    """Build JSON-serialisable chart data for bar, line, and pie charts.

    Args:
        df: Games dataframe from build_games_dataframe.
        mode: 'all' or 'player'.
        player_name: Required when mode='player'; also used for pie chart.

    Returns:
        Dictionary with keys bar_data, line_data, line_champions, pie_data.
    """
    # --- Bar chart ---
    if mode == "player" and player_name:
        player_df = df[df["player_name"] == player_name]
        grouped = (
            player_df.groupby("champion_name", as_index=False)["games"]
            .sum()
            .sort_values(["games", "champion_name"], ascending=[False, True])
        )
        bar_data: list[dict] = [
            {"champion": str(row["champion_name"]), "games": int(row["games"])}
            for _, row in grouped.iterrows()
        ]
    else:
        grouped_all = df.groupby(["champion_name", "player_name"], as_index=False)["games"].sum()
        totals = (
            grouped_all.groupby("champion_name", as_index=False)["games"]
            .sum()
            .sort_values(["games", "champion_name"], ascending=[False, True])
        )
        bar_data = []
        for _, total_row in totals.iterrows():
            champ = str(total_row["champion_name"])
            entry: dict = {"champion": champ}
            for player in PLAYERS:
                player_rows = grouped_all[
                    (grouped_all["champion_name"] == champ) & (grouped_all["player_name"] == player)
                ]
                entry[player] = int(player_rows["games"].sum()) if not player_rows.empty else 0
            bar_data.append(entry)

    # --- Line chart ---
    scoped_df = df if mode == "all" else df[df["player_name"] == player_name]
    if scoped_df.empty:
        line_data: list[dict] = []
        line_champions: list[str] = []
    else:
        champ_totals = (
            scoped_df.groupby("champion_name")["games"]
            .sum()
            .sort_values(ascending=False)
        )
        line_champions = champ_totals.index.tolist()

        weekly = (
            scoped_df.groupby(["week_start_date", "champion_name"], as_index=False)["games"]
            .sum()
        )
        weeks = sorted(scoped_df["week_start_date"].unique())
        pivot = (
            weekly.pivot(index="week_start_date", columns="champion_name", values="games")
            .reindex(weeks)
            .fillna(0)
        )

        line_data = []
        for week in weeks:
            entry_: dict = {"week": pd.Timestamp(week).strftime("%Y-%m-%d")}
            for champ in line_champions:
                entry_[champ] = int(pivot.loc[week, champ]) if champ in pivot.columns else 0
            line_data.append(entry_)

    # --- Pie chart (always player-specific) ---
    pie_player = player_name if player_name else (PLAYERS[0] if PLAYERS else None)
    if pie_player and not df.empty:
        pie_df = df[df["player_name"] == pie_player]
        pie_grouped = (
            pie_df.groupby("champion_name")["games"]
            .sum()
            .sort_values(ascending=False)
        )
        pie_data: list[dict] = [
            {"name": str(champ), "value": int(games)}
            for champ, games in pie_grouped.items()
            if games > 0
        ]
    else:
        pie_data = []

    total_games = int(df["games"].sum()) if not df.empty else 0

    return {
        "bar_data": bar_data,
        "line_data": line_data,
        "line_champions": line_champions,
        "pie_data": pie_data,
        "pie_player": pie_player or "",
        "total_games": total_games,
    }


def render_bar_chart(
    df: pd.DataFrame,
    mode: str,
    player_name: Optional[str],
    top_n: int,
) -> bytes:
    if df.empty:
        return _render_empty_chart("Champion Games (Bar)", "No data in selected range", (11, 5))

    if mode == "player":
        player_df = df[df["player_name"] == player_name]
        if player_df.empty:
            return _render_empty_chart("Champion Games (Bar)", "No data in selected range", (11, 5))

        grouped = _sorted_champion_totals(player_df).head(top_n)
        if grouped.empty:
            return _render_empty_chart("Champion Games (Bar)", "No data in selected range", (11, 5))

        fig, ax = plt.subplots(figsize=(11, 5))
        fig.patch.set_facecolor(CHART_FIGURE_BG)
        _style_axes(ax)
        ax.bar(grouped["champion_name"], grouped["games"], color="#d97706")
        ax.set_title(f"Top Champions - {player_name}", fontsize=14, fontweight="bold")
        ax.set_ylabel("Games Played")
        ax.set_xlabel("Champion")
        ax.tick_params(axis="x", rotation=40)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.grid(axis="y", alpha=0.4, color=CHART_GRID, linestyle="--", linewidth=0.8)
        return _figure_to_png_bytes(fig)

    grouped = (
        df.groupby(["champion_name", "player_name"], as_index=False)["games"]
        .sum()
    )
    totals = (
        grouped.groupby("champion_name", as_index=False)["games"]
        .sum()
        .sort_values(["games", "champion_name"], ascending=[False, True])
        .head(top_n)
    )
    if totals.empty:
        return _render_empty_chart("Champion Games (Bar)", "No data in selected range", (12, 6))

    top_champions = totals["champion_name"].tolist()
    grouped = grouped[grouped["champion_name"].isin(top_champions)]
    pivot = grouped.pivot(index="champion_name", columns="player_name", values="games").fillna(0)
    pivot = pivot.reindex(top_champions, fill_value=0)
    for player in PLAYERS:
        if player not in pivot.columns:
            pivot[player] = 0
    pivot = pivot[PLAYERS]

    x = np.arange(len(pivot.index))
    width = 0.16

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(CHART_FIGURE_BG)
    _style_axes(ax)
    for idx, player in enumerate(PLAYERS):
        offset = (idx - 2) * width
        ax.bar(x + offset, pivot[player], width=width, label=player, color=PLAYER_COLORS[player])

    ax.set_title("Top Champions - All Players", fontsize=14, fontweight="bold")
    ax.set_ylabel("Games Played")
    ax.set_xlabel("Champion")
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index, rotation=35, ha="right")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", alpha=0.4, color=CHART_GRID, linestyle="--", linewidth=0.8)
    legend = ax.legend(title="Players", frameon=False)
    _style_legend(legend)
    return _figure_to_png_bytes(fig)


def render_pie_chart(df: pd.DataFrame, player_name: str, top_n: int) -> bytes:
    player_df = df[df["player_name"] == player_name]
    grouped = _sorted_champion_totals(player_df).head(top_n)

    if grouped.empty:
        fig, ax = plt.subplots(figsize=(7.2, 6.8))
        fig.patch.set_facecolor(CHART_FIGURE_BG)
        ax.set_facecolor(CHART_AXES_BG)
        ax.pie(
            [1],
            colors=["#3b556b"],
            startangle=90,
            radius=1.08,
            wedgeprops={"linewidth": 1.5, "edgecolor": CHART_FIGURE_BG},
        )
        ax.text(0, 0, "No games", ha="center", va="center", fontsize=14, fontweight="bold", color=CHART_TEXT)
        ax.set_title(f"{player_name} Champion Share", fontsize=12, fontweight="bold")
        ax.title.set_color(CHART_TEXT)
        ax.set_aspect("equal")
        return _figure_to_png_bytes(fig)

    labels = grouped["champion_name"].tolist()
    values = grouped["games"].astype(int).tolist()

    fig, ax = plt.subplots(figsize=(7.6, 7.4))
    fig.patch.set_facecolor(CHART_FIGURE_BG)
    ax.set_facecolor(CHART_AXES_BG)
    pie_colors = list(islice(cycle(PIE_COLORS), len(values)))
    wedges, _, autotexts = ax.pie(
        values,
        startangle=90,
        colors=pie_colors,
        radius=1.12,
        pctdistance=0.72,
        autopct=lambda pct: f"{pct:.0f}%" if pct >= 5 else "",
        textprops={"color": CHART_TEXT, "fontsize": 10, "fontweight": "semibold"},
        wedgeprops={"linewidth": 1.2, "edgecolor": CHART_FIGURE_BG},
    )
    for autotext in autotexts:
        autotext.set_color(CHART_TEXT)

    legend_labels = [f"{name} ({count})" for name, count in zip(labels, values)]
    legend = ax.legend(
        wedges,
        legend_labels,
        title="Champions",
        loc="upper center",
        bbox_to_anchor=(0.5, -0.06),
        ncol=2 if len(legend_labels) > 4 else 1,
        frameon=False,
        fontsize=9,
    )
    _style_legend(legend)
    ax.set_title(f"{player_name} Champion Share", fontsize=12, fontweight="bold")
    ax.title.set_color(CHART_TEXT)
    ax.set_aspect("equal")
    return _figure_to_png_bytes(fig)


def render_line_chart(
    df: pd.DataFrame,
    mode: str,
    player_name: Optional[str],
    top_n: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> bytes:
    scoped_df = df if mode == "all" else df[df["player_name"] == player_name]
    if scoped_df.empty:
        return _render_empty_chart("Weekly Champion Trend", "No data in selected range", (11, 5))

    top_champions = _sorted_champion_totals(scoped_df).head(top_n)["champion_name"].tolist()
    if not top_champions:
        return _render_empty_chart("Weekly Champion Trend", "No data in selected range", (11, 5))

    weekly = (
        scoped_df[scoped_df["champion_name"].isin(top_champions)]
        .groupby(["week_start_date", "champion_name"], as_index=False)["games"]
        .sum()
    )

    if start_date and end_date:
        week_axis = _build_week_axis(start_date, end_date)
    else:
        min_week = weekly["week_start_date"].min().date()
        max_week = weekly["week_start_date"].max().date()
        week_axis = _build_week_axis(min_week, max_week)

    fig, ax = plt.subplots(figsize=(11, 5))
    fig.patch.set_facecolor(CHART_FIGURE_BG)
    _style_axes(ax)

    for champion in top_champions:
        champion_series = (
            weekly[weekly["champion_name"] == champion]
            .set_index("week_start_date")["games"]
            .reindex(week_axis, fill_value=0)
        )
        ax.plot(
            week_axis,
            champion_series.values,
            marker="o",
            linewidth=2,
            markersize=4,
            label=champion,
        )

    title = "Weekly Champion Trend - All Players" if mode == "all" else f"Weekly Champion Trend - {player_name}"
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_ylabel("Games Played")
    ax.set_xlabel("Week Start")
    ax.grid(alpha=0.4, color=CHART_GRID, linestyle="--", linewidth=0.8)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.tick_params(axis="x", rotation=35)
    legend = ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1), borderaxespad=0, frameon=False)
    _style_legend(legend)
    return _figure_to_png_bytes(fig)
