import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Textarea } from './ui/textarea'
import { Button } from './ui/button'
import { api } from '@/lib/api'
import type { DraftNote } from '@/types/api.types'

export function DraftNotes() {
  const [notes, setNotes] = useState('')
  const [lastUpdated, setLastUpdated] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadNotes()
  }, [])

  async function loadNotes() {
    try {
      const data: DraftNote = await api.getDraftNotes()
      setNotes(data.notes)
      setLastUpdated(data.last_updated)
    } catch (error) {
      console.error('Error loading draft notes:', error)
    } finally {
      setLoading(false)
    }
  }

  async function saveNotes() {
    try {
      const data: DraftNote = await api.updateDraftNotes(notes)
      setLastUpdated(data.last_updated)
    } catch (error) {
      console.error('Error saving notes:', error)
    }
  }

  if (loading) {
    return <Card><CardContent className="pt-6">Loading...</CardContent></Card>
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Draft Notes</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={6}
          placeholder="Add draft strategy notes..."
        />
        <div className="flex items-center justify-between">
          <Button onClick={saveNotes}>Save</Button>
          {lastUpdated && (
            <p className="text-sm text-muted-foreground">
              Last updated: {new Date(lastUpdated).toLocaleString()}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
