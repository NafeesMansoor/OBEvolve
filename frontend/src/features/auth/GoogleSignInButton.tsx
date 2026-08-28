import * as React from 'react'

import { useAuth } from '@/features/auth/useAuth'

const GOOGLE_CLIENT_ID: string | undefined = import.meta.env.VITE_GOOGLE_CLIENT_ID
const GOOGLE_SCRIPT_SRC = 'https://accounts.google.com/gsi/client'

/** Whether `VITE_GOOGLE_CLIENT_ID` is configured — pages that render this
 * button alongside other UI (a divider, an "or") should gate that UI on
 * this too, so nothing dangles when Google Sign-In isn't set up. */
export const isGoogleSignInEnabled = Boolean(GOOGLE_CLIENT_ID)

interface GoogleCredentialResponse {
  credential: string
}

interface GoogleIdConfig {
  client_id: string
  callback: (response: GoogleCredentialResponse) => void
}

interface GoogleButtonConfig {
  type?: 'standard' | 'icon'
  theme?: 'outline' | 'filled_blue' | 'filled_black'
  size?: 'large' | 'medium' | 'small'
  width?: number
  text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin'
}

// Google Identity Services attaches itself to `window.google` — no npm
// package ships types for it, so this is the minimal shape this component
// actually calls.
declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: GoogleIdConfig) => void
          renderButton: (parent: HTMLElement, config: GoogleButtonConfig) => void
        }
      }
    }
  }
}

let scriptLoadPromise: Promise<void> | null = null

function loadGoogleScript(): Promise<void> {
  if (window.google?.accounts?.id) return Promise.resolve()
  scriptLoadPromise ??= new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${GOOGLE_SCRIPT_SRC}"]`)
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('Failed to load Google script')))
      return
    }
    const script = document.createElement('script')
    script.src = GOOGLE_SCRIPT_SRC
    script.async = true
    script.defer = true
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load Google script'))
    document.head.appendChild(script)
  })
  return scriptLoadPromise
}

/**
 * Renders Google's own "Sign in with Google" button. Silently renders
 * nothing if `VITE_GOOGLE_CLIENT_ID` isn't set — Google Sign-In is optional
 * per-deployment (see .env.example), password login never depends on it.
 */
export function GoogleSignInButton({ onError }: { onError: (message: string) => void }) {
  const { loginWithGoogle } = useAuth()
  const containerRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !containerRef.current) return
    let cancelled = false

    loadGoogleScript()
      .then(() => {
        if (cancelled || !window.google || !containerRef.current) return
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: (response) => {
            loginWithGoogle(response.credential).catch((err: unknown) => {
              const message =
                err instanceof Error ? err.message : 'Unable to sign in with Google.'
              onError(message)
            })
          },
        })
        // Measure the container instead of hard-coding a pixel width so the
        // button never overflows narrow viewports (Google's renderButton
        // only accepts an explicit px width, not a CSS percentage).
        const measuredWidth = containerRef.current.clientWidth || 320
        window.google.accounts.id.renderButton(containerRef.current, {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          text: 'signin_with',
          width: Math.min(Math.max(measuredWidth, 200), 400),
        })
      })
      .catch(() => {
        if (!cancelled) onError('Could not load Google Sign-In.')
      })

    return () => {
      cancelled = true
    }
  }, [loginWithGoogle, onError])

  if (!GOOGLE_CLIENT_ID) return null

  return <div ref={containerRef} className="flex w-full justify-center" />
}
