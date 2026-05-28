const ZONES = [
  'Lowman',
  'Garden Valley',
  'Atlanta/Trinity',
  'Mackay/Lost River',
  'Salmon/Elk Bend',
  'Stanley/Sawtooth',
]

const NF_OPTIONS = [
  { value: 'inholding', label: 'Inholding' },
  { value: 'adjacent', label: 'Adjacent' },
  { value: 'near', label: 'Near NF' },
]

const SORT_OPTIONS = [
  { value: 'score_desc', label: 'Score ↓' },
  { value: 'score_asc', label: 'Score ↑' },
  { value: 'price_asc', label: 'Price ↑' },
  { value: 'price_desc', label: 'Price ↓' },
  { value: 'date_desc', label: 'Newest' },
  { value: 'ppa_asc', label: '$/acre ↑' },
]

export default function FilterPanel({ filters, onChange }) {
  const set = (key, value) => onChange(prev => ({ ...prev, [key]: value }))

  const toggleArray = (key, value) => {
    const arr = filters[key] || []
    set(key, arr.includes(value) ? arr.filter(x => x !== value) : [...arr, value])
  }

  return (
    <aside className="w-52 flex-shrink-0 bg-gray-900 border-r border-gray-800 overflow-y-auto p-3 space-y-4">
      {/* Sort */}
      <Section label="Sort">
        <select
          value={filters.sort || 'score_desc'}
          onChange={e => set('sort', e.target.value)}
          className="input w-full"
        >
          {SORT_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </Section>

      {/* Zone */}
      <Section label="Zone">
        {ZONES.map(z => (
          <CheckRow
            key={z}
            label={z}
            checked={(filters.zone || []).includes(z)}
            onChange={() => toggleArray('zone', z)}
          />
        ))}
      </Section>

      {/* NF Adjacency */}
      <Section label="NF Adjacency">
        {NF_OPTIONS.map(o => (
          <CheckRow
            key={o.value}
            label={o.label}
            checked={(filters.nf_adjacency || []).includes(o.value)}
            onChange={() => toggleArray('nf_adjacency', o.value)}
          />
        ))}
      </Section>

      {/* Price */}
      <Section label="Price">
        <NumberInput
          placeholder="Min $"
          value={filters.min_price || ''}
          onChange={v => set('min_price', v ? parseInt(v) : null)}
        />
        <NumberInput
          placeholder="Max $"
          value={filters.max_price || ''}
          onChange={v => set('max_price', v ? parseInt(v) : null)}
        />
      </Section>

      {/* Acreage */}
      <Section label="Acreage">
        <NumberInput
          placeholder="Min acres"
          value={filters.min_acreage || ''}
          onChange={v => set('min_acreage', v ? parseFloat(v) : null)}
        />
        <NumberInput
          placeholder="Max acres"
          value={filters.max_acreage || ''}
          onChange={v => set('max_acreage', v ? parseFloat(v) : null)}
        />
      </Section>

      {/* Min Score */}
      <Section label={`Min Score: ${filters.min_score || 0}`}>
        <input
          type="range"
          min={0}
          max={100}
          step={5}
          value={filters.min_score || 0}
          onChange={e => set('min_score', parseInt(e.target.value))}
          className="w-full accent-forest-500"
        />
      </Section>

      {/* Flags */}
      <Section label="Flags">
        <CheckRow
          label="New only"
          checked={filters.is_new === true}
          onChange={() => set('is_new', filters.is_new === true ? null : true)}
        />
        <CheckRow
          label="Starred"
          checked={filters.is_starred === true}
          onChange={() => set('is_starred', filters.is_starred === true ? null : true)}
        />
      </Section>

      {/* Reset */}
      <button
        onClick={() => onChange({ sort: 'score_desc', status: ['Active', 'Under Contract'] })}
        className="w-full btn-ghost text-xs border border-gray-700"
      >
        Reset Filters
      </button>
    </aside>
  )
}

function Section({ label, children }) {
  return (
    <div>
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">{label}</p>
      <div className="space-y-1">{children}</div>
    </div>
  )
}

function CheckRow({ label, checked, onChange }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-300 hover:text-white">
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="rounded border-gray-600 accent-forest-500"
      />
      {label}
    </label>
  )
}

function NumberInput({ placeholder, value, onChange }) {
  return (
    <input
      type="number"
      placeholder={placeholder}
      value={value}
      onChange={e => onChange(e.target.value)}
      className="input w-full"
    />
  )
}
