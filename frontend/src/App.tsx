import { SessionReview } from '@/components/SessionReview'
import { WeeklyChampions } from '@/components/WeeklyChampions'
import { DraftNotes } from '@/components/DraftNotes'
import { PickStats } from '@/components/PickStats'

function App() {
  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-foreground">League Dashboard</h1>
          <p className="text-muted-foreground mt-2">
            Track your team's performance and strategy
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SessionReview />
          <WeeklyChampions />
          <DraftNotes />
          <PickStats />
        </div>
      </div>
    </div>
  )
}

export default App
