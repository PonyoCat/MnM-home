import { withRetry, fetchWithTimeout } from './retry'
import type { CurrentWeekConfig, WeekBoundaryVersion } from '@/types/api.types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const CHARTS_BASE = '/api/analytics/charts'

type ChartMode = 'all' | 'player'

interface ChartDateRangeParams {
  startDate: string
  endDate: string
  topN?: number
}

export interface BarChartParams extends ChartDateRangeParams {
  mode: ChartMode
  playerName?: string
}

export interface PieChartParams extends ChartDateRangeParams {
  playerName: string
}

export interface LineChartParams extends ChartDateRangeParams {
  mode: ChartMode
  playerName?: string
}

export interface ChartDateBounds {
  earliest_date: string | null
  latest_date: string | null
}

export interface ChartJsonDataParams {
  mode: ChartMode
  playerName: string
  startDate: string
  endDate: string
}

export interface ChartJsonData {
  bar_data: Record<string, string | number>[]
  line_data: Record<string, string | number>[]
  line_champions: string[]
  pie_data: { name: string; value: number }[]
  pie_player: string
  total_games: number
}

function buildChartUrl(path: string, params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    search.set(key, String(value))
  })

  return `${API_URL}${path}?${search.toString()}`
}

export function getBarChartUrl(params: BarChartParams) {
  return buildChartUrl(`${CHARTS_BASE}/bar`, {
    mode: params.mode,
    player_name: params.playerName,
    start_date: params.startDate,
    end_date: params.endDate,
    top_n: params.topN
  })
}

export function getPieChartUrl(params: PieChartParams) {
  return buildChartUrl(`${CHARTS_BASE}/pie`, {
    player_name: params.playerName,
    start_date: params.startDate,
    end_date: params.endDate,
    top_n: params.topN
  })
}

export function getLineChartUrl(params: LineChartParams) {
  return buildChartUrl(`${CHARTS_BASE}/line`, {
    mode: params.mode,
    player_name: params.playerName,
    start_date: params.startDate,
    end_date: params.endDate,
    top_n: params.topN
  })
}

// Helper function to make API calls with retry logic and timeout
async function apiFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  type HttpError = Error & { status?: number }

  return withRetry(async () => {
    const response = await fetchWithTimeout(
      `${API_URL}${endpoint}`,
      options,
      10000 // 10 second timeout
    )

    if (!response.ok) {
      // Throw error with status for better error handling
      const error: HttpError = new Error(`HTTP ${response.status}: ${response.statusText}`)
      error.status = response.status
      throw error
    }

    return response
  })
}

export const api = {
  getBarChartUrl,
  getPieChartUrl,
  getLineChartUrl,

  async getChartJsonData(params: ChartJsonDataParams): Promise<ChartJsonData> {
    try {
      const search = new URLSearchParams({
        mode: params.mode,
        player_name: params.playerName,
        start_date: params.startDate,
        end_date: params.endDate,
      })
      const response = await apiFetch(`/api/analytics/charts/json-data?${search.toString()}`)
      return response.json()
    } catch (error) {
      console.error('Failed to fetch chart json data:', error)
      throw error
    }
  },

  async getChartDateBounds(): Promise<ChartDateBounds> {
    try {
      const response = await apiFetch('/api/analytics/charts/date-bounds')
      return response.json()
    } catch (error) {
      console.error('Failed to fetch chart date bounds:', error)
      throw error
    }
  },

  // Week Config
  async getCurrentWeekConfig(targetDate?: string): Promise<CurrentWeekConfig> {
    try {
      const url = targetDate
        ? `/api/week-config/current?target_date=${targetDate}`
        : '/api/week-config/current'
      const response = await apiFetch(url)
      return response.json()
    } catch (error) {
      console.error('Failed to fetch current week config:', error)
      throw error
    }
  },

  async getWeekBoundaryVersions(): Promise<WeekBoundaryVersion[]> {
    try {
      const response = await apiFetch('/api/week-config/versions')
      return response.json()
    } catch (error) {
      console.error('Failed to fetch week boundary versions:', error)
      throw error
    }
  },

  // Session Review
  async getSessionReview() {
    try {
      const response = await apiFetch('/api/session-review')
      return response.json()
    } catch (error) {
      console.error('Failed to fetch session review:', error)
      throw error
    }
  },

  async updateSessionReview(notes: string) {
    try {
      const response = await apiFetch('/api/session-review', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes })
      })
      return response.json()
    } catch (error) {
      console.error('Failed to update session review:', error)
      throw error
    }
  },

  // Weekly Games
  async getWeeklyChampions(weekStart: string) {
    try {
      const response = await apiFetch(`/api/weekly-champions?week_start=${weekStart}`)
      return response.json()
    } catch (error) {
      console.error('Failed to fetch weekly games:', error)
      throw error
    }
  },

  async toggleWeeklyChampion(data: {
    player_name: string
    champion_name: string
    played: boolean
    week_start_date: string
  }) {
    try {
      const response = await apiFetch('/api/weekly-champions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      return response.json()
    } catch (error) {
      console.error('Failed to add game:', error)
      throw error
    }
  },

  // Draft Notes
  async getDraftNotes() {
    try {
      const response = await apiFetch('/api/draft-notes')
      return response.json()
    } catch (error) {
      console.error('Failed to fetch draft notes:', error)
      throw error
    }
  },

  async updateDraftNotes(notes: string) {
    try {
      const response = await apiFetch('/api/draft-notes', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes })
      })
      return response.json()
    } catch (error) {
      console.error('Failed to update draft notes:', error)
      throw error
    }
  },

  // Pick Stats
  async getPickStats() {
    try {
      const response = await apiFetch('/api/pick-stats')
      return response.json()
    } catch (error) {
      console.error('Failed to fetch pick stats:', error)
      throw error
    }
  },

  async createPickStat(championName: string) {
    try {
      const response = await apiFetch('/api/pick-stats', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ champion_name: championName })
      })
      return response.json()
    } catch (error) {
      console.error('Failed to create pick stat:', error)
      throw error
    }
  },

  async addWin(id: number) {
    try {
      const response = await apiFetch(`/api/pick-stats/${id}/win`, {
        method: 'PATCH'
      })
      return response.json()
    } catch (error) {
      console.error('Failed to add win:', error)
      throw error
    }
  },

  async addLoss(id: number) {
    try {
      const response = await apiFetch(`/api/pick-stats/${id}/loss`, {
        method: 'PATCH'
      })
      return response.json()
    } catch (error) {
      console.error('Failed to add loss:', error)
      throw error
    }
  },

  async deletePickStat(id: number) {
    try {
      const response = await apiFetch(`/api/pick-stats/${id}`, {
        method: 'DELETE'
      })
      return response.json()
    } catch (error) {
      console.error('Failed to delete pick stat:', error)
      throw error
    }
  },

  async updatePickStatChampion(id: number, championName: string) {
    try {
      const response = await apiFetch(`/api/pick-stats/${id}/champion`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ champion_name: championName })
      })
      return response.json()
    } catch (error) {
      console.error('Failed to update champion name:', error)
      throw error
    }
  },

  async updatePickStat(id: number, data: { first_pick_games?: number; first_pick_wins?: number }) {
    try {
      const response = await apiFetch(`/api/pick-stats/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      return response.json()
    } catch (error) {
      console.error('Failed to update pick stat:', error)
      throw error
    }
  },

  // Session Review Archives
  async createSessionReviewArchive(title: string, notes: string, originalDate?: string) {
    try {
      const response = await apiFetch('/api/session-review/archive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, notes, original_date: originalDate })
      })
      return response.json()
    } catch (error) {
      console.error('Failed to create archive:', error)
      throw error
    }
  },

  async getSessionReviewArchives() {
    try {
      const response = await apiFetch('/api/session-review/archives')
      return response.json()
    } catch (error) {
      console.error('Failed to fetch archives:', error)
      throw error
    }
  },

  async getSessionReviewArchive(id: number) {
    try {
      const response = await apiFetch(`/api/session-review/archives/${id}`)
      return response.json()
    } catch (error) {
      console.error('Failed to fetch archive:', error)
      throw error
    }
  },

  async updateSessionReviewArchive(id: number, title?: string, notes?: string) {
    try {
      const response = await apiFetch(`/api/session-review/archives/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, notes })
      })
      return response.json()
    } catch (error) {
      console.error('Failed to update archive:', error)
      throw error
    }
  },

  // Weekly Games Additional Methods
  async deleteWeeklyChampion(playerName: string, championName: string, weekStart: string) {
    try {
      await apiFetch(
        `/api/weekly-champions?player_name=${encodeURIComponent(playerName)}&champion_name=${encodeURIComponent(championName)}&week_start=${weekStart}`,
        { method: 'DELETE' }
      )
    } catch (error) {
      console.error('Failed to delete champion:', error)
      throw error
    }
  },

  async deleteOneWeeklyChampionInstance(playerName: string, championName: string, weekStart: string, played: boolean = true) {
    try {
      await apiFetch(
        `/api/weekly-champions/instance?player_name=${encodeURIComponent(playerName)}&champion_name=${encodeURIComponent(championName)}&week_start=${weekStart}&played=${played}`,
        { method: 'DELETE' }
      )
    } catch (error) {
      console.error('Failed to delete game instance:', error)
      throw error
    }
  },

  // Champion Pool
  async getChampionPools(playerName?: string, weekStart?: string) {
    try {
      const search = new URLSearchParams()
      if (playerName) search.set('player_name', playerName)
      if (weekStart) search.set('week_start', weekStart)
      const endpoint = search.size > 0
        ? `/api/champion-pool?${search.toString()}`
        : '/api/champion-pool'
      const response = await apiFetch(endpoint)
      return response.json()
    } catch (error) {
      console.error('Failed to fetch champion pools:', error)
      throw error
    }
  },

  async createChampionPool(data: {
    player_name: string
    champion_name: string
    description: string
    pick_priority: string
  }) {
    try {
      const response = await apiFetch('/api/champion-pool', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      return response.json()
    } catch (error) {
      console.error('Failed to create champion pool entry:', error)
      throw error
    }
  },

  async updateChampionPool(
    id: number,
    data: {
      champion_name?: string
      description?: string
      pick_priority?: string
      disabled?: boolean
    }
  ) {
    try {
      const response = await apiFetch(`/api/champion-pool/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      return response.json()
    } catch (error) {
      console.error('Failed to update champion pool entry:', error)
      throw error
    }
  },

  async deleteChampionPool(id: number) {
    try {
      const response = await apiFetch(`/api/champion-pool/${id}`, {
        method: 'DELETE'
      })
      return response.json()
    } catch (error) {
      console.error('Failed to delete champion pool entry:', error)
      throw error
    }
  },

  // Message Board (Weekly Message endpoint)
  async getWeeklyMessage() {
    try {
      const response = await apiFetch('/api/weekly-message')
      return response.json()
    } catch (error) {
      console.error('Failed to fetch message board:', error)
      throw error
    }
  },

  async updateWeeklyMessage(message: string) {
    try {
      const response = await apiFetch('/api/weekly-message', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
      })
      return response.json()
    } catch (error) {
      console.error('Failed to update message board:', error)
      throw error
    }
  },

  // Accountability Check
  async getAccountabilityCheck(weekStart?: string) {
    try {
      const endpoint = weekStart
        ? `/api/accountability/check?week_start=${weekStart}`
        : '/api/accountability/check'
      const response = await apiFetch(endpoint)
      return response.json()
    } catch (error) {
      console.error('Failed to fetch accountability check:', error)
      throw error
    }
  },

  // Fines (Bødekasse)
  async getFines() {
    try {
      const response = await apiFetch('/api/fines')
      return response.json()
    } catch (error) {
      console.error('Failed to fetch fines:', error)
      throw error
    }
  },

  async createFine(data: { player_name: string; reason: string; amount: number }) {
    try {
      const response = await apiFetch('/api/fines', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      return response.json()
    } catch (error) {
      console.error('Failed to create fine:', error)
      throw error
    }
  },

  async deleteFine(id: number) {
    try {
      const response = await apiFetch(`/api/fines/${id}`, {
        method: 'DELETE'
      })
      return response.json()
    } catch (error) {
      console.error('Failed to delete fine:', error)
      throw error
    }
  },

  // Clash Dates
  async getClashDates() {
    try {
      const response = await apiFetch('/api/clash-dates')
      return response.json()
    } catch (error) {
      console.error('Failed to fetch clash dates:', error)
      throw error
    }
  },

  async updateClashDates(date1: string | null, date2: string | null) {
    try {
      const response = await apiFetch('/api/clash-dates', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ date1, date2 })
      })
      return response.json()
    } catch (error) {
      console.error('Failed to update clash dates:', error)
      throw error
    }
  }
}

export { API_URL }
