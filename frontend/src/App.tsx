import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Navigation } from '@/components/Navigation'
import { HomePage } from '@/pages/HomePage'
import { ScrimPage } from '@/pages/ScrimPage'
import { ChampionPoolPage } from '@/pages/ChampionPoolPage'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen px-4 py-8 md:px-8">
        <div className="max-w-6xl mx-auto space-y-8">
          <header className="mb-4 border-b border-border/60 pb-6 space-y-2">
            <h1 className="text-4xl md:text-5xl font-semibold text-foreground">
              MnM dashboard
            </h1>
            <p className="text-muted-foreground text-base md:text-lg">
              Work harder not smarter
            </p>
          </header>

          <Navigation />

          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/scrim" element={<ScrimPage />} />
            <Route path="/champion-pool" element={<ChampionPoolPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}

export default App
