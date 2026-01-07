import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { WeeklyChampions } from '@/components/WeeklyChampions'
import { WeeklyMessage } from '@/components/WeeklyMessage'
import { AccountabilityCheck } from '@/components/AccountabilityCheck'
import { AccountabilityDebug } from '@/components/AccountabilityDebug'
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

      <div key={reloadKey} className="space-y-8">
        {/* Weekly Message at top (full width, auto-scale height) */}
        <WeeklyMessage />

        {/* 3/5 + 2/5 grid on large screens, stack on mobile */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
          <div className="lg:col-span-3">
            <WeeklyChampions />
          </div>
          <div className="lg:col-span-2">
            <AccountabilityCheck />
          </div>
        </div>

        {/* Database verification at bottom (full width) */}
        <AccountabilityDebug />
      </div>
    </div>
  )
}
