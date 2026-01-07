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
  archived_at: string | null
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

export interface WeeklyChampionArchive {
  id: number
  player_name: string
  champion_name: string
  times_played: number
  week_start_date: string
  week_end_date: string
  archived_at: string
}

export interface ChampionPool {
  id: number
  player_name: string
  champion_name: string
  description: string
  pick_priority: string
  created_at: string
  updated_at: string
}

export interface WeeklyMessage {
  id: number
  message: string
  last_updated: string
  created_at: string
}
