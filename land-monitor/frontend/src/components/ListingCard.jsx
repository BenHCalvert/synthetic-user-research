const NF_LABELS = {
  inholding: { label: 'Inholding', cls: 'bg-green-900 text-green-300' },
  adjacent: { label: 'NF Adjacent', cls: 'bg-emerald-900 text-emerald-300' },
  near: { label: 'Near NF', cls: 'bg-teal-900 text-teal-300' },
}

const ACCESS_ICONS = {
  year_round_paved: '🛣️',
  year_round_gravel: '🪨',
  seasonal: '🍂',
  hike_in: '🥾',
  unknown: '',
}

const WATER_ICONS = {
  drilled_well: '🚿',
  creek_river: '🌊',
  community: '🏘️',
  none: '🏜️',
  unknown: '',
}

function ScoreBadge({ score }) {
  if (score == null) return <span className="badge bg-gray-700 text-gray-400">–</span>
  const cls =
    score >= 75 ? 'bg-green-900 text-green-300' :
    score >= 50 ? 'bg-yellow-900 text-yellow-300' :
    score >= 25 ? 'bg-orange-900 text-orange-300' :
                  'bg-red-900 text-red-400'
  return <span className={`badge ${cls} font-bold`}>{score}</span>
}

function fmtPrice(p) {
  if (!p) return 'N/A'
  return p >= 1_000_000
    ? `$${(p / 1_000_000).toFixed(2)}M`
    : `$${(p / 1000).toFixed(0)}k`
}

export default function ListingCard({ listing, onSelect, onMarkRead }) {
  const nf = NF_LABELS[listing.nf_adjacency]

  return (
    <div
      className={`card cursor-pointer hover:border-gray-600 transition-colors relative flex flex-col
        ${listing.is_new ? 'ring-1 ring-forest-600' : ''}`}
      onClick={() => onSelect(listing)}
    >
      {/* Thumbnail */}
      <div className="h-32 bg-gray-800 relative overflow-hidden">
        {listing.thumbnail_url ? (
          <img
            src={listing.thumbnail_url}
            alt=""
            className="w-full h-full object-cover"
            onError={e => { e.target.style.display = 'none' }}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-4xl text-gray-700">🌄</div>
        )}

        {/* Badges overlay */}
        <div className="absolute top-2 left-2 flex flex-wrap gap-1">
          {listing.is_new && (
            <span className="badge bg-forest-800 text-forest-200 font-semibold">NEW</span>
          )}
          {listing.in_snra && (
            <span className="badge bg-amber-900 text-amber-300">⚠️ SNRA</span>
          )}
          {listing.is_mining_claim && (
            <span className="badge bg-purple-900 text-purple-300">⛏️ Claim</span>
          )}
        </div>

        <div className="absolute top-2 right-2">
          <ScoreBadge score={listing.score} />
        </div>

        {listing.status !== 'Active' && (
          <div className="absolute bottom-0 left-0 right-0 bg-gray-900/80 text-center py-0.5 text-xs font-medium
            text-yellow-300">
            {listing.status}
          </div>
        )}
      </div>

      {/* Body */}
      <div className="p-3 flex-1 flex flex-col gap-2">
        <div>
          <p className="text-sm font-medium text-gray-100 line-clamp-2 leading-tight">
            {listing.title || 'Untitled Listing'}
          </p>
          <p className="text-xs text-gray-500 mt-0.5 truncate">
            {listing.address || listing.zone || '–'}
          </p>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-base font-bold text-white">{fmtPrice(listing.price)}</span>
          <span className="text-sm text-gray-400">
            {listing.acreage ? `${listing.acreage} ac` : '–'}
          </span>
        </div>

        {listing.price_per_acre && (
          <p className="text-xs text-gray-500">
            ${Math.round(listing.price_per_acre).toLocaleString()}/acre
          </p>
        )}

        {/* Tags row */}
        <div className="flex flex-wrap gap-1 mt-auto">
          {nf && (
            <span className={`badge ${nf.cls}`}>{nf.label}</span>
          )}
          {listing.zone && (
            <span className="badge bg-blue-900/60 text-blue-300">{listing.zone}</span>
          )}
          {listing.access_type && listing.access_type !== 'unknown' && (
            <span className="badge bg-gray-700 text-gray-300">
              {ACCESS_ICONS[listing.access_type]} {listing.access_type.replace(/_/g, ' ')}
            </span>
          )}
          {listing.water && listing.water !== 'unknown' && (
            <span className="badge bg-gray-700 text-gray-300">
              {WATER_ICONS[listing.water]} {listing.water.replace(/_/g, ' ')}
            </span>
          )}
          {listing.is_starred && <span className="badge bg-yellow-900 text-yellow-300">⭐</span>}
        </div>
      </div>

      {/* Source */}
      <div className="px-3 pb-2 flex items-center justify-between text-xs text-gray-600">
        <span>{listing.source}</span>
        {listing.is_new && (
          <button
            onClick={e => { e.stopPropagation(); onMarkRead(listing.id) }}
            className="text-gray-500 hover:text-gray-300 transition-colors"
            title="Mark as read"
          >
            ✓ Mark read
          </button>
        )}
      </div>
    </div>
  )
}
