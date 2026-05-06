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
  won?: boolean | null
  riot_match_id?: string | null
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

export interface Player {
  id: number
  player_name: string
  riot_id: string | null
  puuid: string | null
  region: string
  created_at: string | null
  updated_at: string | null
}

export interface MatchHistory {
  id: number
  player_name: string
  riot_match_id: string
  champion_name: string
  won: boolean
  kills: number
  deaths: number
  assists: number
  cs: number
  vision_score: number
  gold_earned: number
  damage_to_champions: number
  game_duration_seconds: number
  team_position: string | null
  game_start_time: string
  week_start_date: string
  queue_id: number
  user_excluded: boolean
  is_remake: boolean
  created_at: string | null
}

export interface ExcludedFriend {
  id: number
  player_name: string
  riot_id: string
  puuid: string | null
  region: string
  created_at: string | null
  updated_at: string | null
}

export interface SyncResult {
  player_name: string
  games_synced: number
  games_excluded: number
  games_already_present: number
  total_games_found: number
  message: string
}

export interface SyncAllResult {
  trigger: 'manual' | 'scheduled' | 'full_manual'
  started_at: string
  finished_at: string
  per_player: SyncResult[]
  total_games_synced: number
  total_games_excluded: number
  total_games_already_present: number
  total_games_found: number
  failed_players: string[]
  message: string
}

export interface LastSync {
  last_synced_at: string | null
}

export interface FullSyncStarted {
  run_id: number
  status: 'running'
  message: string
}

export interface FullSyncProgress {
  players_total: number
  players_done: number
  current_player: string | null
  games_synced_so_far: number
  games_found_so_far: number
}

export interface FullSyncStatus {
  run_id: number
  status: 'running' | 'success' | 'partial' | 'failed'
  progress: FullSyncProgress | null
  result: SyncAllResult | null
}
