import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Textarea } from './ui/textarea'
import { Button } from './ui/button'
import { api } from '@/lib/api'

export function WeeklyMessage() {
  const [message, setMessage] = useState('')
  const [isSaved, setIsSaved] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
      setError('Failed to load message')
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
      setError('Failed to save message')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle>Weekly Message</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 flex-1">
        {error && (
          <div className="text-red-500 text-sm">{error}</div>
        )}
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Add a message for the team this week..."
          className="min-h-[200px]"
          disabled={isLoading || isSaving}
        />
        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={isLoading || isSaving}>
            {isSaving ? 'Saving...' : isSaved ? 'Saved!' : 'Save Message'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
