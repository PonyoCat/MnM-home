import { SessionReview } from '@/components/SessionReview'
import { DraftNotes } from '@/components/DraftNotes'
import { PickStats } from '@/components/PickStats'

export function ScrimPage() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <SessionReview />
      <DraftNotes />
      <div className="lg:col-span-2">
        <PickStats />
      </div>
    </div>
  )
}
