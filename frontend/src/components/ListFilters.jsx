export function ListFilters({ filters, onChange, definitions }) {
  return <div className="flex flex-wrap gap-2" aria-label="List filters">
    {definitions.map(({ key, label, options = [] }) => <label key={key} className="sr-only">{label}<select aria-label={label} className="h-9 rounded-md border bg-white px-3 text-sm not-sr-only" value={filters[key] || ''} onChange={(event) => onChange(key, event.target.value)}><option value="">All {label}s</option>{options.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}</select></label>)}
  </div>;
}
