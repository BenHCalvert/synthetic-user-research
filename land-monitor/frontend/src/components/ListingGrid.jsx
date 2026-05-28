import { useState, useEffect, useRef } from 'react'
import { api } from '../api/client'
import ListingCard from './ListingCard'

export default function ListingGrid({ filters, refreshKey, onSelect, onRefresh }) {
  const [data, setData] = useState({ listings: [], total: 0 })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [offset, setOffset] = useState(0)
  const LIMIT = 50
  const prevFilters = useRef(null)

  useEffect(() => {
    // Reset offset when filters change
    if (JSON.stringify(filters) !== JSON.stringify(prevFilters.current)) {
      prevFilters.current = filters
      setOffset(0)
    }
    load(0)
  }, [filters, refreshKey])

  const load = async (off = offset) => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.listings({ ...filters, limit: LIMIT, offset: off })
      setData(result)
      setOffset(off)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleMarkRead = async (id) => {
    await api.patchListing(id, { is_new: false })
    onRefresh()
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-red-400 text-sm">
        Error loading listings: {error}
      </div>
    )
  }

  return (
    <div>
      {/* Count bar */}
      <div className="flex items-center justify-between mb-3 text-sm text-gray-400">
        <span>
          {loading ? 'Loading…' : `${data.total} listings`}
          {data.total > LIMIT && ` (showing ${offset + 1}–${Math.min(offset + LIMIT, data.total)})`}
        </span>
        <div className="flex gap-2">
          {offset > 0 && (
            <button className="btn-ghost text-xs" onClick={() => load(offset - LIMIT)}>← Prev</button>
          )}
          {offset + LIMIT < data.total && (
            <button className="btn-ghost text-xs" onClick={() => load(offset + LIMIT)}>Next →</button>
          )}
        </div>
      </div>

      {/* Grid */}
      {loading && data.listings.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card h-44 animate-pulse bg-gray-800" />
          ))}
        </div>
      ) : data.listings.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          <span className="text-4xl mb-3">🌲</span>
          <p>No listings match your filters.</p>
          <p className="text-xs mt-1">Try broadening the search or triggering a scrape.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {data.listings.map(listing => (
            <ListingCard
              key={listing.id}
              listing={listing}
              onSelect={onSelect}
              onMarkRead={handleMarkRead}
            />
          ))}
        </div>
      )}
    </div>
  )
}
