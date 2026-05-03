import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'sonner'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'
import { Navigation } from '@/components/Navigation'
import { HomePage } from '@/pages/HomePage'
import { ScrimPage } from '@/pages/ScrimPage'
import { ChampionPoolPage } from '@/pages/ChampionPoolPage'
import { MiscPage } from '@/pages/MiscPage'
import { DataPage } from '@/pages/DataPage'

function App() {
  const [reloadKey, setReloadKey] = useState(0)

  const handleReload = () => {
    setReloadKey(prev => prev + 1)
  }

  return (
    <BrowserRouter>
      <div className="min-h-screen px-4 py-8 md:px-8">
        <div className="max-w-6xl mx-auto space-y-8">
          <header className="border-b border-border/60 pb-6">
            <div className="flex justify-between items-start gap-4">
              <div className="space-y-2">
                <h1 className="text-4xl md:text-5xl font-semibold text-foreground">
                  MnM dashboard
                </h1>
                <p className="text-muted-foreground text-base md:text-lg">
                  Work harder not smarter
                </p>
              </div>
              <Button
                variant="outline"
                size="sm" // Changed to default size for better visibility, or keep sm? User said "top right", often implies a prominent utility. I'll keep it sm to match previous style but maybe md is better? Sticking to sm for consistency.
                onClick={handleReload}
                className="gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Reload Website
              </Button>
            </div>
          </header>

          <Navigation />

          <div key={reloadKey}>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/scrim" element={<ScrimPage />} />
              <Route path="/champion-pool" element={<ChampionPoolPage />} />
              <Route path="/misc" element={<MiscPage />} />
              <Route path="/data" element={<DataPage />} />
            </Routes>
          </div>
        </div>
      </div>
      <Toaster richColors position="bottom-right" />
    </BrowserRouter>
  )
}

export default App
