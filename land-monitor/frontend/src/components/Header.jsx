import { useState } from 'react'

const fmtPrice = (p) => p ? `$${(p / 1000).toFixed(0)}k` : '–'
const fmtNum = (n) => n ?? '–'

export default function Header({ stats, activeTab, tabs, onTabChange, onScrape }) {
  const [scraping, setScraping] = useState(false)

  const handleScrape = async () => {
    setScraping(true)
    try { await onScrape('all') } finally {
      setTimeout(() => setScraping(false), 5000)
    }
  }

  return (
    <header className="bg-gray-900 border-b border-gray-800 flex-shrink-0">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span className="text-lg">🌲</span>
          <span className="font-semibold text-white tracking-tight">Land Parcel Monitor</span>
          <span className="text-gray-500 text-xs">Central Idaho</span>
        </div>

        {/* Stats pills */}
        <div className="hidden sm:flex items-center gap-3 text-sm">
          <StatPill label="Active" value={fmtNum(stats?.active_listings)} />
          <StatPill
            label="New"
            value={fmtNum(stats?.new_listings)}
            highlight={stats?.new_listings > 0}
          />
          <StatPill label="Avg Score" value={stats?.avg_score ?? '–'} />
          <StatPill label="Avg Price" value={fmtPrice(stats?.avg_price)} />
          {stats?.idl_new > 0 && (
            <StatPill label="IDL New" value={stats.idl_new} highlight />
          )}
        </div>

        <button
          onClick={handleScrape}
          disabled={scraping}
          className="btn-primary disabled:opacity-50 text-xs"
        >
          {scraping ? (
            <><span className="animate-spin">⟳</span> Scraping…</>
          ) : (
            '⟳ Scrape Now'
          )}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex px-4 gap-1">
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => onTabChange(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-forest-500 text-forest-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>
    </header>
  )
}

function StatPill({ label, value, highlight }) {
  return (
    <div className={`flex flex-col items-center px-2 py-0.5 rounded ${highlight ? 'bg-forest-900/50 text-forest-300' : 'text-gray-400'}`}>
      <span className="text-xs leading-none">{label}</span>
      <span className={`font-semibold leading-tight ${highlight ? 'text-forest-300' : 'text-gray-200'}`}>{value}</span>
    </div>
  )
}
