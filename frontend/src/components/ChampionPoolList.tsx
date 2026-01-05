import { useEffect, useState } from 'react'
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
import { api } from '@/lib/api'
import type { ChampionPool } from '@/types/api.types'

const PLAYERS = ['Alex', 'Hans', 'Elias', 'Mikkel', 'Sinus']

export function ChampionPoolList() {
  const [playerPools, setPlayerPools] = useState<Record<string, ChampionPool[]>>({
    Alex: [], Hans: [], Elias: [], Mikkel: [], Sinus: []
  })
  const [loading, setLoading] = useState(true)
  const [expandedPlayers, setExpandedPlayers] = useState<Record<string, boolean>>({
    Alex: false, Hans: false, Elias: false, Mikkel: false, Sinus: false
  })

  // Form state for adding
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
    loadPools()
  }, [])

  async function loadPools() {
    try {
      const data = await api.getChampionPools()
      const grouped = PLAYERS.reduce((acc, player) => {
        acc[player] = data.filter((p: ChampionPool) => p.player_name === player)
        return acc
      }, {} as Record<string, ChampionPool[]>)
      setPlayerPools(grouped)
    } catch (error) {
      console.error('Error loading champion pools:', error)
    } finally {
      setLoading(false)
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
    } catch (error) {
      console.error('Error adding champion:', error)
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
    } catch (error) {
      console.error('Error updating champion:', error)
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
    } catch (error) {
      console.error('Error deleting champion:', error)
    }
  }

  function togglePlayerExpanded(player: string) {
    setExpandedPlayers(prev => ({ ...prev, [player]: !prev[player] }))
  }

  if (loading) {
    return <Card><CardContent className="pt-6">Loading...</CardContent></Card>
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Champion Pools</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {PLAYERS.map(player => (
            <div key={player} className="space-y-3">
              <h3
                className="font-semibold text-lg cursor-pointer hover:text-primary transition-colors flex items-center gap-2"
                onClick={() => togglePlayerExpanded(player)}
              >
                <span>{expandedPlayers[player] ? '▼' : '▶'}</span>
                {player}
              </h3>

              {expandedPlayers[player] && (
                <>
                  {/* Add form */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-2">
                    <Input
                      placeholder="Champion name..."
                      value={newChampion.player === player ? newChampion.name : ''}
                      onChange={(e) => setNewChampion({
                        player,
                        name: e.target.value,
                        description: newChampion.player === player ? newChampion.description : '',
                        pickPriority: newChampion.player === player ? newChampion.pickPriority : ''
                      })}
                    />
                    <Input
                      placeholder="Description..."
                      value={newChampion.player === player ? newChampion.description : ''}
                      onChange={(e) => setNewChampion({
                        player,
                        name: newChampion.player === player ? newChampion.name : '',
                        description: e.target.value,
                        pickPriority: newChampion.player === player ? newChampion.pickPriority : ''
                      })}
                    />
                    <Input
                      placeholder="Pick priority..."
                      value={newChampion.player === player ? newChampion.pickPriority : ''}
                      onChange={(e) => setNewChampion({
                        player,
                        name: newChampion.player === player ? newChampion.name : '',
                        description: newChampion.player === player ? newChampion.description : '',
                        pickPriority: e.target.value
                      })}
                    />
                    <Button onClick={() => addChampion(player)}>Add</Button>
                  </div>

                  {/* Table */}
                  {playerPools[player].length > 0 && (
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
                        {playerPools[player].map(pool => (
                          <TableRow key={pool.id}>
                            <TableCell className="font-medium">{pool.champion_name}</TableCell>
                            <TableCell>{pool.description}</TableCell>
                            <TableCell>{pool.pick_priority}</TableCell>
                            <TableCell>
                              <div className="flex gap-2">
                                <Button size="sm" onClick={() => openEditDialog(pool)}>
                                  Edit
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
          ))}
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
            <Button onClick={updateChampion}>
              Save Changes
            </Button>
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
            <AlertDialogCancel onClick={() => {
              setDeleteDialogOpen(false)
              setPoolToDelete(null)
              setDeleteConfirmText('')
            }}>
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
    </>
  )
}
