export default function Header({
  title,
  description,
  datasets,
  selectedDatasetId,
  onDatasetChange,
  selectedYear,
  onYearChange,
  selectedMonth,
  onMonthChange,
}) {
  const years = Array.from({ length: 6 }, (_, index) => new Date().getFullYear() - index)
  const months = [
    { value: '', label: 'All months' },
    { value: 1, label: 'Jan' },
    { value: 2, label: 'Feb' },
    { value: 3, label: 'Mar' },
    { value: 4, label: 'Apr' },
    { value: 5, label: 'May' },
    { value: 6, label: 'Jun' },
    { value: 7, label: 'Jul' },
    { value: 8, label: 'Aug' },
    { value: 9, label: 'Sep' },
    { value: 10, label: 'Oct' },
    { value: 11, label: 'Nov' },
    { value: 12, label: 'Dec' },
  ]

  return (
    <header className="topbar">
      <div>
        <h1>{title}</h1>
        {description ? <p>{description}</p> : null}
      </div>

      <div className="topbar-actions">
        <label className="filter-field">
          <span>Dataset</span>
          <select value={selectedDatasetId || ''} onChange={(e) => onDatasetChange(Number(e.target.value))}>
            {datasets.map((dataset) => (
              <option key={dataset.id} value={dataset.id}>
                {dataset.name}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span>Year</span>
          <select value={selectedYear || ''} onChange={(e) => onYearChange(Number(e.target.value))}>
            {years.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span>Month</span>
          <select value={selectedMonth ?? ''} onChange={(e) => onMonthChange(e.target.value === '' ? null : Number(e.target.value))}>
            {months.map((month) => (
              <option key={month.value ?? 'all'} value={month.value}>
                {month.label}
              </option>
            ))}
          </select>
        </label>
      </div>
    </header>
  )
}
