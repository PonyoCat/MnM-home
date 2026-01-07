import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { WeeklyChampions } from '@/components/WeeklyChampions'
import { WeeklyMessage } from '@/components/WeeklyMessage'
import { RefreshCw } from 'lucide-react'

export function HomePage() {
  const [reloadKey, setReloadKey] = useState(0)

  function handleReloadAll() {
    // Force re-render of all components by changing key
    setReloadKey(prev => prev + 1)
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button
          variant="outline"
          size="sm"
          onClick={handleReloadAll}
          className="gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Reload All Data
        </Button>
      </div>

      <div key={reloadKey} className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <WeeklyChampions />
        <WeeklyMessage />
      </div>
    </div>
  )
}
