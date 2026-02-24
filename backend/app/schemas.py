from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional

# Session Review Schemas
class SessionReviewBase(BaseModel):
    notes: str = Field(default="")

class SessionReviewCreate(SessionReviewBase):
    pass

class SessionReviewUpdate(SessionReviewBase):
    pass

class SessionReview(SessionReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_updated: datetime
    created_at: datetime

# Weekly Champion Schemas
class WeeklyChampionBase(BaseModel):
    player_name: str
    champion_name: str
    played: bool = False
    week_start_date: date

class WeeklyChampionCreate(WeeklyChampionBase):
    pass

class WeeklyChampionUpdate(BaseModel):
    played: bool

class WeeklyChampion(WeeklyChampionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

# Draft Note Schemas
class DraftNoteBase(BaseModel):
    notes: str = Field(default="")

class DraftNoteCreate(DraftNoteBase):
    pass

class DraftNoteUpdate(DraftNoteBase):
    pass

class DraftNote(DraftNoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_updated: datetime
    created_at: datetime

# Pick Stat Schemas
class PickStatBase(BaseModel):
    champion_name: str

class PickStatCreate(PickStatBase):
    pass

class PickStatUpdate(BaseModel):
    first_pick_games: Optional[int] = None
    first_pick_wins: Optional[int] = None

class PickStatChampionUpdate(BaseModel):
    champion_name: str

class PickStat(PickStatBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_pick_games: int
    first_pick_wins: int
    win_rate: float = 0.0  # Computed field
    created_at: datetime
    updated_at: datetime

# Session Review Archive Schemas
class SessionReviewArchiveBase(BaseModel):
    title: str
    notes: str = Field(default="")
    original_date: Optional[date] = None

class SessionReviewArchiveCreate(SessionReviewArchiveBase):
    pass

class SessionReviewArchiveUpdate(BaseModel):
    title: Optional[str] = None
    notes: Optional[str] = None

class SessionReviewArchive(SessionReviewArchiveBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    archived_at: datetime

# Champion Pool Schemas
class ChampionPoolBase(BaseModel):
    player_name: str
    champion_name: str
    description: str = Field(default="")
    pick_priority: str = Field(default="")
    disabled: bool = Field(default=False)

class ChampionPoolCreate(ChampionPoolBase):
    pass

class ChampionPoolUpdate(BaseModel):
    champion_name: Optional[str] = None
    description: Optional[str] = None
    pick_priority: Optional[str] = None
    disabled: Optional[bool] = None

class ChampionPool(ChampionPoolBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    effective_from_week: date
    effective_to_week: Optional[date] = None
    created_at: datetime
    updated_at: datetime

# Weekly Message Schemas
class WeeklyMessageBase(BaseModel):
    message: str = Field(default="")

class WeeklyMessageUpdate(WeeklyMessageBase):
    pass

class WeeklyMessage(WeeklyMessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_updated: datetime
    created_at: datetime

# Accountability Check Schemas
class ChampionDetail(BaseModel):
    """Detailed status for a single champion"""
    champion_name: str
    has_played: bool
    games_played: int

class PlayerAccountability(BaseModel):
    """Schema for player accountability check"""
    player_name: str
    all_champions_played: bool
    missing_champions: list[str]
    total_champions: int
    champions_played: int
    champion_details: list[ChampionDetail]  # NEW: For expandable UI


# Fine Schemas (Bødekasse)
class FineBase(BaseModel):
    player_name: str
    reason: str
    amount: int


class FineCreate(FineBase):
    pass


class Fine(FineBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class PlayerFinesSummary(BaseModel):
    """Summary of fines for a single player"""
    player_name: str
    total_amount: int
    fines: list[Fine]


# Clash Dates Schemas
class ClashDatesBase(BaseModel):
    date1: Optional[date] = None
    date2: Optional[date] = None


class ClashDatesUpdate(ClashDatesBase):
    pass


class ClashDates(ClashDatesBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime


# Week Boundary Config Schemas
class WeekBoundaryVersion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    week_start_weekday: int
    effective_from_date: date
    effective_to_date: Optional[date] = None
    created_at: datetime


class CurrentWeekConfig(BaseModel):
    target_date: date
    week_start_date: date
    week_start_weekday: int
    week_start_day_name: str
