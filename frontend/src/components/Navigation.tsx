import { NavLink } from 'react-router-dom'
import { ThemeToggle } from './ThemeToggle'

export function Navigation() {
  return (
    <nav className="border-b border-border/60 mb-8">
      <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex gap-6">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `text-lg font-medium transition-colors hover:text-primary ${
                isActive
                  ? 'text-primary border-b-2 border-primary pb-1'
                  : 'text-muted-foreground'
              }`
            }
          >
            Home
          </NavLink>
          <NavLink
            to="/scrim"
            className={({ isActive }) =>
              `text-lg font-medium transition-colors hover:text-primary ${
                isActive
                  ? 'text-primary border-b-2 border-primary pb-1'
                  : 'text-muted-foreground'
              }`
            }
          >
            Scrim
          </NavLink>
          <NavLink
            to="/champion-pool"
            className={({ isActive }) =>
              `text-lg font-medium transition-colors hover:text-primary ${
                isActive
                  ? 'text-primary border-b-2 border-primary pb-1'
                  : 'text-muted-foreground'
              }`
            }
          >
            Champion Pool
          </NavLink>
          <NavLink
            to="/misc"
            className={({ isActive }) =>
              `text-lg font-medium transition-colors hover:text-primary ${
                isActive
                  ? 'text-primary border-b-2 border-primary pb-1'
                  : 'text-muted-foreground'
              }`
            }
          >
            Bøde
          </NavLink>
        </div>
        <ThemeToggle />
      </div>
    </nav>
  )
}
