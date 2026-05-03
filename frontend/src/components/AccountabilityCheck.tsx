import { useEffect, useState } from 'react'
import { formatDate } from '@/lib/utils'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Button } from './ui/button'
import { LoadingState } from './ui/error-state'
import { api } from '@/lib/api'
import { Check, X, ChevronDown, ChevronRight } from 'lucide-react'

interface ChampionDetail {
  champion_name: string
  has_played: boolean
  games_played: number
}

interface PlayerAccountability {
  player_name: string
  all_champions_played: boolean
  missing_champions: string[]
  total_champions: number
  champions_played: number
  champion_details: ChampionDetail[]
}

function toLocalIsoDate(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function parseLocalIsoDate(value: string): Date {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year, month - 1, day)
}

function getFallbackCurrentWeekStart(): string {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  // Week resets Thursday at 16:00. If it's Thursday and past 16:00, new week starts today.
  const isThursday = today.getDay() === 4
  const pastResetHour = now.getHours() >= 16
  const referenceDate = new Date(today)
  if (!(isThursday && pastResetHour)) {
    referenceDate.setDate(today.getDate() - 1)
  }
  const refDow = referenceDate.getDay()
  const thursday = new Date(referenceDate)
  const daysBack = (refDow - 4 + 7) % 7
  thursday.setDate(referenceDate.getDate() - daysBack)
  return toLocalIsoDate(thursday)
}

function isCurrentWeek(selectedWeek: string | null, currentWeekStart: string | null): boolean {
  if (!selectedWeek || !currentWeekStart) return false
  return selectedWeek === currentWeekStart
}

export function AccountabilityCheck() {
  const [accountabilityData, setAccountabilityData] = useState<PlayerAccountability[]>([])
  const [loading, setLoading] = useState(true)
  const [dataLoading, setDataLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [currentWeekStart, setCurrentWeekStart] = useState<string | null>(null)
  const [selectedWeek, setSelectedWeek] = useState<string | null>(null)

  // NEW: Track expanded state per player (mirror WeeklyChampions.tsx pattern)
  const [expandedPlayers, setExpandedPlayers] = useState<Record<string, boolean>>({
    Alex: false, Hans: false, Elias: false, Mikkel: false, Sinus: false
  })

  useEffect(() => {
    initializeData()
  }, [])

  async function initializeData() {
    const fallbackWeekStart = getFallbackCurrentWeekStart()
    let resolvedWeekStart = fallbackWeekStart
    try {
      const currentWeekConfig = await api.getCurrentWeekConfig()
      resolvedWeekStart = currentWeekConfig.week_start_date || fallbackWeekStart
    } catch (err) {
      console.error('Error loading week config, using fallback:', err)
    } finally {
      setCurrentWeekStart(resolvedWeekStart)
      setSelectedWeek(resolvedWeekStart)
      setLoading(false)
    }
    // Load accountability data in the background after the card is visible
    void loadAccountabilityData(resolvedWeekStart)
  }

  async function loadAccountabilityData(targetWeekStart: string) {
    try {
      setDataLoading(true)
      setError(null)
      const data = await api.getAccountabilityCheck(targetWeekStart)
      setAccountabilityData(data)
    } catch (error) {
      console.error('Error loading accountability check:', error)
      setError(error as Error)
    } finally {
      setDataLoading(false)
    }
  }

  async function loadAccountability(targetWeekStart: string) {
    return loadAccountabilityData(targetWeekStart)
  }

  async function navigateWeek(direction: 'prev' | 'next') {
    if (!selectedWeek) return
    const currentWeekDate = parseLocalIsoDate(selectedWeek)
    // For previous: land one day before this week's start so the backend resolves
    // the correct prior week (handles transitions between different week-start weekdays).
    // For next: land 7 days ahead which is inside the next week under normal rules.
    const targetDate = new Date(currentWeekDate)
    targetDate.setDate(currentWeekDate.getDate() + (direction === 'prev' ? -1 : 7))
    try {
      const config = await api.getCurrentWeekConfig(toLocalIsoDate(targetDate))
      let newWeekStart = config.week_start_date
      // For 'next': at a config transition boundary the +7 target resolves back to
      // the current week (the transition overlap). Advance one more day to cross
      // into the genuine next week.
      if (direction === 'next' && newWeekStart === selectedWeek) {
        const advancedDate = new Date(targetDate)
        advancedDate.setDate(targetDate.getDate() + 1)
        const advancedConfig = await api.getCurrentWeekConfig(toLocalIsoDate(advancedDate))
        newWeekStart = advancedConfig.week_start_date
      }
      if (newWeekStart) {
        setSelectedWeek(newWeekStart)
        await loadAccountability(newWeekStart)
      }
    } catch {
      // Fallback: plain 7-day offset
      const fallback = toLocalIsoDate(targetDate)
      setSelectedWeek(fallback)
      await loadAccountability(fallback)
    }
  }

  // NEW: Toggle expansion for a player
  function togglePlayerExpanded(player: string) {
    setExpandedPlayers(prev => ({
      ...prev,
      [player]: !prev[player]
    }))
  }

  if (loading || !selectedWeek) {
    return <LoadingState componentName="accountability check" />
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <CardTitle>Accountability Check</CardTitle>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-sm text-muted-foreground">Week start date {formatDate(selectedWeek)}</span>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigateWeek('prev')}
              >
                Previous Week
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => { setSelectedWeek(currentWeekStart); if (currentWeekStart) loadAccountability(currentWeekStart) }}
                disabled={isCurrentWeek(selectedWeek, currentWeekStart)}
              >
                Current Week
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigateWeek('next')}
                disabled={isCurrentWeek(selectedWeek, currentWeekStart)}
              >
                Next Week
              </Button>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 p-4">
        {error && (
          <div className="text-sm text-destructive pb-2">
            Failed to load accountability data.{' '}
            <button className="underline" onClick={() => loadAccountability(selectedWeek)}>Retry</button>
          </div>
        )}
        <div className="space-y-2">
          {dataLoading ? (
            <div className="text-sm text-muted-foreground py-6 text-center">Loading...</div>
          ) : accountabilityData.map((player) => (
            <div key={player.player_name} className="space-y-2">
              {/* Player summary - clickable to expand */}
              <div
                className="flex items-center justify-between p-3 rounded-lg border cursor-pointer hover:bg-accent transition-colors"
                onClick={() => togglePlayerExpanded(player.player_name)}
              >
                <div className="flex items-center gap-3">
                  {/* Expansion icon */}
                  {expandedPlayers[player.player_name] ? (
                    <ChevronDown className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  )}

                  {/* Status icon */}
                  {player.all_champions_played ? (
                    <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                      <Check className="w-4 h-4 text-white" />
                    </div>
                  ) : (
                    <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center">
                      <X className="w-4 h-4 text-white" />
                    </div>
                  )}

                  <div>
                    <div className="font-medium">{player.player_name}</div>
                    <div className="text-sm text-muted-foreground">
                      {player.champions_played} / {player.total_champions} champions played
                    </div>
                  </div>
                </div>
              </div>

              {/* NEW: Expanded champion details */}
              {expandedPlayers[player.player_name] && player.champion_details.length > 0 && (
                <div className="ml-9 space-y-2 border-l-2 border-muted pl-4">
                  {/* Total games summary */}
                  <div className="text-sm font-medium text-muted-foreground pb-1 border-b">
                    Total games this week: {player.champion_details.reduce((sum, champ) => sum + champ.games_played, 0)}
                  </div>
                  {/* Champion breakdown */}
                  <div className="space-y-1">
                    {player.champion_details.map((champ) => (
                      <div
                        key={champ.champion_name}
                        className="flex items-center gap-2 text-sm"
                      >
                        {champ.has_played ? (
                          <Check className="w-4 h-4 text-green-500" />
                        ) : (
                          <X className="w-4 h-4 text-red-500" />
                        )}
                        <span className={champ.has_played ? 'text-foreground' : 'text-muted-foreground'}>
                          {champ.champion_name}
                        </span>
                        {champ.has_played && (
                          <span className="text-xs text-muted-foreground">
                            ({champ.games_played} {champ.games_played === 1 ? 'game' : 'games'})
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Show message if no champion pool data */}
              {expandedPlayers[player.player_name] && player.champion_details.length === 0 && (
                <div className="ml-9 text-sm text-muted-foreground italic border-l-2 border-muted pl-4">
                  No champion pool configured
                </div>
              )}
            </div>
          ))}
          {!dataLoading && accountabilityData.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              No data available
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
