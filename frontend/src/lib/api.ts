const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = {
  // Session Review
  async getSessionReview() {
    const response = await fetch(`${API_URL}/api/session-review`)
    if (!response.ok) throw new Error('Failed to fetch session review')
    return response.json()
  },

  async updateSessionReview(notes: string) {
    const response = await fetch(`${API_URL}/api/session-review`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes })
    })
    if (!response.ok) throw new Error('Failed to update session review')
    return response.json()
  },

  // Weekly Games
  async getWeeklyChampions(weekStart: string) {
    const response = await fetch(`${API_URL}/api/weekly-champions?week_start=${weekStart}`)
    if (!response.ok) throw new Error('Failed to fetch weekly games')
    return response.json()
  },

  async toggleWeeklyChampion(data: {
    player_name: string
    champion_name: string
    played: boolean
    week_start_date: string
  }) {
    const response = await fetch(`${API_URL}/api/weekly-champions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!response.ok) throw new Error('Failed to add game')
    return response.json()
  },

  // Draft Notes
  async getDraftNotes() {
    const response = await fetch(`${API_URL}/api/draft-notes`)
    if (!response.ok) throw new Error('Failed to fetch draft notes')
    return response.json()
  },

  async updateDraftNotes(notes: string) {
    const response = await fetch(`${API_URL}/api/draft-notes`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes })
    })
    if (!response.ok) throw new Error('Failed to update draft notes')
    return response.json()
  },

  // Pick Stats
  async getPickStats() {
    const response = await fetch(`${API_URL}/api/pick-stats`)
    if (!response.ok) throw new Error('Failed to fetch pick stats')
    return response.json()
  },

  async createPickStat(championName: string) {
    const response = await fetch(`${API_URL}/api/pick-stats`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ champion_name: championName })
    })
    if (!response.ok) throw new Error('Failed to create pick stat')
    return response.json()
  },

  async addWin(id: number) {
    const response = await fetch(`${API_URL}/api/pick-stats/${id}/win`, {
      method: 'PATCH'
    })
    if (!response.ok) throw new Error('Failed to add win')
    return response.json()
  },

  async addLoss(id: number) {
    const response = await fetch(`${API_URL}/api/pick-stats/${id}/loss`, {
      method: 'PATCH'
    })
    if (!response.ok) throw new Error('Failed to add loss')
    return response.json()
  },

  async deletePickStat(id: number) {
    const response = await fetch(`${API_URL}/api/pick-stats/${id}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error('Failed to delete pick stat')
    return response.json()
  },

  async updatePickStatChampion(id: number, championName: string) {
    const response = await fetch(`${API_URL}/api/pick-stats/${id}/champion`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ champion_name: championName })
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to update champion name')
    }
    return response.json()
  },

  // Session Review Archives
  async createSessionReviewArchive(title: string, notes: string, originalDate?: string) {
    const response = await fetch(`${API_URL}/api/session-review/archive`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, notes, original_date: originalDate })
    })
    if (!response.ok) throw new Error('Failed to create archive')
    return response.json()
  },

  async getSessionReviewArchives() {
    const response = await fetch(`${API_URL}/api/session-review/archives`)
    if (!response.ok) throw new Error('Failed to fetch archives')
    return response.json()
  },

  async getSessionReviewArchive(id: number) {
    const response = await fetch(`${API_URL}/api/session-review/archives/${id}`)
    if (!response.ok) throw new Error('Failed to fetch archive')
    return response.json()
  },

  async updateSessionReviewArchive(id: number, title?: string, notes?: string) {
    const response = await fetch(`${API_URL}/api/session-review/archives/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, notes })
    })
    if (!response.ok) throw new Error('Failed to update archive')
    return response.json()
  },

  // Weekly Games Additional Methods
  async deleteWeeklyChampion(playerName: string, championName: string, weekStart: string) {
    const response = await fetch(
      `${API_URL}/api/weekly-champions?player_name=${encodeURIComponent(playerName)}&champion_name=${encodeURIComponent(championName)}&week_start=${weekStart}`,
      { method: 'DELETE' }
    )
    if (!response.ok) throw new Error('Failed to delete champion')
    return
  },

  async deleteOneWeeklyChampionInstance(playerName: string, championName: string, weekStart: string, played: boolean = true) {
    const response = await fetch(
      `${API_URL}/api/weekly-champions/instance?player_name=${encodeURIComponent(playerName)}&champion_name=${encodeURIComponent(championName)}&week_start=${weekStart}&played=${played}`,
      { method: 'DELETE' }
    )
    if (!response.ok) throw new Error('Failed to delete game instance')
    return
  },

  async archiveWeeklyChampions(weekStart: string) {
    const response = await fetch(`${API_URL}/api/weekly-champions/archive?week_start=${weekStart}`, {
      method: 'POST'
    })
    if (!response.ok) throw new Error('Failed to archive weekly games')
    return response.json()
  },

  async getWeeklyChampionArchives(playerName?: string) {
    const url = playerName
      ? `${API_URL}/api/weekly-champions/archives?player_name=${encodeURIComponent(playerName)}`
      : `${API_URL}/api/weekly-champions/archives`
    const response = await fetch(url)
    if (!response.ok) throw new Error('Failed to fetch game archives')
    return response.json()
  },

  // Champion Pool
  async getChampionPools(playerName?: string) {
    const url = playerName
      ? `${API_URL}/api/champion-pool?player_name=${encodeURIComponent(playerName)}`
      : `${API_URL}/api/champion-pool`
    const response = await fetch(url)
    if (!response.ok) throw new Error('Failed to fetch champion pools')
    return response.json()
  },

  async createChampionPool(data: {
    player_name: string
    champion_name: string
    description: string
    pick_priority: string
  }) {
    const response = await fetch(`${API_URL}/api/champion-pool`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!response.ok) throw new Error('Failed to create champion pool entry')
    return response.json()
  },

  async updateChampionPool(
    id: number,
    data: {
      champion_name?: string
      description?: string
      pick_priority?: string
    }
  ) {
    const response = await fetch(`${API_URL}/api/champion-pool/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!response.ok) throw new Error('Failed to update champion pool entry')
    return response.json()
  },

  async deleteChampionPool(id: number) {
    const response = await fetch(`${API_URL}/api/champion-pool/${id}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error('Failed to delete champion pool entry')
    return response.json()
  },

  // Weekly Message
  async getWeeklyMessage() {
    const response = await fetch(`${API_URL}/api/weekly-message`)
    if (!response.ok) throw new Error('Failed to fetch weekly message')
    return response.json()
  },

  async updateWeeklyMessage(message: string) {
    const response = await fetch(`${API_URL}/api/weekly-message`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    })
    if (!response.ok) throw new Error('Failed to update weekly message')
    return response.json()
  }
}

export { API_URL }
