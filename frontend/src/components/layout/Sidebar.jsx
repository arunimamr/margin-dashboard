import { NavLink } from 'react-router-dom'

function Icon({ name }) {
  const paths = {
    overview: (
      <>
        <path d="M3.5 10.8 12 4l8.5 6.8" />
        <path d="M5.5 10.2V20h13v-9.8" />
        <path d="M9.5 20v-5.4h5V20" />
      </>
    ),
    projects: (
      <>
        <rect x="4" y="4" width="6" height="6" rx="1.4" />
        <rect x="14" y="4" width="6" height="6" rx="1.4" />
        <rect x="4" y="14" width="6" height="6" rx="1.4" />
        <rect x="14" y="14" width="6" height="6" rx="1.4" />
      </>
    ),
    productivity: (
      <>
        <path d="M5 19V8" />
        <path d="M12 19V5" />
        <path d="M19 19v-8" />
        <path d="M3.5 19.5h17" />
      </>
    ),
    categories: (
      <>
        <path d="M4 7.5h6l2 2h8v8.8a1.7 1.7 0 0 1-1.7 1.7H5.7A1.7 1.7 0 0 1 4 18.3Z" />
        <path d="M4 7.5V5.7A1.7 1.7 0 0 1 5.7 4h3.8l2 2H18a2 2 0 0 1 2 2v1.5" />
      </>
    ),
    import: (
      <>
        <path d="M12 4v10" />
        <path d="m8.5 10.5 3.5 3.5 3.5-3.5" />
        <path d="M5 15.5v2.8A1.7 1.7 0 0 0 6.7 20h10.6a1.7 1.7 0 0 0 1.7-1.7v-2.8" />
      </>
    ),
    settings: (
      <>
        <path d="M12 8.4a3.6 3.6 0 1 0 0 7.2 3.6 3.6 0 0 0 0-7.2Z" />
        <path d="M19.4 13.6a7.8 7.8 0 0 0 .1-1.6l2-1.5-2-3.5-2.4 1a8.2 8.2 0 0 0-1.4-.8L15.4 4h-4l-.4 3.2a8.2 8.2 0 0 0-1.4.8l-2.4-1-2 3.5 2 1.5a7.8 7.8 0 0 0 0 1.6l-2 1.5 2 3.5 2.4-1c.4.3.9.6 1.4.8l.4 3.2h4l.4-3.2c.5-.2 1-.5 1.4-.8l2.4 1 2-3.5Z" />
      </>
    ),
    user: (
      <>
        <path d="M12 12.2a3.6 3.6 0 1 0 0-7.2 3.6 3.6 0 0 0 0 7.2Z" />
        <path d="M5.2 20a7 7 0 0 1 13.6 0" />
      </>
    ),
  }

  return (
    <svg className="nav-icon" viewBox="0 0 24 24" aria-hidden="true">
      {paths[name]}
    </svg>
  )
}

const links = [
  { to: '/dashboard', label: 'Overview', icon: 'overview' },
  { to: '/dashboard/projects', label: 'Projects', icon: 'projects' },
  { to: '/dashboard/productivity', label: 'Productivity', icon: 'productivity' },
  { to: '/dashboard/categories', label: 'Categories', icon: 'categories' },
  { to: '/dashboard/import', label: 'Import Data', icon: 'import' },
  { to: '/dashboard/settings', label: 'Settings', icon: 'settings' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand-box" aria-label="Margin Dashboard">
        <div className="brand-mark" aria-hidden="true">
          <span />
          <span />
        </div>
      </div>

      <nav className="nav-menu" aria-label="Sidebar navigation">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            aria-label={link.label}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            end={link.to === '/dashboard'}
          >
            <Icon name={link.icon} />
            <span className="nav-tooltip">{link.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="profile-dot" aria-hidden="true">
          <Icon name="user" />
        </div>
      </div>
    </aside>
  )
}
