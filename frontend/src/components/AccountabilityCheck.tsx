import { useEffect, useState } from 'react'
import { formatDate } from '@/lib/utils'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Button } from './ui/button'
import { ErrorState, LoadingState } from './ui/error-state'
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
  const dayOfWeek = now.getDay()
  const thursday = new Date(now)
  // Calculate days back to Thursday (day 4)
  // Thursday=0 days, Friday=1 day, ..., Monday=4 days, Tuesday=5 days, Wednesday=6 days
  const daysBack = (dayOfWeek - 4 + 7) % 7
  thursday.setDate(now.getDate() - daysBack)
  return toLocalIsoDate(thursday)
}

function isCurrentWeek(selectedWeek: string | null, currentWeekStart: string | null): boolean {
  if (!selectedWeek || !currentWeekStart) return false
  return selectedWeek === currentWeekStart
}

export function AccountabilityCheck() {
  const [accountabilityData, setAccountabilityData] = useState<PlayerAccountability[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [currentWeekStart, setCurrentWeekStart] = useState<string | null>(null)
  const [selectedWeek, setSelectedWeek] = useState<string | null>(null)

  // NEW: Track expanded state per player (mirror WeeklyChampions.tsx pattern)
  const [expandedPlayers, setExpandedPlayers] = useState<Record<string, boolean>>({
    Alex: false, Hans: false, Elias: false, Mikkel: false, Sinus: false
  })

  useEffect(() => {
    initializeWeekConfig()
  }, [])

  useEffect(() => {
    if (selectedWeek) {
      loadAccountability(selectedWeek)
    }
  }, [selectedWeek])

  async function initializeWeekConfig() {
    const fallbackWeekStart = getFallbackCurrentWeekStart()
    let resolvedWeekStart = fallbackWeekStart

    try {
      const currentWeekConfig = await api.getCurrentWeekConfig()
      resolvedWeekStart = currentWeekConfig.week_start_date || fallbackWeekStart
    } catch (error) {
      console.error('Error loading week config, using fallback:', error)
    }

    setCurrentWeekStart(resolvedWeekStart)
    setSelectedWeek(resolvedWeekStart)
  }

  async function loadAccountability(targetWeekStart: string) {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getAccountabilityCheck(targetWeekStart)
      setAccountabilityData(data)
    } catch (error) {
      console.error('Error loading accountability check:', error)
      setError(error as Error)
    } finally {
      setLoading(false)
    }
  }

  function navigateWeek(dayOffset: number) {
    if (!selectedWeek) return
    const currentWeekDate = parseLocalIsoDate(selectedWeek)
    const newWeekDate = new Date(currentWeekDate)
    newWeekDate.setDate(currentWeekDate.getDate() + dayOffset)
    setSelectedWeek(toLocalIsoDate(newWeekDate))
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

  if (error) {
    return <ErrorState error={error} onRetry={() => loadAccountability(selectedWeek)} />
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
                onClick={() => navigateWeek(-7)}
              >
                Previous Week
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setSelectedWeek(currentWeekStart)}
                disabled={isCurrentWeek(selectedWeek, currentWeekStart)}
              >
                Current Week
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigateWeek(7)}
                disabled={isCurrentWeek(selectedWeek, currentWeekStart)}
              >
                Next Week
              </Button>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 p-4">
        <div className="space-y-2">
          {accountabilityData.map((player) => (
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

          {accountabilityData.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              No data available
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
