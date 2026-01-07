// Retry configuration and utility functions
export interface RetryConfig {
  maxAttempts: number
  delayMs: number
  backoffMultiplier: number
  shouldRetry: (error: Error) => boolean
}

const DEFAULT_CONFIG: RetryConfig = {
  maxAttempts: 3,
  delayMs: 1000,
  backoffMultiplier: 2,
  shouldRetry: (error) => {
    // Only retry network errors and 5xx server errors
    // Don't retry 4xx client errors
    if (error.message.includes('Failed to fetch')) return true
    if (error.message.includes('NetworkError')) return true
    if (error.message.includes('timeout')) return true
    return false
  }
}

// Exponential backoff delay
function wait(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

// Retry wrapper function
export async function withRetry<T>(
  fn: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const finalConfig = { ...DEFAULT_CONFIG, ...config }
  let lastError: Error

  for (let attempt = 1; attempt <= finalConfig.maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error

      // Check if we should retry
      if (!finalConfig.shouldRetry(lastError)) {
        throw lastError
      }

      // Don't wait after the last attempt
      if (attempt < finalConfig.maxAttempts) {
        const delay = finalConfig.delayMs * Math.pow(finalConfig.backoffMultiplier, attempt - 1)
        console.log(`Retry attempt ${attempt}/${finalConfig.maxAttempts} after ${delay}ms`)
        await wait(delay)
      }
    }
  }

  // All retries exhausted
  throw lastError!
}

// Fetch with timeout
export async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeoutMs: number = 10000
): Promise<Response> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    })
    return response
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error('Request timeout')
    }
    throw error
  } finally {
    clearTimeout(timeout)
  }
}
