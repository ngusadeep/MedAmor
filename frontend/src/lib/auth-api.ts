/**
 * Auth API client for MedAudit backend.
 * Uses credentials: 'include' so HTTP-only cookie (access_token) is sent/received.
 */

/** API root: VITE_API_URL (e.g. /api) or default /api when same origin. */
const getBaseUrl = () => {
  const base = import.meta.env.VITE_API_URL
  if (base) return base.replace(/\/$/, '')
  return '/api'
}

export interface UserResponse {
  id: string
  username: string
  role: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export async function login(username: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${getBaseUrl()}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail ?? 'Login failed')
  }
  return res.json()
}

export async function signup(username: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${getBaseUrl()}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail ?? 'Sign up failed')
  }
  return res.json()
}

export async function logout(): Promise<void> {
  await fetch(`${getBaseUrl()}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  })
}

export async function me(): Promise<UserResponse | null> {
  try {
    const res = await fetch(`${getBaseUrl()}/auth/me`, {
      credentials: 'include',
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}
