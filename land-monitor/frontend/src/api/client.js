const BASE = '/api'

async function req(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`)
  return res.json()
}

export const api = {
  stats: () => req('/stats'),

  listings: (filters = {}) => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([k, v]) => {
      if (v === null || v === undefined || v === '' || v === false) return
      if (Array.isArray(v)) v.forEach(item => params.append(k, item))
      else params.append(k, v)
    })
    const qs = params.toString()
    return req(`/listings${qs ? `?${qs}` : ''}`)
  },

  listing: (id) => req(`/listings/${id}`),

  patchListing: (id, body) =>
    req(`/listings/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),

  priceHistory: (id) => req(`/listings/${id}/price-history`),

  auctions: (filters = {}) => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== null && v !== undefined) params.append(k, v)
    })
    const qs = params.toString()
    return req(`/auctions${qs ? `?${qs}` : ''}`)
  },

  triggerScrape: (source = 'all') =>
    req('/scrape', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source }),
    }),
}
