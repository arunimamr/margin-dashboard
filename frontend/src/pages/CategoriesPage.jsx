import { useEffect, useMemo, useState } from 'react'
import { getCategories, getCategoryMatrix } from '../api/api'
import LoadingPanel from '../components/layout/LoadingPanel'
import { exportToCsv } from '../utils/csv'
import { formatHours, formatPercentage } from '../utils/formatters'

export default function CategoriesPage({ datasetId, year, month }) {
  const [items, setItems] = useState([])
  const [matrix, setMatrix] = useState({ columns: [], rows: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError('')
      try {
        const [response, matrixResponse] = await Promise.all([
          getCategories({ dataset_id: datasetId, year, month }),
          getCategoryMatrix({ dataset_id: datasetId, year, month }),
        ])
        setItems(response.items || [])
        setMatrix(matrixResponse || { columns: [], rows: [] })
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

  const sortedItems = useMemo(() => [...items].sort((a, b) => {
    if (a.billable !== b.billable) {
      return a.billable ? -1 : 1
    }

    return Number(b.percentage || 0) - Number(a.percentage || 0)
  }), [items])

  const maxMatrixHours = useMemo(() => matrix.rows.reduce((max, row) => (
    Math.max(max, ...matrix.columns.map((column) => Number(row.categories?.[column.category] || 0)))
  ), 0), [matrix])

  const matrixCsvRows = useMemo(() => matrix.rows.map((row) => ({
    ...row,
    ...matrix.columns.reduce((values, column) => ({
      ...values,
      [column.category]: row.categories?.[column.category] || 0,
    }), {}),
  })), [matrix])

  if (!datasetId) {
    return <div className="empty-state"><h3>No dataset selected.</h3></div>
  }

  if (loading) {
    return <LoadingPanel label="Loading category data..." />
  }

  if (error) {
    return (
      <div className="empty-state error-state">
        <h3>{error}</h3>
        <button onClick={() => window.location.reload()} className="primary-btn">Retry</button>
      </div>
    )
  }

  if (!items.length) {
    return <div className="empty-state"><h3>No category data for this period.</h3></div>
  }

  return (
    <div className="page-stack">
      <div className="panel table-panel">
        <div className="panel-header">
          <h2>Category summary</h2>
          <button
            className="export-btn"
            type="button"
            onClick={() => exportToCsv('category-summary.csv', [
              { label: 'Category', value: (item) => item.category },
              { label: 'Hours', value: (item) => item.hours },
              { label: 'Percentage', value: (item) => item.percentage },
              { label: 'Billable', value: (item) => (item.billable ? 'Billable' : 'Non-billable') },
            ], sortedItems)}
          >
            Export CSV
          </button>
        </div>

        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Hours</th>
                <th>Percentage</th>
                <th>Billable</th>
              </tr>
            </thead>
            <tbody>
              {sortedItems.map((item) => (
                <tr key={item.category}>
                  <td>{item.category}</td>
                  <td>{formatHours(item.hours)}</td>
                  <td>{formatPercentage(item.percentage)}</td>
                  <td>
                    <span className={`status-badge ${item.billable ? 'green' : 'gray'}`}>
                      {item.billable ? 'Billable' : 'Non-billable'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {matrix.rows.length ? (
        <div className="panel table-panel category-matrix-panel">
          <div className="panel-header">
            <div>
              <h2>Employee x category matrix</h2>
              <p className="panel-note">Hours by employee and category, matching the finance pivot view.</p>
            </div>
            <button
              className="export-btn"
              type="button"
              onClick={() => exportToCsv('employee-category-matrix.csv', [
                { label: 'Employee', value: (row) => row.employee_name },
                { label: 'Employee No', value: (row) => row.employee_no },
                { label: 'Department', value: (row) => row.department || 'Unassigned' },
                { label: 'Total Hours', value: (row) => row.total_hours },
                ...matrix.columns.map((column) => ({
                  label: column.category,
                  value: (row) => row[column.category] ?? 0,
                })),
              ], matrixCsvRows)}
            >
              Export CSV
            </button>
          </div>

          <div className="matrix-scroll">
            <table className="data-table category-matrix-table">
              <thead>
                <tr>
                  <th className="sticky-col employee-col">Employee</th>
                  <th>Department</th>
                  {matrix.columns.map((column) => (
                    <th key={column.category}>
                      <span>{column.category}</span>
                      <small className={column.billable ? 'billable' : 'non-billable'}>
                        {column.billable ? 'Billable' : 'Non-billable'}
                      </small>
                    </th>
                  ))}
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {matrix.rows.map((row) => (
                  <tr key={row.employee_no}>
                    <td className="sticky-col employee-col">
                      <strong>{row.employee_name}</strong>
                      <span>{row.employee_no}</span>
                    </td>
                    <td>{row.department || 'Unassigned'}</td>
                    {matrix.columns.map((column) => {
                      const hours = Number(row.categories?.[column.category] || 0)
                      const intensity = maxMatrixHours ? hours / maxMatrixHours : 0

                      return (
                        <td key={column.category} className="matrix-cell">
                          <span
                            style={{
                              '--cell-opacity': 0.08 + intensity * 0.52,
                              '--cell-scale': Math.max(0.08, intensity),
                            }}
                          >
                            {hours ? formatHours(hours) : '-'}
                          </span>
                        </td>
                      )
                    })}
                    <td className="matrix-total">{formatHours(row.total_hours)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  )
}
