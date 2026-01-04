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

# Weekly Champion Archive Schemas
class WeeklyChampionArchiveBase(BaseModel):
    player_name: str
    champion_name: str
    times_played: int
    week_start_date: date
    week_end_date: date

class WeeklyChampionArchiveCreate(WeeklyChampionArchiveBase):
    pass

class WeeklyChampionArchive(WeeklyChampionArchiveBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    archived_at: datetime
