import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Textarea } from './ui/textarea'
import { Button } from './ui/button'
import { ErrorState, LoadingState } from './ui/error-state'
import { Pencil } from 'lucide-react'
import { api } from '@/lib/api'

export function WeeklyMessage() {
  const [message, setMessage] = useState('')
  const [isEditing, setIsEditing] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    loadMessage()
  }, [])

  // Auto-resize textarea when message changes
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea && isEditing) {
      // Reset height to auto to get the correct scrollHeight for shrinking
      textarea.style.height = 'auto'
      // Set height to scrollHeight to fit content
      textarea.style.height = `${textarea.scrollHeight}px`
    }
  }, [message, isEditing])

  async function loadMessage() {
    try {
      setIsLoading(true)
      setError(null)
      const data = await api.getWeeklyMessage()
      setMessage(data.message)
    } catch (error) {
      console.error('Error loading message board:', error)
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
      setIsEditing(false)
    } catch (error) {
      console.error('Error saving message board:', error)
      setError(error as Error)
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading && !error) {
    return <LoadingState componentName="message board" />
  }

  if (error) {
    return <ErrorState error={error} onRetry={loadMessage} componentName="message board" />
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg text-foreground">Message Board</CardTitle>
          {!isEditing && (
            <Button variant="ghost" size="icon" onClick={() => setIsEditing(true)}>
              <Pencil className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4 flex-1">
        {isEditing ? (
          <>
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Share an update for the team... (supports Markdown)"
              disabled={isSaving}
              className="min-h-[100px] resize-none overflow-hidden text-lg"
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setIsEditing(false)} disabled={isSaving}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? 'Saving...' : 'Save'}
              </Button>
            </div>
          </>
        ) : (
          <div className="markdown-content bg-muted/50 rounded-lg p-4 text-foreground/80">
            {message ? (
              <ReactMarkdown
                components={{
                  h1: ({ children }) => <h1 className="text-3xl font-bold mb-4 text-foreground/80">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-2xl font-bold mb-3 text-foreground/80">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-xl font-bold mb-2 text-foreground/80">{children}</h3>,
                  h4: ({ children }) => <h4 className="text-lg font-semibold mb-2 text-foreground/80">{children}</h4>,
                  p: ({ children }) => <p className="text-base mb-2">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                  li: ({ children }) => <li className="text-base">{children}</li>,
                  strong: ({ children }) => <strong className="font-bold">{children}</strong>,
                  em: ({ children }) => <em className="italic">{children}</em>,
                  code: ({ children }) => <code className="bg-muted px-1 py-0.5 rounded text-sm">{children}</code>,
                }}
              >
                {message}
              </ReactMarkdown>
            ) : (
              <p className="text-muted-foreground italic">No posts yet. Click edit to add one.</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
