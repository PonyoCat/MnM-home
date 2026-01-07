import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { ErrorState, LoadingState } from './ui/error-state'
import { Button } from './ui/button'
import { Eye, EyeOff } from 'lucide-react'
import { API_URL } from '@/lib/api'

interface ChampionPoolEntry {
  id: number
  player_name: string
  champion_name: string
  description: string
  pick_priority: string
}

interface WeeklyChampionEntry {
  id: number
  player_name: string
  champion_name: string
  played: boolean
  week_start_date: string
  archived_at?: string | null
}

interface DebugData {
  week_start: string
  champion_pools: ChampionPoolEntry[]
  weekly_champions: WeeklyChampionEntry[]
}

export function AccountabilityDebug() {
  const [debugData, setDebugData] = useState<DebugData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [isVisible, setIsVisible] = useState(false)

  async function loadDebugData() {
    try {
      setLoading(true)
      setError(null)
      const response = await fetch(`${API_URL}/api/accountability/debug`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      const data = await response.json()
      setDebugData(data)
      setIsVisible(true)
    } catch (error) {
      console.error('Error loading debug data:', error)
      setError(error as Error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Database Verification</CardTitle>
        <Button
          variant="outline"
          size="sm"
          onClick={() => (isVisible ? setIsVisible(false) : loadDebugData())}
          disabled={loading}
        >
          {isVisible ? (
            <>
              <EyeOff className="w-4 h-4 mr-2" />
              Hide Debug Data
            </>
          ) : (
            <>
              <Eye className="w-4 h-4 mr-2" />
              Show Debug Data
            </>
          )}
        </Button>
      </CardHeader>

      {isVisible && (
        <CardContent className="space-y-6">
          {loading && <LoadingState componentName="debug data" />}

          {error && <ErrorState error={error} onRetry={loadDebugData} />}

          {debugData && (
            <>
              <div>
                <div className="text-sm font-medium text-muted-foreground mb-2">
                  Current Week: {debugData.week_start}
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-2">Champion Pools ({debugData.champion_pools.length} entries)</h4>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-muted">
                      <tr>
                        <th className="text-left p-2">Player</th>
                        <th className="text-left p-2">Champion</th>
                        <th className="text-left p-2">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {debugData.champion_pools.map((entry) => (
                        <tr key={entry.id} className="border-t">
                          <td className="p-2">{entry.player_name}</td>
                          <td className="p-2 font-medium">{entry.champion_name}</td>
                          <td className="p-2 text-muted-foreground">{entry.description || '—'}</td>
                        </tr>
                      ))}
                      {debugData.champion_pools.length === 0 && (
                        <tr>
                          <td colSpan={3} className="p-4 text-center text-muted-foreground">
                            No champion pool entries found
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-2">
                  Weekly Champions - Week of {debugData.week_start} ({debugData.weekly_champions.length} entries)
                </h4>
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-muted">
                      <tr>
                        <th className="text-left p-2">Player</th>
                        <th className="text-left p-2">Champion</th>
                        <th className="text-left p-2">Played</th>
                        <th className="text-left p-2">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {debugData.weekly_champions.map((entry) => (
                        <tr key={entry.id} className="border-t">
                          <td className="p-2">{entry.player_name}</td>
                          <td className="p-2 font-medium">{entry.champion_name}</td>
                          <td className="p-2">
                            {entry.played ? (
                              <span className="text-green-600 font-medium">✓ Played</span>
                            ) : (
                              <span className="text-muted-foreground">Not played</span>
                            )}
                          </td>
                          <td className="p-2">
                            {entry.archived_at ? (
                              <span className="text-xs text-muted-foreground">
                                Archived: {new Date(entry.archived_at).toLocaleDateString()}
                              </span>
                            ) : (
                              <span className="text-xs text-green-600 font-medium">Active</span>
                            )}
                          </td>
                        </tr>
                      ))}
                      {debugData.weekly_champions.length === 0 && (
                        <tr>
                          <td colSpan={4} className="p-4 text-center text-muted-foreground">
                            No weekly champion entries found for this week
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="p-4 bg-muted/50 rounded-lg text-sm">
                <p className="font-medium mb-2">How Accountability is Calculated:</p>
                <ol className="space-y-1 list-decimal list-inside text-muted-foreground">
                  <li>For each player, get all champions from Champion Pools</li>
                  <li>Check if player has at least 1 "played=true" record in Weekly Champions for each pool champion</li>
                  <li>Player gets ✓ if ALL their pool champions have been played this week</li>
                  <li>Player gets ✗ if ANY pool champion is missing or not played</li>
                </ol>
              </div>
            </>
          )}
        </CardContent>
      )}
    </Card>
  )
}
