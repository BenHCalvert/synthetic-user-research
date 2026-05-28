import { useState, useEffect } from 'react'
import { api } from '../api/client'

export default function IDLPanel({ refreshKey }) {
  const [auctions, setAuctions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    api.auctions()
      .then(setAuctions)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [refreshKey])

  const markRead = async (id) => {
    await api.patchListing  // IDL auctions don't use the same patch endpoint
    setAuctions(prev => prev.map(a => a.id === id ? { ...a, is_new: false } : a))
  }

  if (loading) {
    return (
      <div className="space-y-3 max-w-2xl">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="card h-24 animate-pulse bg-gray-800" />
        ))}
      </div>
    )
  }

  if (error) {
    return <div className="text-red-400 text-sm">Error: {error}</div>
  }

  return (
    <div className="max-w-2xl space-y-3">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white">IDL State Land Auctions</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            Idaho Department of Lands — state-owned land for sale/auction
          </p>
        </div>
        <a
          href="https://www.idl.idaho.gov/real-estate/state-land-for-sale/"
          target="_blank"
          rel="noopener noreferrer"
          className="btn-ghost text-xs border border-gray-700"
        >
          View IDL Page ↗
        </a>
      </div>

      {auctions.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 text-gray-500">
          <span className="text-4xl mb-3">🏛️</span>
          <p>No IDL auction listings found yet.</p>
          <p className="text-xs mt-1">Check runs every 24 hours.</p>
        </div>
      ) : (
        auctions.map(auction => (
          <AuctionCard key={auction.id} auction={auction} />
        ))
      )}
    </div>
  )
}

function AuctionCard({ auction }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className={`card p-4 cursor-pointer hover:border-gray-600 transition-colors
        ${auction.is_new ? 'ring-1 ring-amber-600' : ''}`}
      onClick={() => setExpanded(e => !e)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            {auction.is_new && (
              <span className="badge bg-amber-900 text-amber-300 font-semibold">NEW</span>
            )}
            <h3 className="text-sm font-medium text-white">{auction.title || 'Untitled Auction'}</h3>
          </div>
          <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
            {auction.location && <span>📍 {auction.location}</span>}
            {auction.acreage && <span>📐 {auction.acreage} ac</span>}
            {auction.asking_price && <span>💰 ${auction.asking_price.toLocaleString()}</span>}
            {auction.date_posted && <span>📅 {auction.date_posted}</span>}
          </div>
        </div>
        <a
          href={auction.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={e => e.stopPropagation()}
          className="btn-ghost text-xs border border-gray-700 flex-shrink-0"
        >
          View ↗
        </a>
      </div>

      {expanded && auction.description && (
        <div className="mt-3 text-xs text-gray-400 bg-gray-800 rounded p-3 leading-relaxed">
          {auction.description.slice(0, 800)}
          {auction.description.length > 800 && '…'}
        </div>
      )}

      <div className="mt-2 text-xs text-gray-600">
        First seen: {new Date(auction.date_first_seen).toLocaleDateString()}
      </div>
    </div>
  )
}
