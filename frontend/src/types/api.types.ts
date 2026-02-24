export interface SessionReview {
  id: number
  notes: string
  last_updated: string
  created_at: string
}

export interface WeeklyChampion {
  id: number
  player_name: string
  champion_name: string
  played: boolean
  week_start_date: string
  created_at: string
}

export interface DraftNote {
  id: number
  notes: string
  last_updated: string
  created_at: string
}

export interface PickStat {
  id: number
  champion_name: string
  first_pick_games: number
  first_pick_wins: number
  win_rate: number
  created_at: string
  updated_at: string
}

export interface SessionReviewArchive {
  id: number
  title: string
  notes: string
  original_date?: string
  archived_at: string
}

export interface ChampionPool {
  id: number
  player_name: string
  champion_name: string
  description: string
  pick_priority: string
  disabled: boolean
  effective_from_week: string
  effective_to_week: string | null
  created_at: string
  updated_at: string
}

export interface WeeklyMessage {
  id: number
  message: string
  last_updated: string
  created_at: string
}

export interface Fine {
  id: number
  player_name: string
  reason: string
  amount: number
  created_at: string
}

export interface PlayerFinesSummary {
  player_name: string
  total_amount: number
  fines: Fine[]
}

export interface ClashDates {
  id: number
  date1: string | null
  date2: string | null
  updated_at: string
}

export interface CurrentWeekConfig {
  target_date: string
  week_start_date: string
  week_start_weekday: number
  week_start_day_name: string
}

export interface WeekBoundaryVersion {
  id: number
  week_start_weekday: number
  effective_from_date: string
  effective_to_date: string | null
  created_at: string
}
