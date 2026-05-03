import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api, type ChartJsonData } from '@/lib/api'

const PLAYERS = ['Alex', 'Hans', 'Elias', 'Mikkel', 'Sinus'] as const
type PlayerName = (typeof PLAYERS)[number]
type Mode = 'all' | 'player'
type ChartType = 'bar' | 'trend' | 'pie'

const PLAYER_COLORS: Record<string, string> = {
  Alex: '#1d4ed8',
  Hans: '#0f766e',
  Elias: '#7c3aed',
  Mikkel: '#dc2626',
  Sinus: '#d97706',
}

const PIE_COLORS = [
  '#f5c84c', '#5ec4ff', '#7ad66f', '#ff8f5a', '#aa8bff',
  '#ff6b8b', '#49d8c5', '#9db4ff', '#f7a8c4', '#d3e27a',
]

const CHART_GRID = 'hsl(var(--border))'
const CHART_TEXT = 'hsl(var(--muted-foreground))'

const TOP_N_OPTIONS = [5, 10, 15, 20] as const

function toIsoDate(value: Date) {
  return value.toISOString().split('T')[0]
}

interface CustomTooltipProps {
  active?: boolean
  payload?: { name: string; value: number; color: string }[]
  label?: string
}

function ChartTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null
  return (
    <div className="rounded-md border px-3 py-2 text-xs shadow-lg bg-card border-border text-card-foreground">
      {label && <p className="mb-1 font-semibold">{label}</p>}
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-muted-foreground">{entry.name}:</span>
          <span className="font-semibold">{entry.value}</span>
        </div>
      ))}
    </div>
  )
}

interface PieTooltipProps {
  active?: boolean
  payload?: { name: string; value: number; payload: { name: string; value: number } }[]
}

function PieTooltip({ active, payload }: PieTooltipProps) {
  if (!active || !payload || payload.length === 0) return null
  const item = payload[0]
  return (
    <div className="rounded-md border px-3 py-2 text-xs shadow-lg bg-card border-border text-card-foreground">
      <p className="font-semibold">{item.name}</p>
      <p className="text-muted-foreground">{item.value} game{item.value !== 1 ? 's' : ''}</p>
    </div>
  )
}

const EMPTY_DATA: ChartJsonData = {
  bar_data: [],
  line_data: [],
  line_champions: [],
  pie_data: [],
  pie_player: '',
  total_games: 0,
}

interface GroupedBarEntry {
  champion: string
  games: number
  player: string
}

interface PlayerGroup {
  player: string
  x1: string
  x2: string
  total: number
}

function buildGroupedBarData(
  barData: Record<string, string | number>[],
  players: readonly string[],
): { entries: GroupedBarEntry[]; groups: PlayerGroup[] } {
  const playerChampions = new Map<string, GroupedBarEntry[]>()
  for (const player of players) playerChampions.set(player, [])

  for (const row of barData) {
    const champion = row.champion as string
    let bestPlayer = ''
    let bestGames = 0
    for (const player of players) {
      const games = (row[player] as number) || 0
      if (games > bestGames) {
        bestGames = games
        bestPlayer = player
      }
    }
    if (bestGames > 0 && bestPlayer) {
      playerChampions.get(bestPlayer)!.push({ champion, games: bestGames, player: bestPlayer })
    }
  }

  const entries: GroupedBarEntry[] = []
  const groups: PlayerGroup[] = []

  for (const player of players) {
    const champs = (playerChampions.get(player) ?? []).sort((a, b) => b.games - a.games)
    if (champs.length === 0) continue
    const total = champs.reduce((sum, c) => sum + c.games, 0)
    groups.push({ player, x1: champs[0].champion, x2: champs[champs.length - 1].champion, total })
    entries.push(...champs)
  }

  return { entries, groups }
}

export function DataPage() {
  const today = useMemo(() => toIsoDate(new Date()), [])
  const [mode, setMode] = useState<Mode>('all')
  const [selectedPlayer, setSelectedPlayer] = useState<PlayerName>('Alex')
  const [startDate, setStartDate] = useState(today)
  const [endDate, setEndDate] = useState(today)
  const [chartData, setChartData] = useState<ChartJsonData>(EMPTY_DATA)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Chart type selector
  const [chartType, setChartType] = useState<ChartType>('bar')

  // Bar chart state
  const [barGrouped, setBarGrouped] = useState(true)
  const [barSortedNInput, setBarSortedNInput] = useState('5')
  const [barPlayerTopN, setBarPlayerTopN] = useState<number | undefined>(10)

  // Trend line state
  const [lineFilterOpen, setLineFilterOpen] = useState(false)
  const [lineExcludedChampions, setLineExcludedChampions] = useState<Set<string>>(new Set())
  const [lineByPlayer, setLineByPlayer] = useState(false)

  // Champion pool filter
  const [poolOnly, setPoolOnly] = useState(true)
  const [allPools, setAllPools] = useState<Record<string, string[]>>({})

  // Load earliest date on mount
  useEffect(() => {
    let active = true
    async function loadDateBounds() {
      try {
        const bounds = await api.getChartDateBounds()
        if (!active) return
        const earliest = bounds.earliest_date ?? today
        setStartDate(earliest)
      } catch {
        if (!active) return
      }
    }
    loadDateBounds()
    return () => { active = false }
  }, [today])

  // Fetch champion pools on mount
  useEffect(() => {
    let active = true
    async function loadPools() {
      try {
        const pools = await api.getChampionPools() as { player_name: string; champion_name: string; disabled: boolean }[]
        if (!active) return
        const grouped: Record<string, string[]> = {}
        for (const entry of pools) {
          if (entry.disabled) continue
          if (!grouped[entry.player_name]) grouped[entry.player_name] = []
          grouped[entry.player_name].push(entry.champion_name)
        }
        setAllPools(grouped)
      } catch {
        // fail silently
      }
    }
    loadPools()
    return () => { active = false }
  }, [])

  // Reset line filter when switching modes
  useEffect(() => {
    setLineExcludedChampions(new Set())
    setLineFilterOpen(false)
    setLineByPlayer(false)
  }, [mode])

  const fetchCharts = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getChartJsonData({
        mode,
        playerName: selectedPlayer,
        startDate,
        endDate,
      })
      setChartData(data)
    } catch {
      setError('Failed to load chart data. Check your date range and try again.')
      setChartData(EMPTY_DATA)
    } finally {
      setLoading(false)
    }
  }, [mode, selectedPlayer, startDate, endDate])

  useEffect(() => {
    if (startDate && endDate && startDate <= endDate) {
      fetchCharts()
    }
  }, [fetchCharts, startDate, endDate])

  const chartAxisStyle = { fill: CHART_TEXT, fontSize: 11, fontFamily: 'inherit' }

  const currentPoolSet = useMemo((): Set<string> | null => {
    if (!poolOnly) return null
    if (mode === 'player') return new Set(allPools[selectedPlayer] ?? [])
    const all = new Set<string>()
    Object.values(allPools).forEach(champs => champs.forEach(c => all.add(c)))
    return all
  }, [poolOnly, mode, selectedPlayer, allPools])

  const filteredBarData = useMemo(() => {
    if (!currentPoolSet) return chartData.bar_data
    return chartData.bar_data.filter(row => currentPoolSet.has(row.champion as string))
  }, [chartData.bar_data, currentPoolSet])

  const filteredLineChampions = useMemo(() => {
    if (!currentPoolSet) return chartData.line_champions
    return chartData.line_champions.filter(c => currentPoolSet.has(c))
  }, [chartData.line_champions, currentPoolSet])

  const filteredPieData = useMemo(() => {
    if (!currentPoolSet) return chartData.pie_data
    return chartData.pie_data.filter(d => currentPoolSet.has(d.name))
  }, [chartData.pie_data, currentPoolSet])

  const filteredTotalGames = useMemo(() => {
    if (!currentPoolSet) return chartData.total_games
    if (mode === 'player') {
      return filteredBarData.reduce((sum, row) => sum + ((row.games as number) || 0), 0)
    }
    return filteredBarData.reduce(
      (sum, row) => sum + PLAYERS.reduce((s, p) => s + ((row[p] as number) || 0), 0), 0
    )
  }, [filteredBarData, currentPoolSet, chartData.total_games, mode])

  const lineChampionColors = useMemo(() => {
    const colorMap: Record<string, string> = {}
    filteredLineChampions.forEach((champ, i) => {
      colorMap[champ] = PIE_COLORS[i % PIE_COLORS.length]
    })
    return colorMap
  }, [filteredLineChampions])

  // Grouped bar data (all mode)
  const groupedBarData = useMemo(() => {
    if (mode !== 'all' || !barGrouped || filteredBarData.length === 0) return null
    return buildGroupedBarData(filteredBarData, PLAYERS)
  }, [filteredBarData, mode, barGrouped])

  // Sorted bar data (all mode, sorted sub-mode)
  const barSortedN = Math.max(1, Math.min(999, parseInt(barSortedNInput) || 5))
  const sortedBarData = useMemo(() => {
    return filteredBarData.slice(0, barSortedN)
  }, [filteredBarData, barSortedN])

  // Player bar data
  const playerBarData = useMemo(() => {
    if (barPlayerTopN === undefined) return filteredBarData
    return filteredBarData.slice(0, barPlayerTopN)
  }, [filteredBarData, barPlayerTopN])

  // Champion-to-player ownership (who has most games on each champion)
  const championOwnership = useMemo(() => {
    const ownership: Record<string, string> = {}
    for (const row of filteredBarData) {
      const champion = row.champion as string
      let bestPlayer = ''
      let bestGames = 0
      for (const player of PLAYERS) {
        const games = (row[player] as number) || 0
        if (games > bestGames) {
          bestGames = games
          bestPlayer = player
        }
      }
      if (bestPlayer) ownership[champion] = bestPlayer
    }
    return ownership
  }, [filteredBarData])

  // Champions grouped by owning player for the filter panel
  const championsByPlayer = useMemo(() => {
    const groups: Record<string, string[]> = {}
    for (const player of PLAYERS) groups[player] = []
    for (const champ of filteredLineChampions) {
      const owner = championOwnership[champ]
      if (owner && groups[owner]) groups[owner].push(champ)
    }
    return groups
  }, [filteredLineChampions, championOwnership])

  // Visible line champions after applying exclusion filter
  const visibleLineChampions = useMemo(() => {
    const base = filteredLineChampions.filter(champ => !lineExcludedChampions.has(champ))
    if (mode === 'player' && !poolOnly) return base.slice(0, 5)
    return base
  }, [filteredLineChampions, lineExcludedChampions, mode, poolOnly])

  // Per-player weekly line data (all mode, lineByPlayer = true)
  const playerWeeklyLineData = useMemo(() => {
    if (mode !== 'all') return []
    return chartData.line_data.map(entry => {
      const row: Record<string, string | number> = { week: entry.week as string }
      for (const player of PLAYERS) row[player] = 0
      for (const [key, value] of Object.entries(entry)) {
        if (key === 'week') continue
        const owner = championOwnership[key]
        if (owner) row[owner] = (row[owner] as number) + (value as number)
      }
      return row
    })
  }, [chartData.line_data, championOwnership, mode])

  function togglePlayerLineFilter(player: string) {
    const playerChamps = championsByPlayer[player] || []
    const allExcluded = playerChamps.length > 0 && playerChamps.every(c => lineExcludedChampions.has(c))
    setLineExcludedChampions(prev => {
      const next = new Set(prev)
      if (allExcluded) {
        playerChamps.forEach(c => next.delete(c))
      } else {
        playerChamps.forEach(c => next.add(c))
      }
      return next
    })
  }

  function toggleChampionLineFilter(champ: string) {
    setLineExcludedChampions(prev => {
      const next = new Set(prev)
      if (next.has(champ)) next.delete(champ)
      else next.add(champ)
      return next
    })
  }

  // Pie data
  const effectivePieData = useMemo(() => {
    if (mode === 'all') {
      return PLAYERS.map(player => ({
        name: player,
        value: filteredBarData.reduce((sum, row) => sum + ((row[player] as number) || 0), 0),
      })).filter(d => d.value > 0)
    }
    return filteredPieData.slice(0, 5)
  }, [filteredBarData, filteredPieData, mode])

  const totalGamesLabel = mode === 'player'
    ? `games by ${selectedPlayer}`
    : 'games across all players'

  return (
    <div className="space-y-4">
      {/* Controls row */}
      <div className="flex flex-wrap items-end gap-4">
        <div className="space-y-1">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">View</p>
          <div className="flex gap-2">
            <Button
              variant={mode === 'all' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setMode('all')}
            >
              All Players
            </Button>
            <Button
              variant={mode === 'player' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setMode('player')}
            >
              Select Player
            </Button>
          </div>
        </div>

        {mode === 'player' && (
          <div className="space-y-1">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Player</p>
            <div className="flex flex-wrap gap-2">
              {PLAYERS.map((player) => (
                <Button
                  key={player}
                  size="sm"
                  variant={selectedPlayer === player ? 'default' : 'outline'}
                  style={selectedPlayer === player ? { backgroundColor: PLAYER_COLORS[player], borderColor: PLAYER_COLORS[player] } : {}}
                  onClick={() => setSelectedPlayer(player)}
                >
                  {player}
                </Button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-1">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Start Date</p>
          <Input
            type="date"
            value={startDate}
            className="w-40"
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div className="space-y-1">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">End Date</p>
          <Input
            type="date"
            value={endDate}
            className="w-40"
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>

        <div className="space-y-1">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Champions</p>
          <div className="flex gap-1">
            <Button
              variant={poolOnly ? 'default' : 'outline'}
              size="sm"
              onClick={() => setPoolOnly(true)}
            >
              Pool Only
            </Button>
            <Button
              variant={!poolOnly ? 'default' : 'outline'}
              size="sm"
              onClick={() => setPoolOnly(false)}
            >
              All
            </Button>
          </div>
        </div>

        <Button variant="outline" size="sm" onClick={fetchCharts} disabled={loading}>
          {loading ? 'Loading...' : 'Refresh'}
        </Button>

        <div className="ml-auto text-right">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Total Games</p>
          <p className="text-2xl font-bold text-foreground">
            {(filteredTotalGames ?? 0).toLocaleString()}
          </p>
          <p className="text-xs text-muted-foreground">{totalGamesLabel}</p>
        </div>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {/* Chart type selector */}
      <div className="flex gap-2">
        <Button variant={chartType === 'bar' ? 'default' : 'outline'} size="sm" onClick={() => setChartType('bar')}>
          Bar Chart
        </Button>
        <Button variant={chartType === 'trend' ? 'default' : 'outline'} size="sm" onClick={() => setChartType('trend')}>
          Trend Line
        </Button>
        <Button variant={chartType === 'pie' ? 'default' : 'outline'} size="sm" onClick={() => setChartType('pie')}>
          Pie Chart
        </Button>
      </div>

      {/* Single chart card */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-2">
            <CardTitle>
              {chartType === 'bar' && (
                <>
                  Champion Games (Bar)
                  {mode === 'player' && <span className="text-muted-foreground font-normal text-sm ml-2">— {selectedPlayer}</span>}
                </>
              )}
              {chartType === 'trend' && (
                <>
                  Weekly Trend (Line)
                  {mode === 'player' && <span className="text-muted-foreground font-normal text-sm ml-2">— {selectedPlayer}</span>}
                </>
              )}
              {chartType === 'pie' && (
                <>
                  Games Share
                  <span className="text-muted-foreground font-normal text-sm ml-2">
                    — {mode === 'all' ? 'By Player' : (chartData.pie_player || selectedPlayer)}
                  </span>
                </>
              )}
            </CardTitle>

            {/* Bar chart controls */}
            {chartType === 'bar' && (
              <div className="flex flex-wrap items-center gap-2">
                {mode === 'all' && (
                  <div className="flex gap-1">
                    <Button
                      variant={barGrouped ? 'default' : 'outline'}
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => setBarGrouped(true)}
                    >
                      Grouped
                    </Button>
                    <Button
                      variant={!barGrouped ? 'default' : 'outline'}
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => setBarGrouped(false)}
                    >
                      Sorted
                    </Button>
                  </div>
                )}
                {mode === 'all' && !barGrouped && (
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-muted-foreground">Show:</span>
                    <Input
                      type="number"
                      min="1"
                      max="999"
                      value={barSortedNInput}
                      className="h-7 w-16 text-xs px-2"
                      onChange={(e) => setBarSortedNInput(e.target.value)}
                    />
                    <span className="text-xs text-muted-foreground">bars</span>
                  </div>
                )}
                {mode === 'player' && (
                  <div className="flex items-center gap-1">
                    <span className="text-xs text-muted-foreground">Top:</span>
                    {TOP_N_OPTIONS.map((n) => (
                      <Button
                        key={n}
                        variant={barPlayerTopN === n ? 'default' : 'outline'}
                        size="sm"
                        className="h-7 px-2 text-xs"
                        onClick={() => setBarPlayerTopN(n)}
                      >
                        {n}
                      </Button>
                    ))}
                    <Button
                      variant={barPlayerTopN === undefined ? 'default' : 'outline'}
                      size="sm"
                      className="h-7 px-2 text-xs"
                      onClick={() => setBarPlayerTopN(undefined)}
                    >
                      All
                    </Button>
                  </div>
                )}
              </div>
            )}

            {/* Trend line controls */}
            {chartType === 'trend' && mode === 'all' && (
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <Button
                    variant={!lineByPlayer ? 'default' : 'outline'}
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => setLineByPlayer(false)}
                  >
                    By Champion
                  </Button>
                  <Button
                    variant={lineByPlayer ? 'default' : 'outline'}
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => setLineByPlayer(true)}
                  >
                    By Player
                  </Button>
                </div>
                {!lineByPlayer && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => setLineFilterOpen(o => !o)}
                  >
                    {lineFilterOpen ? 'Hide Filter' : 'Filter Champions'}
                  </Button>
                )}
              </div>
            )}
          </div>

          {/* Bar grouped label */}
          {chartType === 'bar' && mode === 'all' && barGrouped && (
            <p className="text-xs text-muted-foreground mt-1">All champions grouped by player</p>
          )}

          {/* Trend line champion filter panel */}
          {chartType === 'trend' && mode === 'all' && !lineByPlayer && lineFilterOpen && filteredLineChampions.length > 0 && (
            <div className="mt-3 rounded-md border p-3 space-y-3 bg-muted/50">
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Champion Filter</p>
              {PLAYERS.map(player => {
                const champs = championsByPlayer[player] || []
                if (champs.length === 0) return null
                const allExcluded = champs.every(c => lineExcludedChampions.has(c))
                const shownCount = champs.filter(c => !lineExcludedChampions.has(c)).length
                return (
                  <div key={player} className="space-y-1">
                    <div className="flex items-center gap-2">
                      <button
                        className="text-xs font-semibold px-2 py-0.5 rounded"
                        style={{
                          backgroundColor: allExcluded ? 'transparent' : PLAYER_COLORS[player] + '33',
                          color: allExcluded ? '#64748b' : PLAYER_COLORS[player],
                          border: `1px solid ${PLAYER_COLORS[player]}`,
                        }}
                        onClick={() => togglePlayerLineFilter(player)}
                      >
                        {player}
                      </button>
                      <span className="text-xs text-muted-foreground">
                        {allExcluded ? '(hidden)' : `${shownCount}/${champs.length} shown`}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1 pl-2">
                      {champs.map(champ => {
                        const excluded = lineExcludedChampions.has(champ)
                        return (
                          <button
                            key={champ}
                            className={`text-xs px-2 py-0.5 rounded border transition-colors ${
                              excluded
                                ? 'opacity-40 line-through border-border text-muted-foreground'
                                : 'bg-muted border-border text-foreground'
                            }`}
                            onClick={() => toggleChampionLineFilter(champ)}
                          >
                            {champ}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardHeader>

        <CardContent>
          {/* BAR CHART */}
          {chartType === 'bar' && (
            <>
              {chartData.bar_data.length === 0 ? (
                <EmptyChart />
              ) : mode === 'all' && barGrouped && groupedBarData ? (
                <ResponsiveContainer width="100%" height={440}>
                  <BarChart data={groupedBarData.entries} margin={{ top: 8, right: 16, left: 0, bottom: 72 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
                    {groupedBarData.groups.map((group) => (
                      <ReferenceArea
                        key={group.player}
                        x1={group.x1}
                        x2={group.x2}
                        y1={0}
                        y2={group.total}
                        fill={PLAYER_COLORS[group.player]}
                        fillOpacity={0.07}
                        stroke={PLAYER_COLORS[group.player]}
                        strokeOpacity={0.3}
                        strokeDasharray="4 2"
                        label={{
                          value: `${group.player} (${group.total})`,
                          position: 'insideTopRight',
                          fill: PLAYER_COLORS[group.player],
                          fontSize: 10,
                        }}
                      />
                    ))}
                    <XAxis dataKey="champion" tick={chartAxisStyle} angle={-35} textAnchor="end" interval={0} />
                    <YAxis tick={chartAxisStyle} allowDecimals={false} />
                    <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
                    <Bar dataKey="games" radius={[3, 3, 0, 0]}>
                      {groupedBarData.entries.map((entry, index) => (
                        <Cell key={index} fill={PLAYER_COLORS[entry.player] ?? '#d97706'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : mode === 'all' && !barGrouped ? (
                <ResponsiveContainer width="100%" height={440}>
                  <BarChart data={sortedBarData} margin={{ top: 4, right: 16, left: 0, bottom: 72 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
                    <XAxis dataKey="champion" tick={chartAxisStyle} angle={-35} textAnchor="end" interval={0} />
                    <YAxis tick={chartAxisStyle} allowDecimals={false} />
                    <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
                    <Legend wrapperStyle={{ color: 'hsl(var(--muted-foreground))', fontSize: 12 }} />
                    {PLAYERS.map((player) => (
                      <Bar key={player} dataKey={player} fill={PLAYER_COLORS[player]} radius={[2, 2, 0, 0]} />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <ResponsiveContainer width="100%" height={440}>
                  <BarChart data={playerBarData} margin={{ top: 4, right: 16, left: 0, bottom: 72 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
                    <XAxis dataKey="champion" tick={chartAxisStyle} angle={-35} textAnchor="end" interval={0} />
                    <YAxis tick={chartAxisStyle} allowDecimals={false} />
                    <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
                    <Bar dataKey="games" fill={PLAYER_COLORS[selectedPlayer] ?? '#d97706'} radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </>
          )}

          {/* TREND LINE */}
          {chartType === 'trend' && (
            <>
              {mode === 'all' && lineByPlayer ? (
                playerWeeklyLineData.length === 0 ? (
                  <EmptyChart />
                ) : (
                  <ResponsiveContainer width="100%" height={440}>
                    <LineChart data={playerWeeklyLineData} margin={{ top: 4, right: 16, left: 0, bottom: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
                      <XAxis
                        dataKey="week"
                        tick={chartAxisStyle}
                        angle={-25}
                        textAnchor="end"
                        height={50}
                        interval="preserveStartEnd"
                      />
                      <YAxis tick={chartAxisStyle} allowDecimals={false} />
                      <Tooltip content={<ChartTooltip />} />
                      <Legend
                        layout="vertical"
                        align="right"
                        verticalAlign="middle"
                        wrapperStyle={{ color: 'hsl(var(--muted-foreground))', fontSize: 11, paddingLeft: 8 }}
                      />
                      {PLAYERS.map((player) => (
                        <Line
                          key={player}
                          type="monotone"
                          dataKey={player}
                          stroke={PLAYER_COLORS[player]}
                          strokeWidth={2}
                          dot={false}
                          activeDot={{ r: 4 }}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                )
              ) : chartData.line_data.length === 0 || visibleLineChampions.length === 0 ? (
                <EmptyChart />
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={chartData.line_data} margin={{ top: 4, right: 16, left: 0, bottom: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} />
                      <XAxis
                        dataKey="week"
                        tick={chartAxisStyle}
                        angle={-25}
                        textAnchor="end"
                        height={50}
                        interval="preserveStartEnd"
                      />
                      <YAxis tick={chartAxisStyle} allowDecimals={false} />
                      <Tooltip content={<ChartTooltip />} />
                      {visibleLineChampions.map((champion) => (
                        <Line
                          key={champion}
                          type="monotone"
                          dataKey={champion}
                          stroke={lineChampionColors[champion] ?? '#888'}
                          strokeWidth={2}
                          dot={false}
                          activeDot={{ r: 4 }}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                  <ChampionLegend
                    champions={filteredLineChampions}
                    excludedChampions={mode === 'all' ? lineExcludedChampions : undefined}
                    onToggle={mode === 'all' ? toggleChampionLineFilter : undefined}
                    colorMap={lineChampionColors}
                  />
                </>
              )}
            </>
          )}

          {/* PIE CHART */}
          {chartType === 'pie' && (
            <>
              {effectivePieData.length === 0 ? (
                <EmptyChart />
              ) : (
                <ResponsiveContainer width="100%" height={620}>
                  <PieChart margin={{ top: 30, bottom: 0, left: 0, right: 0 }}>
                    <Pie
                      data={effectivePieData}
                      cx="50%"
                      cy="48%"
                      outerRadius={200}
                      dataKey="value"
                      label={({ percent }) => (percent ?? 0) >= 0.05 ? `${((percent ?? 0) * 100).toFixed(0)}%` : ''}
                      labelLine={false}
                    >
                      {effectivePieData.map((entry, index) => (
                        <Cell
                          key={index}
                          fill={PLAYER_COLORS[entry.name] ?? Object.values(PLAYER_COLORS)[index % Object.values(PLAYER_COLORS).length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip content={<PieTooltip />} />
                    <Legend
                      layout="vertical"
                      align="center"
                      verticalAlign="bottom"
                      wrapperStyle={{ color: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                      formatter={(value, entry) => {
                        const item = entry.payload as { name: string; value: number } | undefined
                        return `${value}${item ? ` (${item.value})` : ''}`
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function ChampionLegend({ champions, excludedChampions, onToggle, colorMap }: {
  champions: string[]
  excludedChampions?: Set<string>
  onToggle?: (champ: string) => void
  colorMap: Record<string, string>
}) {
  if (champions.length === 0) return null
  return (
    <div className="flex flex-wrap gap-1.5 mt-3 px-1 pb-1">
      {champions.map((champ) => {
        const isExcluded = excludedChampions?.has(champ)
        const color = colorMap[champ] ?? '#888'
        return (
          <button
            key={champ}
            onClick={() => onToggle?.(champ)}
            title={onToggle ? (isExcluded ? `Show ${champ}` : `Hide ${champ}`) : champ}
            className={`inline-flex items-center gap-1.5 text-xs px-2 py-1 rounded-full border transition-all ${
              isExcluded
                ? 'opacity-30 border-border/50 text-muted-foreground'
                : 'border-border text-foreground bg-muted/20 hover:bg-muted/40'
            } ${onToggle ? 'cursor-pointer' : 'cursor-default'}`}
          >
            <span className="inline-block h-2 w-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
            {champ}
          </button>
        )
      })}
    </div>
  )
}

function EmptyChart() {
  return (
    <div className="flex min-h-[240px] w-full items-center justify-center rounded-lg border border-dashed text-sm text-muted-foreground bg-muted/20">
      No data in selected range
    </div>
  )
}
