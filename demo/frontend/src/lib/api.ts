/**
 * MedArmor API base. Uses credentials: 'include' for cookie auth.
 */

const getBaseUrl = () => {
  const base = import.meta.env.VITE_API_URL
  if (base) return base.replace(/\/$/, '')
  return '/api'
}

export function apiGet<T>(path: string): Promise<T> {
  const url = `${getBaseUrl()}${path}`
  return fetch(url, { credentials: 'include' }).then(async (res) => {
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error((data as { detail?: string }).detail ?? 'Request failed')
    }
    return res.json() as Promise<T>
  })
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  const url = `${getBaseUrl()}${path}`
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  }).then(async (res) => {
    if (!res.ok) {
      const data = await res.json().catch(() => ({}))
      throw new Error((data as { detail?: string }).detail ?? 'Request failed')
    }
    return res.json() as Promise<T>
  })
}
