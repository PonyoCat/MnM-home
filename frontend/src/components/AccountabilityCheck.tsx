import { useEffect, useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from './ui/card'
import { ErrorState, LoadingState } from './ui/error-state'
import { api } from '@/lib/api'
import { Check, X } from 'lucide-react'

interface PlayerAccountability {
  player_name: string
  all_champions_played: boolean
  missing_champions: string[]
  total_champions: number
  champions_played: number
}

export function AccountabilityCheck() {
  const [accountabilityData, setAccountabilityData] = useState<PlayerAccountability[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    loadAccountability()
  }, [])

  async function loadAccountability() {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getAccountabilityCheck()
      setAccountabilityData(data)
    } catch (error) {
      console.error('Error loading accountability check:', error)
      setError(error as Error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <LoadingState componentName="accountability check" />
  }

  if (error) {
    return <ErrorState error={error} onRetry={loadAccountability} />
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Accountability Check</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {accountabilityData.map((player) => (
            <div
              key={player.player_name}
              className="flex items-center justify-between p-3 rounded-lg border"
            >
              <div className="flex items-center gap-3">
                {player.all_champions_played ? (
                  <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                ) : (
                  <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center">
                    <X className="w-4 h-4 text-white" />
                  </div>
                )}
                <div>
                  <div className="font-medium">{player.player_name}</div>
                  <div className="text-sm text-muted-foreground">
                    {player.champions_played} / {player.total_champions} champions played
                  </div>
                </div>
              </div>
              {!player.all_champions_played && player.missing_champions.length > 0 && (
                <div className="text-sm text-muted-foreground">
                  Missing: {player.missing_champions.join(', ')}
                </div>
              )}
            </div>
          ))}
          {accountabilityData.length === 0 && (
            <div className="text-center text-muted-foreground py-8">
              No champion pool data available
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
