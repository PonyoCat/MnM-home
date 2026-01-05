import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Textarea } from './ui/textarea'
import { Button } from './ui/button'

export function WeeklyMessage() {
  const [message, setMessage] = useState('')
  const [isSaved, setIsSaved] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('weeklyMessage')
    if (saved) {
      setMessage(saved)
    }
  }, [])

  const handleSave = () => {
    localStorage.setItem('weeklyMessage', message)
    setIsSaved(true)
    setTimeout(() => setIsSaved(false), 2000)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Weekly Message</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Add a message for the team this week..."
          className="min-h-[200px]"
        />
        <div className="flex justify-end">
          <Button onClick={handleSave}>
            {isSaved ? 'Saved!' : 'Save Message'}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
