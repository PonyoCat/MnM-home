import { WeeklyChampions } from '@/components/WeeklyChampions'
import { WeeklyMessage } from '@/components/WeeklyMessage'
import { AccountabilityCheck } from '@/components/AccountabilityCheck'
import { ClashInfo } from '@/components/ClashInfo'

export function HomePage() {
  return (
    <div className="space-y-8">
      {/* Clash Info (40%) + Message Board (60%) side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-2">
          <ClashInfo />
        </div>
        <div className="lg:col-span-3">
          <WeeklyMessage />
        </div>
      </div>

      {/* 3/5 + 2/5 grid on large screens, stack on mobile */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        <div className="lg:col-span-3">
          <WeeklyChampions />
        </div>
        <div className="lg:col-span-2">
          <AccountabilityCheck />
        </div>
      </div>
    </div>
  )
}
