import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Input } from './ui/input'
import { Button } from './ui/button'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from './ui/table'
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel
} from './ui/alert-dialog'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from './ui/dialog'
import { ErrorState, LoadingState } from './ui/error-state'
import { api } from '@/lib/api'
import type { PickStat } from '@/types/api.types'

export function PickStats() {
  const [stats, setStats] = useState<PickStat[]>([])
  const [newChampion, setNewChampion] = useState('')
  const [deleteConfirmText, setDeleteConfirmText] = useState('')
  const [championToDelete, setChampionToDelete] = useState<PickStat | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [editingStat, setEditingStat] = useState<PickStat | null>(null)
  const [editChampionName, setEditChampionName] = useState('')
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [sortBy, setSortBy] = useState<'win_rate' | 'games'>('win_rate')

  useEffect(() => {
    loadStats()
  }, [])

  async function loadStats() {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getPickStats()
      const sorted = sortBy === 'win_rate'
        ? data.sort((a: PickStat, b: PickStat) => b.win_rate - a.win_rate)
        : data.sort((a: PickStat, b: PickStat) => b.first_pick_games - a.first_pick_games)
      setStats(sorted)
    } catch (error) {
      console.error('Error loading pick stats:', error)
      setError(error as Error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!loading) {
      loadStats()
    }
  }, [sortBy])

  async function addChampion() {
    if (!newChampion.trim()) return
    try {
      await api.createPickStat(newChampion.trim())
      setNewChampion('')
      await loadStats()
    } catch (error) {
      console.error('Error adding champion:', error)
    }
  }

  async function handleWin(id: number) {
    try {
      await api.addWin(id)
      await loadStats()
    } catch (error) {
      console.error('Error adding win:', error)
    }
  }

  async function handleLoss(id: number) {
    try {
      await api.addLoss(id)
      await loadStats()
    } catch (error) {
      console.error('Error adding loss:', error)
    }
  }

  async function handleDelete() {
    if (!championToDelete) return

    const expectedText = `Delete ${championToDelete.champion_name}`
    if (deleteConfirmText !== expectedText) {
      return
    }

    try {
      await api.deletePickStat(championToDelete.id)
      setChampionToDelete(null)
      setDeleteConfirmText('')
      await loadStats()
    } catch (error) {
      console.error('Error deleting champion:', error)
    }
  }

  async function handleEditChampion() {
    if (!editingStat || !editChampionName.trim()) return
    try {
      await api.updatePickStatChampion(editingStat.id, editChampionName.trim())
      setEditDialogOpen(false)
      setEditingStat(null)
      setEditChampionName('')
      await loadStats()
    } catch (error: any) {
      console.error('Error editing champion:', error)
      alert(error.message || 'Failed to update champion name')
    }
  }

  const filteredStats = stats.filter(stat =>
    stat.champion_name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (loading && !error) {
    return <LoadingState componentName="pick statistics" />
  }

  if (error) {
    return <ErrorState error={error} onRetry={loadStats} componentName="pick statistics" />
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pick Statistics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search champions..."
            className="flex-1"
          />
          <Button
            variant={sortBy === 'win_rate' ? 'default' : 'outline'}
            onClick={() => setSortBy('win_rate')}
          >
            Win %
          </Button>
          <Button
            variant={sortBy === 'games' ? 'default' : 'outline'}
            onClick={() => setSortBy('games')}
          >
            Games
          </Button>
        </div>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Champion</TableHead>
              <TableHead>Games</TableHead>
              <TableHead>Wins</TableHead>
              <TableHead>Win %</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredStats.map(stat => (
              <TableRow key={stat.id}>
                <TableCell className="font-medium">{stat.champion_name}</TableCell>
                <TableCell>{stat.first_pick_games}</TableCell>
                <TableCell>{stat.first_pick_wins}</TableCell>
                <TableCell>{stat.win_rate.toFixed(1)}%</TableCell>
                <TableCell>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => handleWin(stat.id)}>
                      Win
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => handleLoss(stat.id)}>
                      Loss
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditingStat(stat)
                        setEditChampionName(stat.champion_name)
                        setEditDialogOpen(true)
                      }}
                    >
                      Edit
                    </Button>
                    <AlertDialog
                      onOpenChange={(open) => {
                        if (!open) {
                          setChampionToDelete(null)
                          setDeleteConfirmText('')
                        }
                      }}
                    >
                      <AlertDialogTrigger asChild>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => {
                            setChampionToDelete(stat)
                            setDeleteConfirmText('')
                          }}
                        >
                          Delete
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete Champion</AlertDialogTitle>
                          <AlertDialogDescription>
                            Type "Delete {stat.champion_name}" to confirm deletion. This action cannot be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <div className="py-4">
                          <Input
                            value={deleteConfirmText}
                            onChange={(e) => setDeleteConfirmText(e.target.value)}
                            placeholder={`Delete ${stat.champion_name}`}
                            autoFocus
                          />
                        </div>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            onClick={handleDelete}
                            disabled={deleteConfirmText !== `Delete ${stat.champion_name}`}
                          >
                            Confirm Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <div className="flex gap-2 pt-4 border-t">
          <Input
            value={newChampion}
            onChange={(e) => setNewChampion(e.target.value)}
            placeholder="Add new champion..."
            onKeyDown={(e) => e.key === 'Enter' && addChampion()}
          />
          <Button onClick={addChampion}>Add Champion</Button>
        </div>

        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Champion Name</DialogTitle>
            </DialogHeader>
            <Input
              value={editChampionName}
              onChange={(e) => setEditChampionName(e.target.value)}
              placeholder="Champion name..."
              onKeyDown={(e) => e.key === 'Enter' && handleEditChampion()}
            />
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleEditChampion}>
                Save
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  )
}
