import { useState } from 'react'

const emptySummary = {
  dataset_id: null,
  employees_imported: 0,
  salary_records_imported: 0,
  projects_imported: 0,
  timesheet_rows_imported: 0,
  warnings: [],
  errors: [],
}

function formatFileSize(bytes) {
  if (!bytes) {
    return ''
  }

  const units = ['B', 'KB', 'MB', 'GB']
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1)
  const value = bytes / (1024 ** index)

  return `${value.toFixed(value >= 10 || index === 0 ? 0 : 1)} ${units[index]}`
}

function warningSummary(warnings = []) {
  const grouped = new Map()

  warnings.forEach((warning) => {
    grouped.set(warning, (grouped.get(warning) || 0) + 1)
  })

  return Array.from(grouped.entries()).slice(0, 6)
}

export default function ImportPage() {
  const [datasetName, setDatasetName] = useState('')
  const [files, setFiles] = useState({ timesheet: null, salary: null, project: null })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const warnings = warningSummary(result?.warnings)

  function updateFile(key, file) {
    setFiles((current) => ({ ...current, [key]: file }))
    setError('')
  }

  async function handleSubmit(event) {
    event.preventDefault()

    const missingFields = [
      !datasetName.trim() ? 'dataset name' : null,
      !files.timesheet ? 'timesheet file' : null,
      !files.salary ? 'salary file' : null,
      !files.project ? 'project price file' : null,
    ].filter(Boolean)

    if (missingFields.length) {
      setError(`Missing ${missingFields.join(', ')}.`)
      return
    }

    setLoading(true)
    setError('')

    const formData = new FormData()
    formData.append('dataset_name', datasetName.trim())
    formData.append('timesheet', files.timesheet)
    formData.append('salary', files.salary)
    formData.append('project', files.project)

    try {
      const response = await fetch('http://127.0.0.1:8000/api/import', {
        method: 'POST',
        body: formData,
      })

      const payload = await response.json()

      if (!response.ok) {
        throw new Error(payload.detail?.message || 'Unable to import dataset.')
      }

      setResult(payload)
      setDatasetName('')
      setFiles({ timesheet: null, salary: null, project: null })
    } catch (err) {
      setError(err.message || 'Unable to import this dataset.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-stack">
      <form className="panel import-form" onSubmit={handleSubmit}>
        <div className="panel-header">
          <h2>Import dataset</h2>
        </div>

        <label className="field">
          <span>Dataset name</span>
          <input
            value={datasetName}
            onChange={(e) => {
              setDatasetName(e.target.value)
              setError('')
            }}
            placeholder="e.g. 2025 Q2 data"
          />
        </label>

        <div className="upload-grid">
          {[
            ['timesheet', 'Timesheet file'],
            ['salary', 'Salary file'],
            ['project', 'Project price file'],
          ].map(([key, label]) => (
            <label key={key} className="file-field">
              <span>{label}</span>
              <input
                className="file-input"
                type="file"
                accept=".xlsx,.xls"
                onChange={(e) => updateFile(key, e.target.files[0])}
              />
              <span className="file-picker">Choose file</span>
              {files[key] ? (
                <small className="file-meta">
                  <strong>{files[key].name}</strong>
                  <span>{formatFileSize(files[key].size)}</span>
                </small>
              ) : (
                <small className="file-meta empty">No file selected</small>
              )}
            </label>
          ))}
        </div>

        {error ? <div className="inline-error">{error}</div> : null}

        <div className="form-actions">
          <button type="submit" className="primary-btn" disabled={loading}>
            {loading ? 'Importing...' : 'Upload dataset'}
          </button>
        </div>
      </form>

      {result ? (
        <div className="panel success-panel">
          <div className="panel-header">
            <h2>Dataset created</h2>
          </div>

          <div className="import-summary-grid">
            <div>
              <span>Employees</span>
              <strong>{result.employees_imported}</strong>
            </div>
            <div>
              <span>Salary records</span>
              <strong>{result.salary_records_imported}</strong>
            </div>
            <div>
              <span>Projects</span>
              <strong>{result.projects_imported}</strong>
            </div>
            <div>
              <span>Timesheet entries</span>
              <strong>{result.timesheet_rows_imported}</strong>
            </div>
          </div>

          {warnings.length ? (
            <div className="import-warning-summary">
              <div>
                <h3>{result.warnings.length} import warning{result.warnings.length > 1 ? 's' : ''}</h3>
              </div>
              <ul>
                {warnings.map(([warning, count]) => (
                  <li key={warning}>
                    <span>{warning}</span>
                    {count > 1 ? <strong>{count}</strong> : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
