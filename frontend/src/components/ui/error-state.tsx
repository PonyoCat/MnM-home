import { Button } from './button'
import { Card, CardContent } from './card'

interface ErrorStateProps {
  error: Error | null
  onRetry: () => void
  componentName?: string
}

export function ErrorState({ error, onRetry }: ErrorStateProps) {
  if (!error) return null

  const isNetworkError =
    error.message.includes('Failed to fetch') ||
    error.message.includes('NetworkError') ||
    error.message.includes('timeout')

  return (
    <Card className="border-destructive/50">
      <CardContent className="pt-6">
        <div className="text-center space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-destructive">
              {isNetworkError ? 'Connection Error' : 'Error Loading Data'}
            </h3>
            <p className="text-sm text-muted-foreground mt-2">
              {isNetworkError
                ? 'Unable to connect to the server. The backend may be starting up (takes ~30 seconds).'
                : error.message
              }
            </p>
          </div>
          <Button onClick={onRetry} variant="outline">
            Retry
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

interface LoadingStateProps {
  componentName?: string
}

export function LoadingState({ componentName = 'component' }: LoadingStateProps) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="text-center space-y-2">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" />
          <p className="text-sm text-muted-foreground">Loading {componentName}...</p>
        </div>
      </CardContent>
    </Card>
  )
}
