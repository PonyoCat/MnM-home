import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Textarea } from './ui/textarea'
import { Button } from './ui/button'
import { ErrorState, LoadingState } from './ui/error-state'
import { api } from '@/lib/api'

export function WeeklyMessage() {
  const [message, setMessage] = useState('')
  const [isSaved, setIsSaved] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    loadMessage()
  }, [])

  async function loadMessage() {
    try {
      setIsLoading(true)
      setError(null)
      const data = await api.getWeeklyMessage()
      setMessage(data.message)
    } catch (error) {
      console.error('Error loading weekly message:', error)
      setError(error as Error)
    } finally {
      setIsLoading(false)
    }
  }

  async function handleSave() {
    try {
      setIsSaving(true)
      setError(null)
      await api.updateWeeklyMessage(message)
      setIsSaved(true)
      setTimeout(() => setIsSaved(false), 2000)
    } catch (error) {
      console.error('Error saving weekly message:', error)
      setError(error as Error)
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading && !error) {
    return <LoadingState componentName="weekly message" />
  }

  if (error) {
    return <ErrorState error={error} onRetry={loadMessage} componentName="weekly message" />
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle>Weekly Message</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 flex-1">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Add a message for the team this week..."
          className="min-h-[200px]"
          disabled={isSaving}
        />
        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Saving...' : isSaved ? 'Saved!' : 'Save Message'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
