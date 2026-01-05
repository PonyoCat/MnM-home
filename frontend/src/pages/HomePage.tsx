import { WeeklyChampions } from '@/components/WeeklyChampions'
import { WeeklyMessage } from '@/components/WeeklyMessage'

export function HomePage() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <WeeklyChampions />
      <WeeklyMessage />
    </div>
  )
}
