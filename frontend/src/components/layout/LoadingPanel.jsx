export default function LoadingPanel({ label = 'Loading dashboard...' }) {
  return (
    <div className="panel loading-panel" role="status" aria-live="polite">
      <div className="loading-orb" aria-hidden="true">
        <svg className="loading-chart-icon" viewBox="0 0 72 72">
          <rect x="8" y="8" width="56" height="56" rx="16" />
          <path className="loading-axis" d="M20 50h34" />
          <path className="loading-line" d="M20 44l9-11 10 7 13-20" />
          <circle cx="20" cy="44" r="3.5" />
          <circle cx="29" cy="33" r="3.5" />
          <circle cx="39" cy="40" r="3.5" />
          <circle cx="52" cy="20" r="3.5" />
        </svg>
      </div>
      <div className="loading-copy">
        <strong>{label}</strong>
        <span>Preparing analytics</span>
      </div>
      <div className="loading-bars" aria-hidden="true">
        <i />
        <i />
        <i />
        <i />
      </div>
    </div>
  )
}
