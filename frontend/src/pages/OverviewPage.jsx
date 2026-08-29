import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { getDashboard, getDashboardTrend, getDepartmentAnalytics, getProjects } from '../api/api'
import LoadingPanel from '../components/layout/LoadingPanel'
import { exportToCsv } from '../utils/csv'
import { formatCurrency, formatHours, formatPercentage } from '../utils/formatters'

const EMPTY_DASHBOARD = {
  hours: { total: 0, billable: 0, non_billable: 0 },
  financial: { revenue: 0, cost: 0, profit: 0, margin: 0 },
  productivity: 0,
  period: { year: null, month: null },
  reconciliation: { expected_salary_cost: 0, calculated_company_cost: 0, difference: 0, passed: true },
}

const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function StatCard({ label, value, helper, tone }) {
  return (
    <div className={`stat-card ${tone}`}>
      <div className="stat-copy">
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{helper}</small>
      </div>
    </div>
  )
}

function PanelLoading({ label }) {
  return (
    <div className="panel-inline-loading" role="status" aria-live="polite">
      <span className="inline-loading-icon" aria-hidden="true" />
      <strong>{label}</strong>
    </div>
  )
}

function statusKey(status) {
  if (status === 'loss' || status === 'loss-making') {
    return 'loss'
  }

  if (status === 'profitable') {
    return 'profitable'
  }

  return 'unpriced'
}

function statusLabel(status) {
  const key = statusKey(status)
  return key === 'loss' ? 'Loss' : key.charAt(0).toUpperCase() + key.slice(1)
}

function statusClass(status) {
  const key = statusKey(status)
  return key === 'profitable' ? 'green' : key === 'loss' ? 'red' : 'gray'
}

function buildDonutBackground(items) {
  const total = items.reduce((sum, item) => sum + item.value, 0)

  if (!total) {
    return '#e6edf4'
  }

  let cursor = 0
  const segments = items.map((item) => {
    const start = cursor
    const end = cursor + (item.value / total) * 360
    cursor = end
    return `${item.color} ${start}deg ${end}deg`
  })

  return `conic-gradient(${segments.join(', ')})`
}

function ProjectHealthDonut({ items, total, projects }) {
  const [activeStatus, setActiveStatus] = useState(items[0]?.key || '')
  const activeItem = items.find((item) => item.key === activeStatus) || items[0]
  const visibleProjects = projects.filter((project) => statusKey(project.status) === activeItem?.key).slice(0, 6)
  const donutSegments = useMemo(() => {
    const itemTotal = items.reduce((sum, item) => sum + item.value, 0)
    let cursor = 0

    return items.map((item) => {
      const start = cursor
      const end = cursor + (item.value / itemTotal) * 360
      cursor = end
      return { key: item.key, start, end }
    })
  }, [items])

  function handleDonutPointerMove(event) {
    const rect = event.currentTarget.getBoundingClientRect()
    const x = event.clientX - rect.left - rect.width / 2
    const y = event.clientY - rect.top - rect.height / 2
    const angle = (Math.atan2(y, x) * 180 / Math.PI + 90 + 360) % 360
    const segment = donutSegments.find((item) => angle >= item.start && angle < item.end)

    if (segment) {
      setActiveStatus(segment.key)
    }
  }

  return (
    <div className="donut-3d-layout">
      <div
        className="donut-3d"
        style={{
          '--donut-bg': buildDonutBackground(items),
          '--active-donut-color': activeItem?.color || '#79d8ae',
        }}
        onMouseEnter={() => setActiveStatus(activeItem?.key || '')}
        onMouseMove={handleDonutPointerMove}
        aria-label={`${activeItem?.name || 'Project'} projects selected`}
        role="img"
      >
        <div className="donut-3d-center">
          <strong>{total}</strong>
          <span>Projects</span>
        </div>
      </div>

      <ul className="donut-3d-legend">
        {items.map((item) => (
          <li
            key={item.name}
            className={item.key === activeItem?.key ? 'active' : ''}
            onMouseEnter={() => setActiveStatus(item.key)}
            onFocus={() => setActiveStatus(item.key)}
            tabIndex={0}
          >
            <span className="legend-swatch" style={{ background: item.color }} />
            <span>{item.name}</span>
            <strong>{item.value}</strong>
          </li>
        ))}
      </ul>

      <div className="donut-project-list">
        <h3>{activeItem?.name || 'Projects'}</h3>
        {visibleProjects.length ? (
          <ul>
            {visibleProjects.map((project) => (
              <li key={project.ref_code}>
                <span>{project.project_name || project.ref_code}</span>
                <strong>{project.margin == null ? '-' : formatPercentage(project.margin)}</strong>
              </li>
            ))}
          </ul>
        ) : (
          <p>No projects in this group.</p>
        )}
      </div>
    </div>
  )
}

function formatCompactCurrency(value) {
  const amount = Number(value || 0)
  const compact = new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(Math.abs(amount))

  return `${amount < 0 ? '-' : ''}AED ${compact}`
}

function DepartmentAnalyticsSection({ analytics, loading }) {
  const departments = analytics.departments || []
  const maxEmployees = Math.max(...departments.map((item) => Number(item.employee_count || 0)), 1)
  const maxAverageSalary = Math.max(...departments.map((item) => Number(item.average_salary || 0)), 1)
  const maxFinance = Math.max(
    ...departments.flatMap((item) => [Math.abs(Number(item.total_salary || 0)), Math.abs(Number(item.profit || 0))]),
    1,
  )

  return (
    <div className="panel department-analytics-panel">
      <div className="panel-header">
        <div>
          <h2>Department salary and profit analysis</h2>
          <p className="panel-note">Salary distribution, people mix, and allocated profit by department.</p>
        </div>
      </div>

      {loading && !departments.length ? (
        <PanelLoading label="Loading department analytics..." />
      ) : departments.length ? (
        <div className="department-analytics-grid">
          <section className="mini-chart-card employee-count-chart">
            <h3>Employees per department</h3>
            <div className="employee-horizontal-chart">
              {departments.map((item, index) => (
                <div className="employee-horizontal-row" key={item.department}>
                  <span title={item.department}>{item.department}</span>
                  <div><i style={{ width: `${Math.max(7, Number(item.employee_count || 0) / maxEmployees * 100)}%`, '--bar-color': `var(--analytics-${index % 6})` }} /></div>
                  <strong>{item.employee_count}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="mini-chart-card">
            <h3>Average salary by department</h3>
            <div className="analytics-bar-list">
              {departments.map((item, index) => (
                <div className="analytics-bar-row" key={item.department}>
                  <span title={item.department}>{item.department}</span>
                  <div><i style={{ width: `${Math.max(4, Number(item.average_salary || 0) / maxAverageSalary * 100)}%`, '--bar-color': `var(--analytics-${index % 6})` }} /></div>
                  <strong>{formatCompactCurrency(item.average_salary)}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="mini-chart-card">
            <h3>Salary and profit by department</h3>
            <div className="department-profit-list">
              {departments.map((item, index) => (
                <div className="department-profit-row" key={item.department}>
                  <div className="department-profit-label">
                    <span title={item.department}>{item.department}</span>
                    <strong className={Number(item.profit || 0) >= 0 ? 'positive' : 'negative'}>{formatCompactCurrency(item.profit)}</strong>
                  </div>
                  <div className="dual-bar">
                    <i className="salary" style={{ width: `${Math.max(4, Math.abs(Number(item.total_salary || 0)) / maxFinance * 100)}%`, '--bar-color': `var(--analytics-${index % 6})` }} />
                    <i className={Number(item.profit || 0) >= 0 ? 'profit' : 'loss'} style={{ width: `${Math.max(4, Math.abs(Number(item.profit || 0)) / maxFinance * 100)}%` }} />
                  </div>
                  <div className="department-profit-meta">
                    <span>Salary {formatCompactCurrency(item.total_salary)}</span>
                    <span>{formatPercentage(item.margin)} margin</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      ) : (
        <div className="empty-state compact"><h3>No department analytics for this period.</h3></div>
      )}
    </div>
  )
}

export default function OverviewPage({ datasetId, year, month }) {
  const [dashboard, setDashboard] = useState(EMPTY_DASHBOARD)
  const [projects, setProjects] = useState([])
  const [trendData, setTrendData] = useState([])
  const [departmentAnalytics, setDepartmentAnalytics] = useState({ departments: [], salary_ranges: [] })
  const [profitabilityTab, setProfitabilityTab] = useState('profit')
  const [loading, setLoading] = useState(true)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function load() {
      setLoading(true)
      setAnalyticsLoading(false)
      setError('')
      setProjects([])
      setTrendData([])
      setDepartmentAnalytics({ departments: [], salary_ranges: [] })

      try {
        const dashboardData = await getDashboard({ dataset_id: datasetId, year, month })
        if (!active) {
          return
        }
        setDashboard(dashboardData)
        setLoading(false)
        setAnalyticsLoading(true)

        try {
          const [projectsData, departmentData, trendResponse] = await Promise.all([
            getProjects({ dataset_id: datasetId, year, month, page_size: 100 }),
            getDepartmentAnalytics({ dataset_id: datasetId, year, month }),
            getDashboardTrend({ dataset_id: datasetId, year, month }),
          ])

          if (!active) {
            return
          }
          setProjects(projectsData.items || [])
          setDepartmentAnalytics(departmentData)
          setTrendData((trendResponse.items || []).map((item) => ({
            name: monthLabels[item.month - 1],
            revenue: item.revenue,
            cost: item.cost,
            profit: item.profit,
          })))
        } catch (analyticsError) {
          console.error('Unable to load dashboard analytics.', analyticsError)
        }
      } catch (err) {
        if (active) {
          setError('Unable to load this data.')
        }
      } finally {
        if (active) {
          setLoading(false)
          setAnalyticsLoading(false)
        }
      }
    }

    if (datasetId) {
      load()
    } else {
      setLoading(false)
    }

    return () => {
      active = false
    }
  }, [datasetId, year, month])

  const projectCounts = useMemo(() => projects.reduce(
    (counts, project) => {
      counts[statusKey(project.status)] += 1
      return counts
    },
    { profitable: 0, loss: 0, unpriced: 0 },
  ), [projects])

  const pieData = useMemo(() => [
    { key: 'profitable', name: 'Profitable', value: projectCounts.profitable, color: '#79d8ae' },
    { key: 'loss', name: 'Loss', value: projectCounts.loss, color: '#ff9f9b' },
    { key: 'unpriced', name: 'Unpriced', value: projectCounts.unpriced, color: '#b9c7ff' },
  ].filter((item) => item.value > 0), [projectCounts])

  const projectPreview = useMemo(() => {
    const targetStatus = profitabilityTab === 'profit' ? 'profitable' : 'loss'
    const filtered = projects.filter((project) => statusKey(project.status) === targetStatus)

    return [...filtered]
      .sort((a, b) => (
        profitabilityTab === 'profit'
          ? Number(b.profit ?? 0) - Number(a.profit ?? 0)
          : Number(a.profit ?? 0) - Number(b.profit ?? 0)
      ))
      .slice(0, 5)
  }, [projects, profitabilityTab])

  const projectTotal = projects.length

  if (!datasetId) {
    return <div className="empty-state"><h3>No dataset selected.</h3></div>
  }

  if (loading) {
    return <LoadingPanel label="Loading dashboard..." />
  }

  if (error) {
    return (
      <div className="empty-state error-state">
        <h3>{error}</h3>
        <button onClick={() => window.location.reload()} className="primary-btn">Retry</button>
      </div>
    )
  }

  return (
    <div className="page-stack">
      <div className="stats-grid">
        <StatCard
          label="Revenue"
          value={formatCurrency(dashboard.financial.revenue)}
          helper="Total booked revenue"
          tone="green"
        />
        <StatCard
          label="Cost"
          value={formatCurrency(dashboard.financial.cost)}
          helper="Operating cost"
          tone="red"
        />
        <StatCard
          label="Profit"
          value={formatCurrency(dashboard.financial.profit)}
          helper="Net contribution"
          tone="blue"
        />
        <StatCard
          label="Margin"
          value={formatPercentage(dashboard.financial.margin)}
          helper="Profitability ratio"
          tone="purple"
        />
        <StatCard
          label="Total Hours"
          value={formatHours(dashboard.hours.total)}
          helper="All hours logged"
          tone="gray"
        />
        <StatCard
          label="Billable Hours"
          value={formatHours(dashboard.hours.billable)}
          helper="Chargeable time"
          tone="amber"
        />
      </div>

      <div className="card-grid two-up">
        <div className="panel chart-panel progress-panel profitability-trend-panel">
          <div className="panel-header">
            <h2>Profitability trend</h2>
          </div>
          <div className="chart-wrap large chart-stage progress-graph-3d">
            {analyticsLoading && !trendData.length ? (
              <PanelLoading label="Loading trend..." />
            ) : (
              <ResponsiveContainer width="100%" height={242}>
                <LineChart data={trendData} margin={{ top: 24, right: 24, bottom: 4, left: 18 }}>
                  <CartesianGrid strokeDasharray="3 6" vertical={false} />
                  <XAxis dataKey="name" />
                  <YAxis width={72} tickFormatter={(value) => `AED ${(value / 1000).toFixed(0)}k`} />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Line type="linear" dataKey="revenue" stroke="#31b982" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} animationDuration={950} />
                  <Line type="linear" dataKey="profit" stroke="#5f8ff5" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} animationDuration={1150} />
                  <Line type="linear" dataKey="cost" stroke="#f17f7d" strokeWidth={2.8} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} animationDuration={1050} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="panel chart-panel donut-panel">
          <div className="panel-header">
            <h2>Project health</h2>
          </div>
          <div className="chart-wrap donut-stage">
            {analyticsLoading && !projects.length ? (
              <PanelLoading label="Loading project health..." />
            ) : pieData.length ? (
              <ProjectHealthDonut items={pieData} total={projectTotal} projects={projects} />
            ) : (
              <div className="empty-state compact"><h3>No project status data.</h3></div>
            )}
          </div>
        </div>
      </div>

      <div className="card-grid dashboard-table-grid">
        <div className={`panel table-panel profitability-section ${profitabilityTab}`}>
          <div className="panel-header">
            <div className="section-title-with-tabs">
              <h2>Project profitability</h2>
              <div className="segmented-tabs" aria-label="Project profitability type">
                <button
                  className={profitabilityTab === 'profit' ? 'active' : ''}
                  type="button"
                  onClick={() => setProfitabilityTab('profit')}
                >
                  Profit
                </button>
                <button
                  className={profitabilityTab === 'loss' ? 'active' : ''}
                  type="button"
                  onClick={() => setProfitabilityTab('loss')}
                >
                  Loss
                </button>
              </div>
            </div>
            <div className="table-actions">
              <button
                className="export-btn"
                type="button"
                onClick={() => exportToCsv(`top-${profitabilityTab}-projects.csv`, [
                  { label: 'Project', value: (project) => project.project_name || project.ref_code },
                  { label: 'Revenue', value: (project) => project.revenue ?? '' },
                  { label: 'Cost', value: (project) => project.cost ?? '' },
                  { label: 'Profit', value: (project) => project.profit ?? '' },
                  { label: 'Margin', value: (project) => project.margin ?? '' },
                  { label: 'Hours', value: (project) => project.hours ?? '' },
                  { label: 'Status', value: (project) => project.status || '' },
                ], projectPreview)}
              >
                Export CSV
              </button>
              <Link to="/dashboard/projects" className="link-btn">View all projects</Link>
            </div>
          </div>

          {analyticsLoading && !projects.length ? (
            <PanelLoading label="Loading project profitability..." />
          ) : projectPreview.length ? (
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Project</th>
                    <th>Revenue</th>
                    <th>Cost</th>
                    <th>Profit</th>
                    <th>Margin</th>
                    <th>Hours</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {projectPreview.map((project) => (
                    <tr key={project.ref_code}>
                      <td>
                        <Link to={`/dashboard/projects/${project.ref_code}`}>{project.project_name || project.ref_code}</Link>
                      </td>
                      <td>{project.revenue === null ? '-' : formatCurrency(project.revenue)}</td>
                      <td>{project.cost === null ? '-' : formatCurrency(project.cost)}</td>
                      <td className={project.profit >= 0 ? 'positive' : 'negative'}>{project.profit === null ? '-' : formatCurrency(project.profit)}</td>
                      <td className={project.margin >= 0 ? 'positive' : 'negative'}>{project.margin === null ? '-' : formatPercentage(project.margin)}</td>
                      <td>{project.hours === null ? '-' : formatHours(project.hours)}</td>
                      <td><span className={`status-badge ${statusClass(project.status)}`}>{statusLabel(project.status)}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state compact"><h3>No {profitabilityTab === 'profit' ? 'profitable' : 'loss'} projects for this period.</h3></div>
          )}
        </div>

      </div>

      <DepartmentAnalyticsSection analytics={departmentAnalytics} loading={analyticsLoading} />
    </div>
  )
}
