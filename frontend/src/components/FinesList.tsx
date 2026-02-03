import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { ErrorState, LoadingState } from './ui/error-state'
import { ChevronDown, ChevronRight, Trash2 } from 'lucide-react'
import { api } from '@/lib/api'
import type { PlayerFinesSummary } from '@/types/api.types'

const FINE_RULES = {
  info: [
    'Informer omkring aflysning senest 1 uge før',
    'Informer om delays i god tid (Så godt du kan)',
  ],
  rules: [
    '10 kr per 30 min for sent (Op til 30 kr max)',
    '10 kr per scrim game misset (Op til 30 kr max)',
    '10 kr for at misse soloQ quota',
    'Op til 20 kr per champ man har misset. Udregnet med (*C/20 kr)',
  ],
}

const PLAYERS = ['Alex', 'Hans', 'Elias', 'Mikkel', 'Sinus']

export function FinesList() {
  const [fines, setFines] = useState<PlayerFinesSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [expandedPlayers, setExpandedPlayers] = useState<Set<string>>(new Set())

  // Form state
  const [selectedPlayer, setSelectedPlayer] = useState(PLAYERS[0])
  const [reason, setReason] = useState('')
  const [amount, setAmount] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    loadFines()
  }, [])

  async function loadFines() {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getFines()
      setFines(data)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }

  async function handleAddFine() {
    if (!reason.trim() || !amount) return

    try {
      setIsSubmitting(true)
      await api.createFine({
        player_name: selectedPlayer,
        reason: reason.trim(),
        amount: parseInt(amount, 10),
      })
      setReason('')
      setAmount('')
      await loadFines()
    } catch (err) {
      console.error('Failed to add fine:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleDeleteFine(fineId: number) {
    try {
      await api.deleteFine(fineId)
      await loadFines()
    } catch (err) {
      console.error('Failed to delete fine:', err)
    }
  }

  function togglePlayer(playerName: string) {
    setExpandedPlayers(prev => {
      const next = new Set(prev)
      if (next.has(playerName)) {
        next.delete(playerName)
      } else {
        next.add(playerName)
      }
      return next
    })
  }

  // Calculate grand total
  const grandTotal = fines.reduce((sum, p) => sum + p.total_amount, 0)

  if (loading && !error) {
    return <LoadingState componentName="fines" />
  }

  if (error) {
    return <ErrorState error={error} onRetry={loadFines} componentName="fines" />
  }

  return (
    <div className="space-y-6">
      {/* Fine Rules Card */}
      <Card>
        <CardHeader>
          <CardTitle>Bødekasse Regler</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold mb-2">Information</h4>
            <ul className="list-disc pl-5 text-sm text-muted-foreground">
              {FINE_RULES.info.map((rule, i) => (
                <li key={i}>{rule}</li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-2">Bøder</h4>
            <ul className="list-disc pl-5 text-sm text-muted-foreground">
              {FINE_RULES.rules.map((rule, i) => (
                <li key={i}>{rule}</li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Add Fine Form */}
      <Card>
        <CardHeader>
          <CardTitle>Tilføj Bøde</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 flex-wrap">
            <select
              value={selectedPlayer}
              onChange={(e) => setSelectedPlayer(e.target.value)}
              className="border rounded px-3 py-2 bg-background text-foreground"
            >
              {PLAYERS.map(player => (
                <option key={player} value={player}>{player}</option>
              ))}
            </select>
            <Input
              placeholder="Årsag (reason)"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="flex-1 min-w-[200px]"
            />
            <Input
              type="number"
              placeholder="Beløb (kr)"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-24"
            />
            <Button onClick={handleAddFine} disabled={isSubmitting || !reason.trim() || !amount}>
              {isSubmitting ? 'Tilføjer...' : 'Tilføj'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Fines List by Player */}
      <Card>
        <CardHeader>
          <CardTitle className="flex justify-between">
            <span>Bøder</span>
            <span className="text-primary">Total: {grandTotal} kr</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {/* Show all players, even those without fines */}
            {PLAYERS.map(playerName => {
              const playerData = fines.find(f => f.player_name === playerName)
              const total = playerData?.total_amount || 0
              const playerFines = playerData?.fines || []
              const isExpanded = expandedPlayers.has(playerName)

              return (
                <div key={playerName} className="border rounded">
                  <button
                    onClick={() => togglePlayer(playerName)}
                    className="w-full flex items-center justify-between p-3 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-2">
                      {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      <span className="font-medium">{playerName}</span>
                    </div>
                    <span className={total > 0 ? 'text-destructive font-semibold' : 'text-muted-foreground'}>
                      {total} kr
                    </span>
                  </button>

                  {isExpanded && playerFines.length > 0 && (
                    <div className="border-t px-3 py-2 space-y-2">
                      {playerFines.map(fine => (
                        <div key={fine.id} className="flex items-center justify-between text-sm">
                          <div className="flex-1">
                            <span>{fine.reason}</span>
                            <span className="text-muted-foreground ml-2">({fine.amount} kr)</span>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteFine(fine.id)}
                            className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}

                  {isExpanded && playerFines.length === 0 && (
                    <div className="border-t px-3 py-2 text-sm text-muted-foreground">
                      Ingen bøder
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
