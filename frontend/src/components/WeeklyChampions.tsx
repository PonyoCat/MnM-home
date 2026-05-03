import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Button } from './ui/button'
import { ErrorState, LoadingState } from './ui/error-state'
import { api } from '@/lib/api'
import type { MatchHistory, SyncAllResult } from '@/types/api.types'

const PLAYERS = ['Alex', 'Hans', 'Elias', 'Mikkel', 'Sinus']

function toLocalIsoDate(value: Date): string {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, '0')
  const day = String(value.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getFallbackWeekStart(): string {
  const now = new Date()
  const referenceDate = new Date(now)
  // Reset happens at end-of-Thursday, so Thursday still belongs to outgoing week.
  // Use yesterday as the reference date to emulate a 23:59 reset with date-only math.
  referenceDate.setDate(referenceDate.getDate() - 1)
  const dayOfWeek = referenceDate.getDay()
  const thursday = new Date(referenceDate)
  const daysBack = (dayOfWeek - 4 + 7) % 7
  thursday.setDate(referenceDate.getDate() - daysBack)
  return toLocalIsoDate(thursday)
}

function formatRelativeTime(iso: string | null): string {
  if (!iso) return 'never'
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return 'never'
  const diffSec = Math.floor((Date.now() - then) / 1000)
  if (diffSec < 60) return 'just now'
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} min ago`
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} h ago`
  return `${Math.floor(diffSec / 86400)} d ago`
}

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

function formatMatchDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function WeeklyChampions() {
  const [matchHistory, setMatchHistory] = useState<Record<string, MatchHistory[]>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [weekStart, setWeekStart] = useState<string | null>(null)
  const [expandedPlayers, setExpandedPlayers] = useState<Record<string, boolean>>(
    Object.fromEntries(PLAYERS.map(p => [p, false]))
  )

  const [playerPools, setPlayerPools] = useState<Record<string, Set<string>>>({})

  // Sync state
  const [syncingAll, setSyncingAll] = useState(false)
  const [syncSummary, setSyncSummary] = useState<SyncAllResult | null>(null)
  const [syncError, setSyncError] = useState<string | null>(null)
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null)

  useEffect(() => {
    initializeData()
  }, [])

  useEffect(() => {
    if (weekStart) loadPools(weekStart)
  }, [weekStart])

  async function loadPools(targetWeekStart: string) {
    try {
      const pools = await api.getChampionPools(undefined, targetWeekStart) as { player_name: string; champion_name: string; disabled: boolean }[]
      const grouped: Record<string, Set<string>> = {}
      for (const entry of pools) {
        if (entry.disabled) continue
        if (!grouped[entry.player_name]) grouped[entry.player_name] = new Set()
        grouped[entry.player_name].add(entry.champion_name)
      }
      setPlayerPools(grouped)
    } catch {
      // fail silently — count will fall back to all ranked games
    }
  }

  async function initializeData() {
    const fallbackWeekStart = getFallbackWeekStart()
    let resolvedWeekStart = fallbackWeekStart

    try {
      const [currentWeekConfig, lastSync] = await Promise.all([
        api.getCurrentWeekConfig(),
        api.getLastSync(),
      ])
      resolvedWeekStart = currentWeekConfig.week_start_date || fallbackWeekStart
      setLastSyncedAt(lastSync.last_synced_at)
    } catch (error) {
      console.error('Error loading week config / last sync, using fallback:', error)
    }

    setWeekStart(resolvedWeekStart)
    await loadData(resolvedWeekStart)
  }

  async function loadData(targetWeekStart: string) {
    try {
      setLoading(true)
      setError(null)
      const results = await Promise.allSettled(
        PLAYERS.map(p => api.getPlayerMatches(p, targetWeekStart))
      )
      const history: Record<string, MatchHistory[]> = {}
      results.forEach((result, i) => {
        if (result.status === 'fulfilled') {
          history[PLAYERS[i]] = result.value
        }
      })
      setMatchHistory(history)
    } catch (error) {
      console.error('Error loading weekly games:', error)
      setError(error as Error)
    } finally {
      setLoading(false)
    }
  }

  async function loadMatchHistory(player: string) {
    try {
      const matches = await api.getPlayerMatches(player, weekStart ?? undefined)
      setMatchHistory(prev => ({ ...prev, [player]: matches }))
    } catch (error) {
      console.error(`Error loading match history for ${player}:`, error)
    }
  }

  async function runSync() {
    setSyncingAll(true)
    setSyncError(null)
    setSyncSummary(null)
    try {
      const result = await api.syncAllPlayerGames(weekStart ?? undefined)
      setSyncSummary(result)
      setLastSyncedAt(result.finished_at)
      // Refresh data and match history for expanded players
      if (weekStart) {
        await loadData(weekStart)
        const refreshTargets = Object.keys(expandedPlayers).filter(p => expandedPlayers[p])
        await Promise.all(refreshTargets.map(p => loadMatchHistory(p)))
      }
    } catch (e) {
      const err = e as Error & { status?: number }
      if (err.status === 409) {
        setSyncError('Sync already in progress')
      } else if (err.status === 502) {
        setSyncError('Riot API unreachable or API key invalid')
      } else if (err.status === 429) {
        setSyncError('Riot API rate limit exceeded -- try again in a minute')
      } else {
        setSyncError(`Sync failed: ${err.message ?? 'unknown error'}`)
      }
    } finally {
      setSyncingAll(false)
    }
  }


  async function togglePlayerExpanded(player: string) {
    const willExpand = !expandedPlayers[player]
    setExpandedPlayers(prev => ({ ...prev, [player]: willExpand }))
    if (willExpand && !matchHistory[player]) {
      await loadMatchHistory(player)
    }
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
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle>Weekly Games</CardTitle>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground" title={lastSyncedAt ?? 'never'}>
              Last synced: {formatRelativeTime(lastSyncedAt)}
            </span>
            <Button
              size="sm"
              onClick={runSync}
              disabled={syncingAll}
            >
              {syncingAll ? 'Syncing...' : 'Update Stats'}
            </Button>
          </div>
        </div>
        {syncSummary && (
          <div className="mt-2 rounded-md border border-green-300 bg-green-50 p-2 text-sm text-green-900 dark:bg-green-950 dark:text-green-100">
            Synced {syncSummary.total_games_synced} new games across{' '}
            {syncSummary.per_player.length - syncSummary.failed_players.length} players
            {syncSummary.failed_players.length > 0 && (
              <span className="ml-1 text-red-700 dark:text-red-400">
                (failed: {syncSummary.failed_players.join(', ')})
              </span>
            )}
          </div>
        )}
        {syncError && (
          <div className="mt-2 rounded-md border border-red-300 bg-red-50 p-2 text-sm text-red-900 dark:bg-red-950 dark:text-red-100">
            {syncError}
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-6 flex-1">
        {PLAYERS.map(player => {
          const matches = matchHistory[player] ?? []
          const pool = playerPools[player]
          const poolGames = matches.filter(
            m => !m.user_excluded && m.queue_id === 420 && (!pool || pool.has(m.champion_name))
          ).length

          return (
            <div key={player} className="space-y-2">
              <h3
                className="font-semibold text-lg cursor-pointer hover:text-primary transition-colors flex items-center gap-2"
                onClick={() => togglePlayerExpanded(player)}
              >
                <span>{expandedPlayers[player] ? '▼' : '▶'}</span>
                {player}
                {matches.length > 0 && (
                  <span className="text-sm font-normal text-muted-foreground">
                    {poolGames} ranked game{poolGames !== 1 ? 's' : ''}
                  </span>
                )}
              </h3>
              {expandedPlayers[player] && (
                <div className="space-y-2">

                  {/* Match history section - current week only */}
                  <div className="rounded-md border border-border overflow-hidden">
                    <div className="flex items-center gap-2 px-3 py-2 text-sm font-medium">
                      Match History
                    </div>
                    <div className="border-t border-border">
                        {matches.length === 0 ? (
                          <p className="text-xs text-muted-foreground px-3 py-2">
                            No matches synced yet.
                          </p>
                        ) : (
                          <div className="divide-y divide-border">
                            {matches.map(m => {
                              const excluded = m.user_excluded || m.queue_id !== 420
                              return (
                                <div
                                  key={m.id}
                                  className={`grid grid-cols-[2rem_1fr_4rem_4rem_3rem_3rem] items-center gap-x-3 px-3 py-2 text-sm ${excluded ? 'opacity-50' : m.won ? 'bg-green-50 dark:bg-green-950/30' : 'bg-red-50 dark:bg-red-950/30'}`}
                                  title={m.user_excluded ? 'Excluded' : m.queue_id !== 420 ? `Queue ${m.queue_id} (not ranked)` : ''}
                                >
                                  <span className={`font-bold text-xs text-center ${m.won ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                                    {m.won ? 'W' : 'L'}
                                  </span>
                                  <span className="font-medium truncate">{m.champion_name}</span>
                                  <span className="text-muted-foreground text-xs text-center tabular-nums">
                                    {m.kills}/{m.deaths}/{m.assists}
                                  </span>
                                  <span className="text-muted-foreground text-xs text-center tabular-nums">
                                    {m.cs} CS
                                  </span>
                                  <span className="text-muted-foreground text-xs text-center tabular-nums">
                                    {formatDuration(m.game_duration_seconds)}
                                  </span>
                                  <span className="text-muted-foreground text-xs text-right">
                                    {formatMatchDate(m.game_start_time)}
                                  </span>
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
