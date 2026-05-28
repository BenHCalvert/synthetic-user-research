import { useState, useEffect } from 'react'
import { api } from '../api/client'
import PriceChart from './PriceChart'

const FIELD_LABELS = {
  nf_adjacency: 'NF Adjacency',
  access_type: 'Access',
  water: 'Water',
  utilities: 'Utilities',
  zone: 'Zone',
  source: 'Source',
  agent_name: 'Agent',
}

const NF_COLORS = {
  inholding: 'text-green-400',
  adjacent: 'text-emerald-400',
  near: 'text-teal-400',
  none: 'text-gray-500',
  unknown: 'text-gray-500',
}

function fmtPrice(p) {
  if (!p) return 'N/A'
  return `$${p.toLocaleString()}`
}

export default function ListingModal({ listing: initial, onClose, onUpdate, onRefresh }) {
  const [listing, setListing] = useState(initial)
  const [history, setHistory] = useState([])
  const [notes, setNotes] = useState(initial.notes || '')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    // Load full detail (includes description)
    api.listing(initial.id).then(full => {
      setListing(full)
      setNotes(full.notes || '')
    })
    api.priceHistory(initial.id).then(setHistory)

    // Mark as read
    if (initial.is_new) {
      api.patchListing(initial.id, { is_new: false }).then(() => onRefresh())
    }
  }, [initial.id])

  const saveNotes = async () => {
    setSaving(true)
    try {
      const updated = await api.patchListing(listing.id, { notes })
      setListing(prev => ({ ...prev, notes: updated.notes }))
      onUpdate(updated)
    } finally {
      setSaving(false)
    }
  }

  const toggleStar = async () => {
    const updated = await api.patchListing(listing.id, { is_starred: !listing.is_starred })
    setListing(updated)
    onUpdate(updated)
    onRefresh()
  }

  const score = listing.score
  const scoreColor =
    score >= 75 ? 'text-green-400' :
    score >= 50 ? 'text-yellow-400' :
    score >= 25 ? 'text-orange-400' : 'text-red-400'

  return (
    <div
      className="fixed inset-0 bg-black/70 z-50 flex items-start justify-center p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-3xl mt-8 mb-8"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-800 flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-semibold text-white leading-tight">
              {listing.title || 'Untitled Listing'}
            </h2>
            <p className="text-sm text-gray-400 mt-0.5 truncate">
              {listing.address || listing.zone || ''}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              onClick={toggleStar}
              className={`text-xl transition-colors ${listing.is_starred ? 'text-yellow-400' : 'text-gray-600 hover:text-yellow-400'}`}
              title={listing.is_starred ? 'Unstar' : 'Star'}
            >⭐</button>
            <button onClick={onClose} className="text-gray-400 hover:text-white text-xl leading-none">✕</button>
          </div>
        </div>

        <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Left column */}
          <div className="space-y-4">
            {/* Thumbnail */}
            {listing.thumbnail_url && (
              <img
                src={listing.thumbnail_url}
                alt=""
                className="w-full h-40 object-cover rounded-lg"
                onError={e => { e.target.style.display = 'none' }}
              />
            )}

            {/* Price / size */}
            <div className="grid grid-cols-3 gap-2">
              <Stat label="Price" value={fmtPrice(listing.price)} large />
              <Stat label="Acres" value={listing.acreage ? `${listing.acreage}` : '–'} />
              <Stat label="$/acre" value={listing.price_per_acre ? `$${Math.round(listing.price_per_acre).toLocaleString()}` : '–'} />
            </div>

            {/* Score */}
            <div className="bg-gray-800 rounded-lg p-3 flex items-center justify-between">
              <span className="text-sm text-gray-400">Match Score</span>
              <span className={`text-3xl font-bold ${scoreColor}`}>
                {score ?? '–'}
              </span>
            </div>

            {/* Key attributes */}
            <div className="space-y-1.5 text-sm">
              {Object.entries(FIELD_LABELS).map(([key, label]) => {
                const val = listing[key]
                if (!val) return null
                return (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-gray-500">{label}</span>
                    <span className={`font-medium ${key === 'nf_adjacency' ? NF_COLORS[val] : 'text-gray-200'}`}>
                      {String(val).replace(/_/g, ' ')}
                    </span>
                  </div>
                )
              })}

              {listing.is_mining_claim && (
                <div className="flex items-center gap-1 text-purple-400">
                  <span>⛏️</span><span>Patented mining claim</span>
                </div>
              )}
              {listing.in_snra && (
                <div className="flex items-center gap-1 text-amber-400">
                  <span>⚠️</span><span>Within SNRA — review regulations</span>
                </div>
              )}
            </div>

            {/* Status */}
            {listing.status !== 'Active' && (
              <div className="badge bg-yellow-900/60 text-yellow-300 text-sm py-1 px-3">
                Status: {listing.status}
                {listing.sold_price && ` — Sold for $${listing.sold_price.toLocaleString()}`}
              </div>
            )}
          </div>

          {/* Right column */}
          <div className="space-y-4">
            {/* Price history chart */}
            {history.length > 1 && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1.5">Price History</p>
                <PriceChart data={history} />
              </div>
            )}

            {/* Description */}
            {listing.description && (
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1.5">Description</p>
                <div className="text-sm text-gray-300 leading-relaxed bg-gray-800 rounded-lg p-3 max-h-40 overflow-y-auto">
                  {listing.description}
                </div>
              </div>
            )}

            {/* Notes */}
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1.5">Notes</p>
              <textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                placeholder="Add your notes here…"
                rows={4}
                className="input w-full resize-none text-sm"
              />
              <button
                onClick={saveNotes}
                disabled={saving || notes === (listing.notes || '')}
                className="btn-primary text-xs mt-1.5 disabled:opacity-50"
              >
                {saving ? 'Saving…' : 'Save Notes'}
              </button>
            </div>

            {/* Date info */}
            <div className="text-xs text-gray-600 space-y-0.5">
              {listing.date_first_seen && (
                <p>First seen: {new Date(listing.date_first_seen).toLocaleDateString()}</p>
              )}
              {listing.date_last_updated && (
                <p>Updated: {new Date(listing.date_last_updated).toLocaleDateString()}</p>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-4 pb-4 pt-1 flex items-center justify-between">
          <span className="text-xs text-gray-600">Source: {listing.source}</span>
          <a
            href={listing.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary text-sm"
          >
            View Listing ↗
          </a>
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value, large }) {
  return (
    <div className="bg-gray-800 rounded-lg p-2 text-center">
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`font-semibold text-white ${large ? 'text-base' : 'text-sm'}`}>{value}</p>
    </div>
  )
}
