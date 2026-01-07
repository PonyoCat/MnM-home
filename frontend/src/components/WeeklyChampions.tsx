import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Input } from './ui/input'
import { Button } from './ui/button'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog'
import { ErrorState, LoadingState } from './ui/error-state'
import { api } from '@/lib/api'
import type { WeeklyChampion } from '@/types/api.types'

const PLAYERS = ['Alex', 'Hans', 'Elias', 'Mikkel', 'Sinus']

function getWeekStart(): string {
  const now = new Date()
  const dayOfWeek = now.getDay()
  const monday = new Date(now)
  monday.setDate(now.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1))
  return monday.toISOString().split('T')[0]
}

export function WeeklyChampions() {
  const [playerChampions, setPlayerChampions] = useState<Record<string, WeeklyChampion[]>>({
    Alex: [], Hans: [], Elias: [], Mikkel: [], Sinus: []
  })
  const [playerInputs, setPlayerInputs] = useState<Record<string, string>>({
    Alex: '', Hans: '', Elias: '', Mikkel: '', Sinus: ''
  })
  const [championToDelete, setChampionToDelete] = useState<{player: string, champion: string} | null>(null)
  const [deleteConfirmText, setDeleteConfirmText] = useState('')
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [expandedPlayers, setExpandedPlayers] = useState<Record<string, boolean>>({
    Alex: false, Hans: false, Elias: false, Mikkel: false, Sinus: false
  })
  const weekStart = getWeekStart()

  useEffect(() => {
    loadChampions()
  }, [])

  async function loadChampions() {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getWeeklyChampions(weekStart)
      const grouped = PLAYERS.reduce((acc, player) => {
        acc[player] = data.filter((c: WeeklyChampion) => c.player_name === player)
        return acc
      }, {} as Record<string, WeeklyChampion[]>)
      setPlayerChampions(grouped)
    } catch (error) {
      console.error('Error loading weekly games:', error)
      setError(error as Error)
    } finally {
      setLoading(false)
    }
  }

  async function addChampionForPlayer(player: string) {
    const championName = playerInputs[player].trim()
    if (!championName) return

    try {
      await api.toggleWeeklyChampion({
        player_name: player,
        champion_name: championName,
        played: false,
        week_start_date: weekStart
      })
      setPlayerInputs(prev => ({ ...prev, [player]: '' }))
      await loadChampions()
    } catch (error) {
      console.error('Error adding game:', error)
    }
  }

  async function incrementChampion(player: string, championName: string) {
    try {
      await api.toggleWeeklyChampion({
        player_name: player,
        champion_name: championName,
        played: true,
        week_start_date: weekStart
      })
      await loadChampions()
    } catch (error) {
      console.error('Error incrementing game count:', error)
    }
  }

  async function decrementChampion(player: string, championName: string, currentCount: number) {
    if (currentCount === 0) return

    try {
      if (currentCount === 1) {
        // If going from 1 to 0, toggle the last instance to played=false instead of deleting
        await api.toggleWeeklyChampion({
          player_name: player,
          champion_name: championName,
          played: false,
          week_start_date: weekStart
        })
      } else {
        // If count is > 1, delete one played instance
        await api.deleteOneWeeklyChampionInstance(player, championName, weekStart, true)
      }
      await loadChampions()
    } catch (error) {
      console.error('Error decrementing game count:', error)
    }
  }

  function getAllChampions() {
    const allChamps: Array<{player: string, champion: string}> = []
    PLAYERS.forEach(player => {
      const uniqueChamps = new Set(playerChampions[player].map(c => c.champion_name))
      uniqueChamps.forEach(champion => {
        allChamps.push({ player, champion })
      })
    })
    return allChamps
  }

  async function removeChampion() {
    if (!championToDelete) return

    const expectedText = `Delete ${championToDelete.champion}`
    if (deleteConfirmText !== expectedText) {
      return
    }

    try {
      await api.deleteWeeklyChampion(
        championToDelete.player,
        championToDelete.champion,
        weekStart
      )

      setDeleteDialogOpen(false)
      setChampionToDelete(null)
      setDeleteConfirmText('')
      await loadChampions()
    } catch (error) {
      console.error('Error removing game:', error)
    }
  }

  function getChampionCount(player: string, championName: string): number {
    return playerChampions[player].filter(
      c => c.champion_name === championName && c.played
    ).length
  }

  function getUniqueChampions(player: string): string[] {
    const uniqueChamps = new Set(playerChampions[player].map(c => c.champion_name))
    return Array.from(uniqueChamps).sort((a, b) => a.localeCompare(b))
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
    return <ErrorState error={error} onRetry={loadChampions} componentName="weekly games" />
  }

  const allChampions = getAllChampions()

  return (
    <>
      <Card className="h-full flex flex-col">
        <CardHeader>
          <CardTitle>Weekly Games (Week of {weekStart})</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 flex-1">
          {PLAYERS.map(player => (
            <div key={player} className="space-y-2">
              <h3
                className="font-semibold text-lg cursor-pointer hover:text-primary transition-colors flex items-center gap-2"
                onClick={() => togglePlayerExpanded(player)}
              >
                <span>{expandedPlayers[player] ? '▼' : '▶'}</span>
                {player}
              </h3>
              {expandedPlayers[player] && (
                <>
                  <div className="flex gap-2">
                    <Input
                      value={playerInputs[player]}
                      onChange={(e) => setPlayerInputs(prev => ({
                        ...prev,
                        [player]: e.target.value
                      }))}
                      placeholder="Champion name..."
                      onKeyDown={(e) =>
                        e.key === 'Enter' && addChampionForPlayer(player)
                      }
                    />
                    <Button onClick={() => addChampionForPlayer(player)}>
                      Add
                    </Button>
                  </div>
                  <div className="space-y-2">
                    {getUniqueChampions(player).map(championName => {
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
                    })}
                  </div>
                </>
              )}
            </div>
          ))}
          <div className="flex justify-end mt-4">
            <Button
              variant="destructive"
              onClick={() => {
                setDeleteDialogOpen(true)
                setChampionToDelete(null)
                setDeleteConfirmText('')
              }}
              disabled={allChampions.length === 0}
            >
              Remove Champion
            </Button>
          </div>
        </CardContent>
      </Card>

      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Champion</AlertDialogTitle>
            <AlertDialogDescription>
              {!championToDelete
                ? 'Select a champion to remove. You will need to confirm by typing the champion\'s name.'
                : `Type "Delete ${championToDelete.champion}" to confirm removal:`
              }
            </AlertDialogDescription>
          </AlertDialogHeader>

          {!championToDelete ? (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {allChampions.map(({ player, champion }) => (
                <Button
                  key={`${player}-${champion}`}
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setChampionToDelete({ player, champion })}
                >
                  {player}: {champion}
                </Button>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              <Input
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder={`Delete ${championToDelete.champion}`}
                autoFocus
              />
            </div>
          )}

          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => {
              setChampionToDelete(null)
              setDeleteConfirmText('')
            }}>
              Cancel
            </AlertDialogCancel>
            {championToDelete && (
              <AlertDialogAction
                onClick={removeChampion}
                disabled={deleteConfirmText !== `Delete ${championToDelete.champion}`}
              >
                Confirm Delete
              </AlertDialogAction>
            )}
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
