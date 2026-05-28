import { useState, useEffect, useCallback } from 'react'
import { api } from './api/client'
import Header from './components/Header'
import FilterPanel from './components/FilterPanel'
import ListingGrid from './components/ListingGrid'
import ListingModal from './components/ListingModal'
import IDLPanel from './components/IDLPanel'

const TABS = ['Listings', 'IDL Auctions']

export default function App() {
  const [stats, setStats] = useState(null)
  const [filters, setFilters] = useState({
    sort: 'score_desc',
    status: ['Active', 'Under Contract'],
  })
  const [activeTab, setActiveTab] = useState('Listings')
  const [selectedListing, setSelectedListing] = useState(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const loadStats = useCallback(() => {
    api.stats().then(setStats).catch(console.error)
  }, [])

  useEffect(() => {
    loadStats()
    const interval = setInterval(loadStats, 60_000)
    return () => clearInterval(interval)
  }, [loadStats])

  const refresh = () => setRefreshKey(k => k + 1)

  const handleScrape = async (source) => {
    try {
      await api.triggerScrape(source)
      setTimeout(refresh, 3000)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        stats={stats}
        activeTab={activeTab}
        tabs={TABS}
        onTabChange={setActiveTab}
        onScrape={handleScrape}
      />

      <div className="flex flex-1 overflow-hidden">
        {activeTab === 'Listings' && (
          <>
            <FilterPanel filters={filters} onChange={setFilters} />
            <main className="flex-1 overflow-y-auto p-4">
              <ListingGrid
                filters={filters}
                refreshKey={refreshKey}
                onSelect={setSelectedListing}
                onRefresh={refresh}
              />
            </main>
          </>
        )}

        {activeTab === 'IDL Auctions' && (
          <main className="flex-1 overflow-y-auto p-4">
            <IDLPanel refreshKey={refreshKey} />
          </main>
        )}
      </div>

      {selectedListing && (
        <ListingModal
          listing={selectedListing}
          onClose={() => setSelectedListing(null)}
          onUpdate={(updated) => setSelectedListing(updated)}
          onRefresh={refresh}
        />
      )}
    </div>
  )
}
