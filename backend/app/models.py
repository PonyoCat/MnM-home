from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Date,
    DateTime,
    CheckConstraint,
    Index,
    UniqueConstraint,
    JSON,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from .database import Base

class SessionReview(Base):
    __tablename__ = "session_reviews"

    id = Column(Integer, primary_key=True, index=True)
    notes = Column(Text, default="", nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WeeklyChampion(Base):
    __tablename__ = "weekly_champions"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(255), nullable=False)
    champion_name = Column(String(255), nullable=False)
    played = Column(Boolean, default=False)
    week_start_date = Column(Date, nullable=False, index=True)
    won = Column(Boolean, nullable=True)  # True=win, False=loss, None=manual entry
    riot_match_id = Column(String(255), nullable=True, index=True)  # links to match_history; null for manual entries
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DraftNote(Base):
    __tablename__ = "draft_notes"

    id = Column(Integer, primary_key=True, index=True)
    notes = Column(Text, default="", nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PickStat(Base):
    __tablename__ = "pick_stats"

    id = Column(Integer, primary_key=True, index=True)
    champion_name = Column(String(255), unique=True, nullable=False, index=True)
    first_pick_games = Column(Integer, default=0)
    first_pick_wins = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class SessionReviewArchive(Base):
    """Archive table for past session reviews"""
    __tablename__ = "session_review_archives"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    notes = Column(Text, default="", nullable=False)
    archived_at = Column(DateTime(timezone=True), server_default=func.now())
    original_date = Column(Date, nullable=True)

class ChampionPool(Base):
    """Champion pool entry for a specific player"""
    __tablename__ = "champion_pools"
    __table_args__ = (
        CheckConstraint(
            "effective_to_week IS NULL OR effective_to_week >= effective_from_week",
            name="ck_champion_pools_effective_range",
        ),
        Index(
            "ix_champion_pools_player_effective_range",
            "player_name",
            "effective_from_week",
            "effective_to_week",
        ),
        Index(
            "ix_champion_pools_active_player_champion_unique",
            "player_name",
            "champion_name",
            unique=True,
            postgresql_where=text("effective_to_week IS NULL"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(255), nullable=False, index=True)  # One of: Alex, Hans, Elias, Mikkel, Sinus
    champion_name = Column(String(255), nullable=False)
    description = Column(Text, default="", nullable=False)  # When/why to pick this champion
    pick_priority = Column(Text, default="", nullable=False)  # Pick strategy notes
    disabled = Column(Boolean, default=False, nullable=False)  # Disabled champions are excluded from accountability
    effective_from_week = Column(Date, nullable=False, index=True)
    effective_to_week = Column(Date, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class WeeklyMessage(Base):
    """Weekly message shared across all users"""
    __tablename__ = "weekly_messages"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, default="", nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Fine(Base):
    """Fine/penalty for a team member (Bødekasse)"""
    __tablename__ = "fines"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(255), nullable=False, index=True)  # Alex, Hans, Elias, Mikkel, Sinus
    reason = Column(Text, nullable=False)  # Description of the infraction
    amount = Column(Integer, nullable=False)  # Amount in DKK (kroner)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ClashDates(Base):
    """Next clash dates - singleton table with up to 2 dates"""
    __tablename__ = "clash_dates"

    id = Column(Integer, primary_key=True, index=True)
    date1 = Column(Date, nullable=True)  # First clash date
    date2 = Column(Date, nullable=True)  # Second clash date
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WeekResetConfig(Base):
    """Week reset configuration history for calculating week start dates."""
    __tablename__ = "week_reset_configs"
    __table_args__ = (
        CheckConstraint(
            "week_start_weekday >= 0 AND week_start_weekday <= 6",
            name="ck_week_reset_configs_weekday_range",
        ),
        CheckConstraint(
            "effective_to_date IS NULL OR effective_to_date >= effective_from_date",
            name="ck_week_reset_configs_effective_range",
        ),
        Index(
            "ix_week_reset_configs_effective_range",
            "effective_from_date",
            "effective_to_date",
        ),
        Index(
            "ix_week_reset_configs_active_unique",
            text("(1)"),
            unique=True,
            postgresql_where=text("effective_to_date IS NULL"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    week_start_weekday = Column(Integer, nullable=False)  # Python weekday: Monday=0 ... Sunday=6
    effective_from_date = Column(Date, nullable=False)
    effective_to_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Player(Base):
    """Roster player with Riot identity (cached PUUID)."""
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    player_name = Column(String(255), unique=True, nullable=False, index=True)
    riot_id = Column(String(255), nullable=True)  # "Ponyo#Meeps"
    puuid = Column(String(255), nullable=True)  # Cached PUUID from Riot API
    region = Column(String(50), nullable=False, default="euw")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MatchHistory(Base):
    """One row per fetched match per roster player."""
    __tablename__ = "match_history"
    __table_args__ = (
        UniqueConstraint("player_name", "riot_match_id", name="uq_player_match"),
        Index("ix_match_history_player", "player_name"),
        Index("ix_match_history_week", "week_start_date"),
        Index("ix_match_history_match_id", "riot_match_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(255), nullable=False)
    riot_match_id = Column(String(255), nullable=False)  # "EUW1_1234567890"
    champion_name = Column(String(255), nullable=False)
    won = Column(Boolean, nullable=False)
    kills = Column(Integer, nullable=False, default=0)
    deaths = Column(Integer, nullable=False, default=0)
    assists = Column(Integer, nullable=False, default=0)
    cs = Column(Integer, nullable=False, default=0)
    vision_score = Column(Integer, nullable=False, default=0)
    gold_earned = Column(Integer, nullable=False, default=0)
    damage_to_champions = Column(Integer, nullable=False, default=0)
    game_duration_seconds = Column(Integer, nullable=False, default=0)
    team_position = Column(String(50), nullable=True)
    game_start_time = Column(DateTime(timezone=True), nullable=False)
    week_start_date = Column(Date, nullable=False)
    queue_id = Column(Integer, nullable=False, default=420)
    team_puuids = Column(JSONB, nullable=False, default=list)
    user_excluded = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ExcludedFriend(Base):
    """A Riot ID that, when present on a roster player's team, excludes that match from accountability."""
    __tablename__ = "excluded_friends"
    __table_args__ = (
        UniqueConstraint("player_name", "riot_id", name="uq_excluded_friend_per_player"),
        Index("ix_excluded_friends_player", "player_name"),
        Index("ix_excluded_friends_puuid", "puuid"),
    )

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(255), nullable=False)  # Roster player who owns this exclusion
    riot_id = Column(String(255), nullable=False)  # "Andy#EUW"
    puuid = Column(String(255), nullable=True)  # Cached PUUID; null until first resolved
    region = Column(String(50), nullable=False, default="euw")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SyncRun(Base):
    """One row per sync attempt (manual or scheduled)."""
    __tablename__ = "sync_runs"
    __table_args__ = (
        Index("ix_sync_runs_finished_at", "finished_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
    trigger = Column(String(20), nullable=False)  # 'scheduled' | 'manual'
    status = Column(String(20), nullable=False)  # 'running' | 'success' | 'partial' | 'failed'
    summary = Column(JSONB, nullable=True)
    progress = Column(JSONB, nullable=True)  # incremental progress for long-running syncs
