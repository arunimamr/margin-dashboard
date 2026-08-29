import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getProjects } from '../api/api'
import LoadingPanel from '../components/layout/LoadingPanel'
import { exportToCsv } from '../utils/csv'
import { formatCurrency, formatHours, formatPercentage } from '../utils/formatters'

function statusClass(status) {
  return status === 'profitable' ? 'green' : status === 'loss' || status === 'loss-making' ? 'red' : 'gray'
}

function statusRank(status) {
  if (status === 'profitable') {
    return 0
  }
  if (status === 'loss' || status === 'loss-making') {
    return 1
  }
  return 2
}

function ProjectFinancialComparison({ projects }) {
  const maxValue = Math.max(
    ...projects.flatMap((project) => [
      Math.abs(project.revenue),
      Math.abs(project.cost),
      Math.abs(project.profit),
    ]),
    1,
  )

  return (
    <div className="project-financial-chart-scroll">
      <div className="project-financial-horizontal-chart">
        {projects.map((project, index) => {
          const isLoss = project.profit < 0
          const values = [
            { key: 'revenue', label: 'Revenue', value: project.revenue },
            { key: 'cost', label: 'Cost', value: project.cost },
            { key: isLoss ? 'loss' : 'profit', label: isLoss ? 'Loss' : 'Profit', value: project.profit },
          ]

          return (
            <div className="project-financial-row" key={project.ref_code} style={{ '--delay': `${index * 55}ms` }}>
              <div className="project-financial-label">
                <strong>{project.ref_code}</strong>
                <span title={project.project}>{project.project}</span>
              </div>
              <div className="project-financial-bars">
                {values.map((item) => (
                  <div
                    className={`project-financial-metric ${item.key}`}
                    key={item.label}
                    aria-label={`${project.ref_code} ${item.label} ${formatCurrency(item.value)}`}
                  >
                    <span className="project-financial-metric-label">{item.label}</span>
                    <div className="project-financial-track">
                      <i
                        className={`project-financial-bar ${item.key}`}
                        style={{ width: `${Math.max(4, Math.abs(item.value) / maxValue * 100)}%` }}
                      />
                    </div>
                    <strong className="project-financial-value">{formatCurrency(item.value)}</strong>
                  </div>
                ))}
              </div>
              <div className="project-financial-tooltip">
                <strong>{project.project}</strong>
                <em>{project.ref_code}</em>
                {values.map((item) => (
                  <div className={item.key} key={item.label}>
                    <span>{item.label}</span>
                    <b>{formatCurrency(item.value)}</b>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function ProjectsPage({ datasetId, year, month }) {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError('')

      try {
        const response = await getProjects({ dataset_id: datasetId, year, month })
        setProjects(response.items || [])
      } catch (err) {
        setError('Unable to load this data.')
      } finally {
        setLoading(false)
      }
    }

    if (datasetId) {
      load()
    } else {
      setLoading(false)
    }
  }, [datasetId, year, month])

  const sortedProjects = useMemo(() => [...projects].sort((a, b) => {
    const rankDifference = statusRank(a.status) - statusRank(b.status)

    if (rankDifference !== 0) {
      return rankDifference
    }

    return Number(b.margin ?? -Infinity) - Number(a.margin ?? -Infinity)
  }), [projects])

  const chartProjects = useMemo(() => sortedProjects.map((project) => ({
    ref_code: project.ref_code,
    project: project.project_name || project.ref_code,
    revenue: Number(project.revenue || 0),
    cost: Number(project.cost || 0),
    profit: Number(project.profit || 0),
  })), [sortedProjects])

  if (!datasetId) {
    return <div className="empty-state"><h3>No dataset selected.</h3></div>
  }

  if (loading) {
    return <LoadingPanel label="Loading projects..." />
  }

  if (error) {
    return (
      <div className="empty-state error-state">
        <h3>{error}</h3>
        <button onClick={() => window.location.reload()} className="primary-btn">Retry</button>
      </div>
    )
  }

  if (!projects.length) {
    return <div className="empty-state"><h3>No project data for this period.</h3></div>
  }

  return (
    <div className="page-stack">
      <div className="panel project-financial-panel">
        <div className="panel-header">
          <div>
            <h2>Project financial comparison</h2>
            <p className="panel-note">Revenue, cost, and profit by project.</p>
          </div>
          <div className="project-finance-legend">
            <span><i className="revenue" />Revenue</span>
            <span><i className="cost" />Cost</span>
            <span><i className="profit" />Profit</span>
            <span><i className="loss" />Loss</span>
          </div>
        </div>

        <ProjectFinancialComparison projects={chartProjects} />
      </div>

      <div className="panel table-panel">
        <div className="panel-header">
          <h2>Projects</h2>
          <button
            className="export-btn"
            type="button"
            onClick={() => exportToCsv('projects.csv', [
              { label: 'Ref Code', value: (project) => project.ref_code },
              { label: 'Project', value: (project) => project.project_name || '' },
              { label: 'Revenue', value: (project) => project.revenue ?? '' },
              { label: 'Cost', value: (project) => project.cost ?? '' },
              { label: 'Profit', value: (project) => project.profit ?? '' },
              { label: 'Margin', value: (project) => project.margin ?? '' },
              { label: 'Hours', value: (project) => project.hours ?? '' },
              { label: 'Status', value: (project) => project.status || '' },
            ], sortedProjects)}
          >
            Export CSV
          </button>
        </div>

        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Ref Code</th>
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
              {sortedProjects.map((project) => (
                <tr key={project.ref_code} className="clickable-row">
                  <td>
                    <Link to={`/dashboard/projects/${project.ref_code}`}>{project.ref_code}</Link>
                  </td>
                  <td>{project.project_name || '-'}</td>
                  <td>{project.revenue === null ? '-' : formatCurrency(project.revenue)}</td>
                  <td>{project.cost === null ? '-' : formatCurrency(project.cost)}</td>
                  <td className={project.profit >= 0 ? 'positive' : 'negative'}>{project.profit === null ? '-' : formatCurrency(project.profit)}</td>
                  <td className={project.margin >= 0 ? 'positive' : 'negative'}>{project.margin === null ? '-' : formatPercentage(project.margin)}</td>
                  <td>{project.hours === null ? '-' : formatHours(project.hours)}</td>
                  <td><span className={`status-badge ${statusClass(project.status)}`}>{project.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
