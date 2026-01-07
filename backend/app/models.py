from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, func, Index
from .database import Base

class SessionReview(Base):
    __tablename__ = "session_reviews"

    id = Column(Integer, primary_key=True, index=True)
    notes = Column(Text, default="", nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WeeklyChampion(Base):
    __tablename__ = "weekly_champions"
    __table_args__ = (
        Index(
            "ix_weekly_champions_week_start_player_champion_archived_at",
            "week_start_date",
            "player_name",
            "champion_name",
            "archived_at",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(255), nullable=False)
    champion_name = Column(String(255), nullable=False)
    played = Column(Boolean, default=False)
    week_start_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    archived_at = Column(DateTime(timezone=True), nullable=True, index=True)

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

class WeeklyChampionArchive(Base):
    """Archive table for weekly champion stats (for future graphs)"""
    __tablename__ = "weekly_champion_archives"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(255), nullable=False, index=True)
    champion_name = Column(String(255), nullable=False)
    times_played = Column(Integer, default=0)
    week_start_date = Column(Date, nullable=False, index=True)
    week_end_date = Column(Date, nullable=False)
    archived_at = Column(DateTime(timezone=True), server_default=func.now())

class ChampionPool(Base):
    """Champion pool entry for a specific player"""
    __tablename__ = "champion_pools"

    id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String(255), nullable=False, index=True)  # One of: Alex, Hans, Elias, Mikkel, Sinus
    champion_name = Column(String(255), nullable=False)
    description = Column(Text, default="", nullable=False)  # When/why to pick this champion
    pick_priority = Column(Text, default="", nullable=False)  # Pick strategy notes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class WeeklyMessage(Base):
    """Weekly message shared across all users"""
    __tablename__ = "weekly_messages"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, default="", nullable=False)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
