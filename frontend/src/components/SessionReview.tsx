import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Textarea } from './ui/textarea'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog'
import { api } from '@/lib/api'
import type { SessionReview as SessionReviewType, SessionReviewArchive } from '@/types/api.types'

export function SessionReview() {
  const [currentNotes, setCurrentNotes] = useState('')
  const [currentTitle, setCurrentTitle] = useState(() => {
    return new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  })
  const [archives, setArchives] = useState<SessionReviewArchive[]>([])
  const [selectedArchive, setSelectedArchive] = useState<SessionReviewArchive | null>(null)
  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadCurrentNotes()
    loadArchives()
  }, [])

  async function loadCurrentNotes() {
    try {
      const data: SessionReviewType = await api.getSessionReview()
      setCurrentNotes(data.notes)
    } catch (error) {
      console.error('Error loading session notes:', error)
    } finally {
      setLoading(false)
    }
  }

  async function loadArchives() {
    try {
      const data = await api.getSessionReviewArchives()
      setArchives(data)
    } catch (error) {
      console.error('Error loading archives:', error)
    }
  }

  async function archiveNotes() {
    if (!currentNotes.trim() && !currentTitle.trim()) {
      return
    }

    try {
      await api.createSessionReviewArchive(
        currentTitle,
        currentNotes,
        new Date().toISOString().split('T')[0]
      )

      // Clear current notes and reset title
      setCurrentNotes('')
      setCurrentTitle(new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      }))

      // Update the main session review to clear it
      await api.updateSessionReview('')

      // Reload archives
      await loadArchives()
    } catch (error) {
      console.error('Error archiving notes:', error)
    }
  }

  function openArchive(archive: SessionReviewArchive) {
    setSelectedArchive({ ...archive })
    setEditDialogOpen(true)
  }

  async function updateArchive() {
    if (!selectedArchive) return

    try {
      await api.updateSessionReviewArchive(
        selectedArchive.id,
        selectedArchive.title,
        selectedArchive.notes
      )

      setEditDialogOpen(false)
      await loadArchives()
    } catch (error) {
      console.error('Error updating archive:', error)
    }
  }

  if (loading) {
    return <Card><CardContent className="pt-6">Loading...</CardContent></Card>
  }

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Session Review</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            value={currentTitle}
            onChange={(e) => setCurrentTitle(e.target.value)}
            placeholder="Session title..."
          />
          <Textarea
            value={currentNotes}
            onChange={(e) => setCurrentNotes(e.target.value)}
            rows={6}
            placeholder="Add notes from this gaming session..."
          />
          <div className="flex gap-2">
            <Button onClick={archiveNotes}>Archive Session</Button>
            <Button variant="outline" onClick={() => setArchiveDialogOpen(true)}>
              View Archives
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={archiveDialogOpen} onOpenChange={setArchiveDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Session Archives</DialogTitle>
          </DialogHeader>
          <div className="max-h-96 overflow-y-auto space-y-2">
            {archives.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No archives yet. Archive your first session above!
              </p>
            ) : (
              archives.map(archive => (
                <Card
                  key={archive.id}
                  className="cursor-pointer hover:bg-accent transition-colors"
                  onClick={() => openArchive(archive)}
                >
                  <CardContent className="p-4">
                    <h4 className="font-semibold">{archive.title}</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                      Archived: {new Date(archive.archived_at).toLocaleDateString()}
                    </p>
                    <p className="text-sm mt-2 line-clamp-2">{archive.notes}</p>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Archive</DialogTitle>
          </DialogHeader>
          {selectedArchive && (
            <div className="space-y-4">
              <Input
                value={selectedArchive.title}
                onChange={(e) => setSelectedArchive({
                  ...selectedArchive,
                  title: e.target.value
                })}
                placeholder="Archive title..."
              />
              <Textarea
                value={selectedArchive.notes}
                onChange={(e) => setSelectedArchive({
                  ...selectedArchive,
                  notes: e.target.value
                })}
                rows={12}
                placeholder="Archive notes..."
              />
              <DialogFooter>
                <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={updateArchive}>Save Changes</Button>
              </DialogFooter>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
