import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Button } from './ui/button'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from './ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel
} from './ui/alert-dialog'
import { ErrorState, LoadingState } from './ui/error-state'
import { api } from '@/lib/api'
import type {
  ChampionPool,
  ExcludedFriend,
  FullSyncStatus,
  MatchHistory,
  Player,
  SyncAllResult,
} from '@/types/api.types'

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

export function ChampionPoolList() {
  const [players, setPlayers] = useState<Player[]>([])
  const [playerPools, setPlayerPools] = useState<Record<string, ChampionPool[]>>({})
  const [matchHistory, setMatchHistory] = useState<Record<string, MatchHistory[]>>({})
  const [excludedFriends, setExcludedFriends] = useState<ExcludedFriend[]>([])
  const [friendsError, setFriendsError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [expandedPlayers, setExpandedPlayers] = useState<Record<string, boolean>>({})
  const [showHistoryFor, setShowHistoryFor] = useState<Record<string, boolean>>({})

  // Riot ID inputs (controlled per player)
  const [riotIdInputs, setRiotIdInputs] = useState<Record<string, string>>({})
  const [savingRiotId, setSavingRiotId] = useState<Record<string, boolean>>({})

  // Excluded friend add input
  const [friendInput, setFriendInput] = useState<string>('')

  // Quick sync state
  const [syncingAll, setSyncingAll] = useState(false)
  const [syncSummary, setSyncSummary] = useState<SyncAllResult | null>(null)
  const [syncError, setSyncError] = useState<string | null>(null)
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null)

  // Full sync (background) state
  const [fullSyncing, setFullSyncing] = useState(false)
  const [showFullSyncConfirm, setShowFullSyncConfirm] = useState(false)
  const fullSyncToastId = useRef<string | number | null>(null)
  const fullSyncInterval = useRef<ReturnType<typeof setInterval> | null>(null)

  // Form state for adding champion
  const [newChampion, setNewChampion] = useState({
    player: '',
    name: '',
    description: '',
    pickPriority: ''
  })

  // Edit state
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingPool, setEditingPool] = useState<ChampionPool | null>(null)
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    pickPriority: ''
  })

  // Delete state
  const [deleteConfirmText, setDeleteConfirmText] = useState('')
  const [poolToDelete, setPoolToDelete] = useState<ChampionPool | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)

  useEffect(() => {
    initializeData()
  }, [])

  async function initializeData() {
    try {
      setLoading(true)
      setError(null)

      const [playerList, lastSync] = await Promise.all([
        api.getPlayers(),
        api.getLastSync(),
      ])
      setPlayers(playerList)
      const names = playerList.map((p) => p.player_name)
      setExpandedPlayers(Object.fromEntries(names.map((n) => [n, false])))
      setRiotIdInputs(Object.fromEntries(playerList.map((p) => [p.player_name, p.riot_id ?? ''])))
      setLastSyncedAt(lastSync.last_synced_at)

      await loadPools(names)
      await loadExcludedFriends()
    } catch (e) {
      console.error('Error loading players/pools:', e)
      setError(e as Error)
    } finally {
      setLoading(false)
    }
  }

  async function loadPools(playerNames: string[] = players.map((p) => p.player_name)) {
    try {
      setError(null)
      const data = await api.getChampionPools()
      const grouped = playerNames.reduce((acc, player) => {
        acc[player] = data.filter((p: ChampionPool) => p.player_name === player)
        return acc
      }, {} as Record<string, ChampionPool[]>)
      setPlayerPools(grouped)
    } catch (e) {
      console.error('Error loading champion pools:', e)
      setError(e as Error)
    }
  }

  async function loadMatchHistory(playerName: string) {
    try {
      const matches = await api.getPlayerMatches(playerName)
      setMatchHistory((prev) => ({ ...prev, [playerName]: matches }))
    } catch (e) {
      console.error(`Failed to load matches for ${playerName}:`, e)
    }
  }

  async function loadExcludedFriends() {
    try {
      setFriendsError(null)
      const friends = await api.getExcludedFriendsGlobal()
      setExcludedFriends(friends)
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Failed to load excluded friends'
      console.error('Failed to load excluded friends:', e)
      setFriendsError(msg)
    }
  }

  async function addChampion(player: string) {
    if (!newChampion.name.trim()) return
    try {
      await api.createChampionPool({
        player_name: player,
        champion_name: newChampion.name.trim(),
        description: newChampion.description.trim(),
        pick_priority: newChampion.pickPriority.trim()
      })
      setNewChampion({ player: '', name: '', description: '', pickPriority: '' })
      await loadPools()
    } catch (e) {
      console.error('Error adding champion:', e)
    }
  }

  function openEditDialog(pool: ChampionPool) {
    setEditingPool(pool)
    setEditForm({
      name: pool.champion_name,
      description: pool.description,
      pickPriority: pool.pick_priority
    })
    setEditDialogOpen(true)
  }

  async function updateChampion() {
    if (!editingPool) return
    try {
      await api.updateChampionPool(editingPool.id, {
        champion_name: editForm.name,
        description: editForm.description,
        pick_priority: editForm.pickPriority
      })
      setEditDialogOpen(false)
      setEditingPool(null)
      await loadPools()
    } catch (e) {
      console.error('Error updating champion:', e)
    }
  }

  async function deleteChampion() {
    if (!poolToDelete) return
    const expectedText = `Delete ${poolToDelete.champion_name}`
    if (deleteConfirmText !== expectedText) return
    try {
      await api.deleteChampionPool(poolToDelete.id)
      setDeleteDialogOpen(false)
      setPoolToDelete(null)
      setDeleteConfirmText('')
      await loadPools()
    } catch (e) {
      console.error('Error deleting champion:', e)
    }
  }

  async function toggleDisabled(pool: ChampionPool) {
    try {
      await api.updateChampionPool(pool.id, { disabled: !pool.disabled })
      await loadPools()
    } catch (e) {
      console.error('Error toggling champion disabled state:', e)
    }
  }

  async function togglePlayerExpanded(playerName: string) {
    const willExpand = !expandedPlayers[playerName]
    setExpandedPlayers((prev) => ({ ...prev, [playerName]: willExpand }))
    if (willExpand && !excludedFriends[playerName]) {
      await loadExcludedFriends(playerName)
    }
  }

  async function toggleHistory(playerName: string) {
    const willShow = !showHistoryFor[playerName]
    setShowHistoryFor((prev) => ({ ...prev, [playerName]: willShow }))
    if (willShow && !matchHistory[playerName]) {
      await loadMatchHistory(playerName)
    }
  }

  async function saveRiotId(playerName: string) {
    const value = (riotIdInputs[playerName] ?? '').trim()
    if (!value || !value.includes('#')) {
      alert('Riot ID must be in "Name#Tag" format')
      return
    }
    setSavingRiotId((prev) => ({ ...prev, [playerName]: true }))
    try {
      const updated = await api.updatePlayer(playerName, { riot_id: value })
      setPlayers((prev) =>
        prev.map((p) => (p.player_name === playerName ? updated : p))
      )
    } catch (e) {
      console.error('Failed to save Riot ID:', e)
      alert('Failed to save Riot ID')
    } finally {
      setSavingRiotId((prev) => ({ ...prev, [playerName]: false }))
    }
  }

  async function addFriendGlobal() {
    const value = friendInput.trim()
    if (!value || !value.includes('#')) {
      toast.error('Friend Riot ID must be in "Name#Tag" format')
      return
    }
    try {
      const added = await api.addExcludedFriendGlobal({ riot_id: value })
      setFriendInput('')
      setExcludedFriends((prev) => [...prev, added])
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Failed to add excluded friend'
      toast.error(msg)
      console.error('Failed to add excluded friend:', e)
    }
  }

  async function removeFriend(friendId: number) {
    try {
      await api.removeExcludedFriendGlobal(friendId)
      await loadExcludedFriends()
    } catch (e) {
      console.error('Failed to remove friend:', e)
    }
  }

  function stopFullSyncPolling() {
    if (fullSyncInterval.current !== null) {
      clearInterval(fullSyncInterval.current)
      fullSyncInterval.current = null
    }
    setFullSyncing(false)
  }

  function startFullSyncPolling(runId: number) {
    setFullSyncing(true)
    const toastId = toast.loading('Full sync running... starting', { duration: Infinity })
    fullSyncToastId.current = toastId

    fullSyncInterval.current = setInterval(async () => {
      let statusData: FullSyncStatus
      try {
        statusData = await api.getFullSyncStatus(runId)
      } catch {
        return // transient fetch error, keep polling
      }

      const p = statusData.progress
      if (statusData.status === 'running') {
        if (p) {
          toast.loading(
            `Full sync running... ${p.players_done}/${p.players_total} players \u2014 ${p.games_synced_so_far} games synced${p.current_player ? ` (${p.current_player})` : ''}`,
            { id: toastId, duration: Infinity },
          )
        }
        return
      }

      // Terminal state
      stopFullSyncPolling()
      const r = statusData.result
      if (statusData.status === 'success') {
        toast.success(
          `Full sync done \u2014 ${r?.total_games_synced ?? 0} new games, ${r?.total_games_found ?? 0} found`,
          { id: toastId, duration: 8000 },
        )
        if (r?.finished_at) setLastSyncedAt(r.finished_at)
      } else if (statusData.status === 'partial') {
        toast.warning(
          `Full sync partial \u2014 ${r?.total_games_synced ?? 0} games synced, failed: ${r?.failed_players?.join(', ') ?? 'some players'}`,
          { id: toastId, duration: 10000 },
        )
        if (r?.finished_at) setLastSyncedAt(r.finished_at)
      } else {
        const perPlayerErrors = r?.per_player
          ?.filter((p: { message?: string }) => p.message?.startsWith('Failed:'))
          .map((p: { player_name: string; message: string }) => `${p.player_name}: ${p.message.replace('Failed: ', '')}`)
          .join(' | ')
        toast.error(
          `Full sync failed \u2014 ${r?.message ?? statusData.status}${perPlayerErrors ? ` (${perPlayerErrors})` : ''}`,
          { id: toastId, duration: 10000 },
        )
      }
    }, 4000)
  }

  async function runFullSync() {
    if (fullSyncing) return
    setShowFullSyncConfirm(true)
  }

  async function confirmFullSync() {
    setShowFullSyncConfirm(false)
    try {
      const started = await api.startFullSync()
      startFullSyncPolling(started.run_id)
    } catch (e) {
      const err = e as Error & { status?: number }
      if (err.status === 409) {
        toast.error('Full sync already in progress')
      } else if (err.status === 502) {
        toast.error('Riot API unreachable or API key invalid')
      } else {
        toast.error(`Full sync failed to start: ${err.message ?? 'unknown error'}`)
      }
    }
  }

  async function runSync() {
    setSyncingAll(true)
    setSyncError(null)
    setSyncSummary(null)
    try {
      const result = await api.syncAllPlayerGames()
      setSyncSummary(result)
      setLastSyncedAt(result.finished_at)
      // Refresh match history for any expanded players
      const refreshTargets = Object.keys(showHistoryFor).filter((p) => showHistoryFor[p])
      await Promise.all(refreshTargets.map((p) => loadMatchHistory(p)))
    } catch (e) {
      const err = e as Error & { status?: number }
      console.error('Sync failed:', err)
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

  if (loading && !error) {
    return <LoadingState componentName="player info" />
  }
  if (error) {
    return <ErrorState error={error} onRetry={initializeData} componentName="player info" />
  }

  const noRiotIds = players.every((p) => !p.riot_id)

  return (
    <>
      {/* Top header bar with single Update Stats button */}
      <Card className="mb-4">
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle>Player Info</CardTitle>
            <div className="flex items-center gap-3">
              <span
                className="text-sm text-muted-foreground"
                title={lastSyncedAt ?? 'never'}
              >
                Last synced: {formatRelativeTime(lastSyncedAt)}
              </span>
              <Button
                variant="outline"
                onClick={runFullSync}
                disabled={fullSyncing || noRiotIds}
                title={noRiotIds ? 'No players have a Riot ID set' : fullSyncing ? 'Full sync in progress' : 'Fetch full match history for all players'}
              >
                {fullSyncing ? 'Full Sync...' : 'Full Sync'}
              </Button>
              <Button
                onClick={runSync}
                disabled={syncingAll || noRiotIds}
                title={noRiotIds ? 'No players have a Riot ID set' : ''}
              >
                {syncingAll ? 'Syncing...' : 'Update Stats'}
              </Button>
            </div>
          </div>
          {syncSummary && (
            <div className="mt-3 rounded-md border border-green-300 bg-green-50 p-2 text-sm text-green-900 dark:bg-green-950 dark:text-green-100">
              Synced {syncSummary.total_games_synced} new games across{' '}
              {syncSummary.per_player.length - syncSummary.failed_players.length} players
              ({syncSummary.total_games_excluded} excluded by eligibility,{' '}
              {syncSummary.total_games_already_present} already counted,{' '}
              {syncSummary.total_games_found} total found)
              {syncSummary.failed_players.length > 0 && (
                <div className="mt-1 text-red-700 dark:text-red-400">
                  Failed: {syncSummary.failed_players.join(', ')}
                </div>
              )}
            </div>
          )}
          {syncError && (
            <div className="mt-3 rounded-md border border-red-300 bg-red-50 p-2 text-sm text-red-900 dark:bg-red-950 dark:text-red-100">
              {syncError}
            </div>
          )}
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Champion Pools</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {players.map((player) => {
            const name = player.player_name
            const isExpanded = expandedPlayers[name]
            const matches = matchHistory[name] ?? []
            const showHistory = showHistoryFor[name]

            return (
              <div key={name} className="space-y-3">
                <h3
                  className="font-semibold text-lg cursor-pointer hover:text-primary transition-colors flex items-center gap-2"
                  onClick={() => togglePlayerExpanded(name)}
                >
                  <span>{isExpanded ? '▼' : '▶'}</span>
                  {name}
                  {player.riot_id && (
                    <span className="text-xs text-muted-foreground font-normal">
                      ({player.riot_id})
                    </span>
                  )}
                </h3>

                {isExpanded && (
                  <>
                    {/* Riot ID Section */}
                    <div className="rounded-md border border-border p-3 space-y-2">
                      <div className="text-sm font-medium">Riot ID</div>
                      <div className="flex gap-2">
                        <Input
                          placeholder="Name#Tag (e.g. Ponyo#Meeps)"
                          value={riotIdInputs[name] ?? ''}
                          onChange={(e) =>
                            setRiotIdInputs((prev) => ({ ...prev, [name]: e.target.value }))
                          }
                        />
                        <Button
                          onClick={() => saveRiotId(name)}
                          disabled={savingRiotId[name]}
                        >
                          {savingRiotId[name] ? 'Saving...' : 'Save'}
                        </Button>
                      </div>
                      {!player.riot_id && (
                        <div className="text-xs text-muted-foreground">Not set</div>
                      )}
                    </div>

                    {/* Match History Section */}
                    <div className="rounded-md border border-border p-3 space-y-2">
                      <div
                        className="flex items-center gap-2 cursor-pointer text-sm font-medium"
                        onClick={() => toggleHistory(name)}
                      >
                        <span>{showHistory ? '\u25bc' : '\u25b6'}</span>
                        Match History
                      </div>
                      {showHistory && (
                        <>
                          {matches.length === 0 ? (
                            <div className="text-xs text-muted-foreground">
                              No matches synced yet.
                            </div>
                          ) : (
                            <Table>
                              <TableHeader>
                                <TableRow>
                                  <TableHead>Champion</TableHead>
                                  <TableHead>Result</TableHead>
                                  <TableHead>KDA</TableHead>
                                  <TableHead>CS</TableHead>
                                  <TableHead>Vision</TableHead>
                                  <TableHead>Gold</TableHead>
                                  <TableHead>Damage</TableHead>
                                  <TableHead>Role</TableHead>
                                  <TableHead>Duration</TableHead>
                                </TableRow>
                              </TableHeader>
                              <TableBody>
                                {matches.map((m) => {
                                  const greyed = m.user_excluded || m.queue_id !== 420
                                  return (
                                    <TableRow
                                      key={m.id}
                                      className={
                                        greyed
                                          ? 'opacity-50'
                                          : m.won
                                          ? 'bg-green-50 dark:bg-green-950/30'
                                          : 'bg-red-50 dark:bg-red-950/30'
                                      }
                                      title={
                                        m.user_excluded
                                          ? 'Manually excluded'
                                          : m.queue_id !== 420
                                          ? `Queue ${m.queue_id} (not ranked solo/duo)`
                                          : ''
                                      }
                                    >
                                      <TableCell className="font-medium">
                                        {m.champion_name}
                                      </TableCell>
                                      <TableCell>
                                        {m.won ? 'Win' : 'Loss'}
                                      </TableCell>
                                      <TableCell>
                                        {m.kills}/{m.deaths}/{m.assists}
                                      </TableCell>
                                      <TableCell>{m.cs}</TableCell>
                                      <TableCell>{m.vision_score}</TableCell>
                                      <TableCell>{m.gold_earned.toLocaleString()}</TableCell>
                                      <TableCell>
                                        {m.damage_to_champions.toLocaleString()}
                                      </TableCell>
                                      <TableCell>{m.team_position ?? '-'}</TableCell>
                                      <TableCell>
                                        {formatDuration(m.game_duration_seconds)}
                                      </TableCell>
                                    </TableRow>
                                  )
                                })}
                              </TableBody>
                            </Table>
                          )}
                        </>
                      )}
                    </div>

                    {/* Add champion form */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
                      <Input
                        placeholder="Champion name..."
                        value={newChampion.player === name ? newChampion.name : ''}
                        onChange={(e) =>
                          setNewChampion({
                            player: name,
                            name: e.target.value,
                            description: newChampion.player === name ? newChampion.description : '',
                            pickPriority: newChampion.player === name ? newChampion.pickPriority : ''
                          })
                        }
                      />
                      <Input
                        placeholder="Description..."
                        value={newChampion.player === name ? newChampion.description : ''}
                        onChange={(e) =>
                          setNewChampion({
                            player: name,
                            name: newChampion.player === name ? newChampion.name : '',
                            description: e.target.value,
                            pickPriority: newChampion.player === name ? newChampion.pickPriority : ''
                          })
                        }
                      />
                      <Input
                        placeholder="Pick priority..."
                        value={newChampion.player === name ? newChampion.pickPriority : ''}
                        onChange={(e) =>
                          setNewChampion({
                            player: name,
                            name: newChampion.player === name ? newChampion.name : '',
                            description: newChampion.player === name ? newChampion.description : '',
                            pickPriority: e.target.value
                          })
                        }
                      />
                      <Button onClick={() => addChampion(name)}>Add</Button>
                    </div>

                    {/* Champion table */}
                    {(playerPools[name] ?? []).length > 0 && (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Champion</TableHead>
                            <TableHead>Description</TableHead>
                            <TableHead>Pick Priority</TableHead>
                            <TableHead>Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {(playerPools[name] ?? []).map((pool) => (
                            <TableRow key={pool.id} className={pool.disabled ? 'opacity-50' : ''}>
                              <TableCell className="font-medium">
                                {pool.champion_name}
                                {pool.disabled && (
                                  <span className="ml-2 text-xs text-muted-foreground">(disabled)</span>
                                )}
                              </TableCell>
                              <TableCell>{pool.description}</TableCell>
                              <TableCell>{pool.pick_priority}</TableCell>
                              <TableCell>
                                <div className="flex gap-2">
                                  <Button size="sm" onClick={() => openEditDialog(pool)}>
                                    Edit
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => toggleDisabled(pool)}
                                  >
                                    {pool.disabled ? 'Enable' : 'Disable'}
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="destructive"
                                    onClick={() => {
                                      setPoolToDelete(pool)
                                      setDeleteConfirmText('')
                                      setDeleteDialogOpen(true)
                                    }}
                                  >
                                    Delete
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </>
                )}
              </div>
            )
          })}
        </CardContent>
      </Card>

      {/* Excluded Friends Card */}
      <Card className="mt-4">
        <CardHeader>
          <CardTitle>Excluded Friends</CardTitle>
          <p className="text-sm text-muted-foreground pt-1">
            Games queued with these Riot IDs on your team won't count toward accountability for anyone. Changes take effect on the next sync.
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          {friendsError && (
            <div className="rounded-md border border-red-300 bg-red-50 p-2 text-sm text-red-900 dark:bg-red-950 dark:text-red-100 flex items-center justify-between">
              <span>Failed to load: {friendsError}</span>
              <Button size="sm" variant="outline" onClick={loadExcludedFriends}>Retry</Button>
            </div>
          )}
          {!friendsError && excludedFriends.length === 0 && (
            <div className="text-sm text-muted-foreground">No excluded friends added yet.</div>
          )}
          {excludedFriends.map((f) => (
            <div key={f.id} className="flex items-center gap-2 text-sm">
              <span>{f.riot_id}</span>
              {f.puuid ? (
                <span
                  className="text-xs text-green-600"
                  title={`PUUID: ${f.puuid}`}
                >
                  PUUID verified
                </span>
              ) : (
                <span
                  className="text-xs text-amber-600"
                  title="PUUID not yet resolved — will be looked up on next sync"
                >
                  No PUUID match
                </span>
              )}
              <Button
                size="sm"
                variant="outline"
                className="ml-auto"
                onClick={() => removeFriend(f.id)}
              >
                Remove
              </Button>
            </div>
          ))}
          <div className="flex gap-2 pt-2">
            <Input
              placeholder="FriendName#Tag"
              value={friendInput}
              onChange={(e) => setFriendInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') addFriendGlobal()
              }}
            />
            <Button onClick={addFriendGlobal}>
              Add
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Champion</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Champion Name</label>
              <Input
                value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                placeholder="Champion name..."
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Description</label>
              <Textarea
                value={editForm.description}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                placeholder="When/why to pick this champion..."
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Pick Priority</label>
              <Textarea
                value={editForm.pickPriority}
                onChange={(e) => setEditForm({ ...editForm, pickPriority: e.target.value })}
                placeholder="Pick strategy notes..."
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={updateChampion}>Save Changes</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete AlertDialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Champion</AlertDialogTitle>
            <AlertDialogDescription>
              Type "Delete {poolToDelete?.champion_name}" to confirm deletion. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="py-4">
            <Input
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              placeholder={poolToDelete ? `Delete ${poolToDelete.champion_name}` : ''}
              autoFocus
            />
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel
              onClick={() => {
                setDeleteDialogOpen(false)
                setPoolToDelete(null)
                setDeleteConfirmText('')
              }}
            >
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={deleteChampion}
              disabled={deleteConfirmText !== `Delete ${poolToDelete?.champion_name}`}
            >
              Confirm Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={showFullSyncConfirm} onOpenChange={setShowFullSyncConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Run Full Historical Sync?</AlertDialogTitle>
            <AlertDialogDescription>
              This will fetch the complete match history for all players going as far back as possible.
              A full sync can take upwards of multiple hours depending on how many games exist.
              The sync runs in the background — you can close this page and check back later.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmFullSync}>Start Full Sync</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
