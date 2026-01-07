import { useEffect, useState } from 'react'
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

function getCurrentWeekStart(): string {
  const now = new Date()
  const dayOfWeek = now.getDay()
  const monday = new Date(now)
  monday.setDate(now.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1))
  return monday.toISOString().split('T')[0]
}

function isCurrentWeek(weekStart: string): boolean {
  return weekStart === getCurrentWeekStart()
}

export function AccountabilityCheck() {
  const [accountabilityData, setAccountabilityData] = useState<PlayerAccountability[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [selectedWeek, setSelectedWeek] = useState(getCurrentWeekStart())

  // NEW: Track expanded state per player (mirror WeeklyChampions.tsx pattern)
  const [expandedPlayers, setExpandedPlayers] = useState<Record<string, boolean>>({
    Alex: false, Hans: false, Elias: false, Mikkel: false, Sinus: false
  })

  useEffect(() => {
    loadAccountability()
  }, [selectedWeek])

  async function loadAccountability() {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getAccountabilityCheck(selectedWeek)
      setAccountabilityData(data)
    } catch (error) {
      console.error('Error loading accountability check:', error)
      setError(error as Error)
    } finally {
      setLoading(false)
    }
  }

  function navigateWeek(dayOffset: number) {
    const currentWeekDate = new Date(selectedWeek)
    const newWeekDate = new Date(currentWeekDate)
    newWeekDate.setDate(currentWeekDate.getDate() + dayOffset)
    setSelectedWeek(newWeekDate.toISOString().split('T')[0])
  }

  // NEW: Toggle expansion for a player
  function togglePlayerExpanded(player: string) {
    setExpandedPlayers(prev => ({
      ...prev,
      [player]: !prev[player]
    }))
  }

  if (loading) {
    return <LoadingState componentName="accountability check" />
  }

  if (error) {
    return <ErrorState error={error} onRetry={loadAccountability} />
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <CardTitle>Accountability Check</CardTitle>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-sm text-muted-foreground">Week of {selectedWeek}</span>
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
                onClick={() => setSelectedWeek(getCurrentWeekStart())}
                disabled={isCurrentWeek(selectedWeek)}
              >
                Current Week
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigateWeek(7)}
                disabled={isCurrentWeek(selectedWeek)}
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
                <div className="ml-9 space-y-1 border-l-2 border-muted pl-4">
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
