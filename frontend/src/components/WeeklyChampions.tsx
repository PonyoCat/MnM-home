import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Button } from './ui/button'
import { ErrorState, LoadingState } from './ui/error-state'
import { api } from '@/lib/api'
import type { WeeklyChampion, ChampionPool } from '@/types/api.types'

const PLAYERS = ['Alex', 'Hans', 'Elias', 'Mikkel', 'Sinus']

function toLocalIsoDate(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getFallbackWeekStart(): string {
  const now = new Date()
  const dayOfWeek = now.getDay()
  const thursday = new Date(now)
  // Calculate days back to Thursday (day 4)
  // Thursday=0 days, Friday=1 day, ..., Monday=4 days, Tuesday=5 days, Wednesday=6 days
  const daysBack = (dayOfWeek - 4 + 7) % 7
  thursday.setDate(now.getDate() - daysBack)
  return toLocalIsoDate(thursday)
}

export function WeeklyChampions() {
  const [playerChampions, setPlayerChampions] = useState<Record<string, WeeklyChampion[]>>({
    Alex: [], Hans: [], Elias: [], Mikkel: [], Sinus: []
  })
  const [championPools, setChampionPools] = useState<Record<string, ChampionPool[]>>({
    Alex: [], Hans: [], Elias: [], Mikkel: [], Sinus: []
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [weekStart, setWeekStart] = useState<string | null>(null)
  const [expandedPlayers, setExpandedPlayers] = useState<Record<string, boolean>>({
    Alex: false, Hans: false, Elias: false, Mikkel: false, Sinus: false
  })

  useEffect(() => {
    initializeData()
  }, [])

  async function initializeData() {
    const fallbackWeekStart = getFallbackWeekStart()
    let resolvedWeekStart = fallbackWeekStart

    try {
      const currentWeekConfig = await api.getCurrentWeekConfig()
      resolvedWeekStart = currentWeekConfig.week_start_date || fallbackWeekStart
    } catch (error) {
      console.error('Error loading week config, using fallback:', error)
    }

    setWeekStart(resolvedWeekStart)
    await loadData(resolvedWeekStart)
  }

  async function loadData(targetWeekStart: string) {
    try {
      setLoading(true)
      setError(null)

      // Fetch both champion pools and weekly champions
      const [poolsData, championsData] = await Promise.all([
        api.getChampionPools(undefined, targetWeekStart),
        api.getWeeklyChampions(targetWeekStart)
      ])

      // Group champion pools by player
      const groupedPools = PLAYERS.reduce((acc, player) => {
        acc[player] = poolsData.filter((c: ChampionPool) => c.player_name === player)
        return acc
      }, {} as Record<string, ChampionPool[]>)
      setChampionPools(groupedPools)

      // Group weekly champions by player
      const groupedChampions = PLAYERS.reduce((acc, player) => {
        acc[player] = championsData.filter((c: WeeklyChampion) => c.player_name === player)
        return acc
      }, {} as Record<string, WeeklyChampion[]>)
      setPlayerChampions(groupedChampions)
    } catch (error) {
      console.error('Error loading weekly games:', error)
      setError(error as Error)
    } finally {
      setLoading(false)
    }
  }

  async function incrementChampion(player: string, championName: string) {
    if (!weekStart) return

    try {
      await api.toggleWeeklyChampion({
        player_name: player,
        champion_name: championName,
        played: true,
        week_start_date: weekStart
      })
      await loadData(weekStart)
    } catch (error) {
      console.error('Error incrementing game count:', error)
    }
  }

  async function decrementChampion(player: string, championName: string, currentCount: number) {
    if (currentCount === 0 || !weekStart) return

    try {
      if (currentCount === 1) {
        // If going from 1 to 0, delete the played instance (leaves the pool placeholder intact)
        await api.deleteOneWeeklyChampionInstance(player, championName, weekStart, true)
      } else {
        // If count is > 1, delete one played instance
        await api.deleteOneWeeklyChampionInstance(player, championName, weekStart, true)
      }
      await loadData(weekStart)
    } catch (error) {
      console.error('Error decrementing game count:', error)
    }
  }

  function getChampionCount(player: string, championName: string): number {
    return playerChampions[player].filter(
      c => c.champion_name === championName && c.played
    ).length
  }

  function getPlayerChampions(player: string): string[] {
    // Get non-disabled champions from the player's champion pool
    return championPools[player]
      .filter(c => !c.disabled)
      .map(c => c.champion_name)
      .sort((a, b) => a.localeCompare(b))
  }

  function togglePlayerExpanded(player: string) {
    setExpandedPlayers(prev => ({
      ...prev,
      [player]: !prev[player]
    }))
  }

  if (loading && !error) {
    return <LoadingState componentName="weekly games" />
  }

  if (error) {
    return <ErrorState error={error} onRetry={initializeData} componentName="weekly games" />
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle>Weekly Games</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6 flex-1">
        {PLAYERS.map(player => {
          const playerChampionList = getPlayerChampions(player)
          return (
            <div key={player} className="space-y-2">
              <h3
                className="font-semibold text-lg cursor-pointer hover:text-primary transition-colors flex items-center gap-2"
                onClick={() => togglePlayerExpanded(player)}
              >
                <span>{expandedPlayers[player] ? '▼' : '▶'}</span>
                {player}
              </h3>
              {expandedPlayers[player] && (
                <div className="space-y-2">
                  {playerChampionList.length === 0 ? (
                    <p className="text-sm text-muted-foreground italic px-3 py-2">
                      No champions in pool. Add champions in the Champion Pool page.
                    </p>
                  ) : (
                    playerChampionList.map(championName => {
                      const playCount = getChampionCount(player, championName)
                      return (
                        <div
                          key={championName}
                          className="flex items-center justify-between bg-accent px-3 py-2 rounded-md"
                        >
                          <span className="font-medium">{championName}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-lg font-bold w-8 text-center">{playCount}</span>
                            <div className="flex gap-1">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => incrementChampion(player, championName)}
                              >
                                +1
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => decrementChampion(player, championName, playCount)}
                                disabled={playCount === 0}
                              >
                                -1
                              </Button>
                            </div>
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>
              )}
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
