import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog'
import { Pencil, Check, X, Calendar } from 'lucide-react'
import { api } from '@/lib/api'
import type { ClashDates } from '@/types/api.types'

/**
 * Creates a Google Calendar URL for adding an event with reminders
 * Note: Google Calendar URL doesn't support custom reminders, but users can edit after adding
 */
function createGoogleCalendarUrl(title: string, dateStr: string): string {
  // Parse the date and create all-day event
  const date = new Date(dateStr)

  // Format as YYYYMMDD for all-day event
  const startDate = date.toISOString().split('T')[0].replace(/-/g, '')

  // End date is the next day for all-day events
  const endDate = new Date(date)
  endDate.setDate(endDate.getDate() + 1)
  const endDateStr = endDate.toISOString().split('T')[0].replace(/-/g, '')

  const params = new URLSearchParams({
    action: 'TEMPLATE',
    text: title,
    dates: `${startDate}/${endDateStr}`,
    details: 'MnM Clash event - Husk at sætte påmindelser: 1 time før, 1 dag før, og 2 dage før!',
  })

  return `https://calendar.google.com/calendar/render?${params.toString()}`
}

interface ClashRotation {
  months: number[]
  name: string
  period: string
}

const CLASH_ROTATION: ClashRotation[] = [
  { months: [1, 2], name: 'Sinus', period: 'Januar - Februar' },
  { months: [3, 4, 5], name: 'FN', period: 'Marts - Maj' },
  { months: [6, 7, 8], name: 'Alex 2', period: 'Juni - August' },
  { months: [9, 10], name: 'Elias', period: 'September - Oktober' },
  { months: [11, 12], name: 'Hans', period: 'November - December' },
]

function formatDate(dateStr: string | null): string {
  if (!dateStr) return 'Ukendt'

  const date = new Date(dateStr)
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  // If date has passed, return Ukendt
  if (date < today) {
    return 'Ukendt'
  }

  // Format as "dd. MMM" (e.g., "15. Feb")
  return date.toLocaleDateString('da-DK', { day: 'numeric', month: 'short' })
}

function isDateValid(dateStr: string | null): boolean {
  if (!dateStr) return false
  const date = new Date(dateStr)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date >= today
}

export function ClashInfo() {
  const [clashDates, setClashDates] = useState<ClashDates | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editDate1, setEditDate1] = useState('')
  const [editDate2, setEditDate2] = useState('')
  const [loading, setLoading] = useState(true)
  const [calendarDialogOpen, setCalendarDialogOpen] = useState(false)

  // Function to open Google Calendar with selected date
  function addToCalendar(dateStr: string) {
    const url = createGoogleCalendarUrl('VIGTIG: MnM clash', dateStr)
    window.open(url, '_blank')
    setCalendarDialogOpen(false)
  }

  // JavaScript months are 0-indexed, add 1 for our 1-indexed array
  const currentMonth = new Date().getMonth() + 1
  const current = CLASH_ROTATION.find(r => r.months.includes(currentMonth))

  useEffect(() => {
    loadClashDates()
  }, [])

  async function loadClashDates() {
    try {
      const data = await api.getClashDates()
      setClashDates(data)
    } catch (error) {
      console.error('Failed to load clash dates:', error)
    } finally {
      setLoading(false)
    }
  }

  function startEditing() {
    setEditDate1(clashDates?.date1 || '')
    setEditDate2(clashDates?.date2 || '')
    setIsEditing(true)
  }

  async function saveChanges() {
    try {
      const date1 = editDate1 || null
      const date2 = editDate2 || null
      const updated = await api.updateClashDates(date1, date2)
      setClashDates(updated)
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to save clash dates:', error)
    }
  }

  function cancelEditing() {
    setIsEditing(false)
  }

  // Get display text for clash dates
  const date1Display = formatDate(clashDates?.date1 ?? null)
  const date2Display = formatDate(clashDates?.date2 ?? null)

  const hasValidDate1 = isDateValid(clashDates?.date1 ?? null)
  const hasValidDate2 = isDateValid(clashDates?.date2 ?? null)

  let clashDatesText: string
  if (hasValidDate1 && hasValidDate2) {
    clashDatesText = `${date1Display} og ${date2Display}`
  } else if (hasValidDate1) {
    clashDatesText = date1Display
  } else if (hasValidDate2) {
    clashDatesText = date2Display
  } else {
    clashDatesText = 'Ukendt'
  }

  if (!current) {
    return null
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg">Clash Info</CardTitle>
          {!isEditing ? (
            <Button variant="ghost" size="icon" onClick={startEditing}>
              <Pencil className="h-4 w-4" />
            </Button>
          ) : (
            <div className="flex gap-1">
              <Button variant="ghost" size="icon" onClick={saveChanges}>
                <Check className="h-4 w-4 text-green-600" />
              </Button>
              <Button variant="ghost" size="icon" onClick={cancelEditing}>
                <X className="h-4 w-4 text-red-600" />
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Next Clash Dates - BIG TEXT */}
        <div className="text-center py-4 bg-muted/50 rounded-lg">
          <div className="text-sm text-muted-foreground mb-1">Næste clash datoer</div>
          {isEditing ? (
            <div className="flex gap-2 justify-center items-center px-4 flex-wrap">
              <Input
                type="date"
                value={editDate1}
                onChange={(e) => setEditDate1(e.target.value)}
                className="w-36"
              />
              <span className="text-muted-foreground">og</span>
              <Input
                type="date"
                value={editDate2}
                onChange={(e) => setEditDate2(e.target.value)}
                className="w-36"
              />
            </div>
          ) : (
            <div className="text-3xl md:text-4xl font-bold text-primary">
              {loading ? '...' : clashDatesText}
            </div>
          )}
          {/* Add to Calendar button */}
          {(hasValidDate1 || hasValidDate2) && !isEditing && (
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => setCalendarDialogOpen(true)}
            >
              <Calendar className="h-4 w-4 mr-2" />
              Tilføj til kalender
            </Button>
          )}
        </div>

        {/* Clash Ansvarlig section */}
        <div className="border-t pt-4">
          <div className="text-sm text-muted-foreground mb-1">Ansvarlig</div>
          <div className="text-2xl font-bold">{current.name}</div>
          <div className="text-sm text-muted-foreground">{current.period}</div>
        </div>
      </CardContent>

      {/* Calendar Date Selection Dialog */}
      <Dialog open={calendarDialogOpen} onOpenChange={setCalendarDialogOpen}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Vælg dato til kalender</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-4">
            <p className="text-sm text-muted-foreground">
              Vælg hvilken clash dato du vil tilføje til din Google Kalender:
            </p>
            {hasValidDate1 && clashDates?.date1 && (
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => addToCalendar(clashDates.date1!)}
              >
                <Calendar className="h-4 w-4 mr-2" />
                {date1Display}
              </Button>
            )}
            {hasValidDate2 && clashDates?.date2 && (
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => addToCalendar(clashDates.date2!)}
              >
                <Calendar className="h-4 w-4 mr-2" />
                {date2Display}
              </Button>
            )}
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setCalendarDialogOpen(false)}>
              Annuller
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}
