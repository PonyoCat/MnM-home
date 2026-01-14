import { useEffect, useState } from 'react'
import { formatDate } from '@/lib/utils'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Textarea } from './ui/textarea'
import { Button } from './ui/button'
import { ErrorState, LoadingState } from './ui/error-state'
import { api } from '@/lib/api'
import type { DraftNote } from '@/types/api.types'

export function DraftNotes() {
  const [notes, setNotes] = useState('')
  const [lastUpdated, setLastUpdated] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    loadNotes()
  }, [])

  async function loadNotes() {
    try {
      setLoading(true)
      setError(null)
      const data: DraftNote = await api.getDraftNotes()
      setNotes(data.notes)
      setLastUpdated(data.last_updated)
    } catch (error) {
      console.error('Error loading draft notes:', error)
      setError(error as Error)
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

  if (loading && !error) {
    return <LoadingState componentName="draft notes" />
  }

  if (error) {
    return <ErrorState error={error} onRetry={loadNotes} componentName="draft notes" />
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
              Last updated: {formatDate(lastUpdated)} {new Date(lastUpdated).toLocaleTimeString()}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
