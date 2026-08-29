import { useEffect, useMemo, useState } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import Sidebar from './components/layout/Sidebar'
import { getDatasets } from './api/api'
import OverviewPage from './pages/OverviewPage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import ProductivityPage from './pages/ProductivityPage'
import CategoriesPage from './pages/CategoriesPage'
import ImportPage from './pages/ImportPage'
import SettingsPage from './pages/SettingsPage'

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

function inferDatasetYear(dataset) {
  const match = dataset?.name?.match(/\b(20\d{2})\b/)
  return match ? Number(match[1]) : null
}

export default function Dashboard() {
  const location = useLocation()
  const [datasets, setDatasets] = useState([])
  const [selectedDatasetId, setSelectedDatasetId] = useState('')
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [selectedMonth, setSelectedMonth] = useState('')

  const pageTitle = useMemo(() => {
    const path = location.pathname

    if (path.includes('/dashboard/projects/')) {
      return 'Project Detail'
    }
    if (path.endsWith('/dashboard/projects')) {
      return 'Projects'
    }
    if (path.endsWith('/dashboard/productivity')) {
      return 'Productivity'
    }
    if (path.endsWith('/dashboard/categories')) {
      return 'Categories'
    }
    if (path.endsWith('/dashboard/import')) {
      return 'Import Data'
    }
    if (path.endsWith('/dashboard/settings')) {
      return 'Settings'
    }

    return 'Overview'
  }, [location.pathname])

  const availableYears = useMemo(() => {
    const datasetYears = datasets.map(inferDatasetYear).filter(Boolean)
    return [...new Set([...datasetYears, ...years])].sort((a, b) => b - a)
  }, [datasets])

  useEffect(() => {
    async function loadDatasets() {
      try {
        const response = await getDatasets()
        const items = response.items || []
        setDatasets(items)

        if (items.length && !selectedDatasetId) {
          const firstDataset = items[0]
          setSelectedDatasetId(firstDataset.id)
          setSelectedYear(inferDatasetYear(firstDataset) || new Date().getFullYear())
        }
      } catch (error) {
        console.error('Unable to load datasets', error)
      }
    }

    loadDatasets()
  }, [selectedDatasetId])

  const monthValue = selectedMonth === '' ? null : Number(selectedMonth)

  function handleDatasetChange(value) {
    const nextDatasetId = Number(value)
    const nextDataset = datasets.find((dataset) => dataset.id === nextDatasetId)
    setSelectedDatasetId(nextDatasetId)
    setSelectedYear(inferDatasetYear(nextDataset) || new Date().getFullYear())
  }

  return (
    <div className="dashboard-shell">
      <Sidebar />

      <main className="main-panel">
        <header className="topbar">
          <div>
            <h1>{pageTitle}</h1>
            <p>Track project financials, effort, and profitability in real time.</p>
          </div>

          <div className="topbar-actions">
            <label className="filter-field">
              <span>Dataset</span>
              <select value={selectedDatasetId} onChange={(e) => handleDatasetChange(e.target.value)}>
                {datasets.length === 0 ? <option value="">No dataset</option> : null}
                {datasets.map((dataset) => (
                  <option key={dataset.id} value={dataset.id}>{dataset.name}</option>
                ))}
              </select>
            </label>

            <label className="filter-field">
              <span>Year</span>
              <select value={selectedYear} onChange={(e) => setSelectedYear(Number(e.target.value))}>
                {availableYears.map((year) => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </label>

            <label className="filter-field">
              <span>Month</span>
              <select value={selectedMonth} onChange={(e) => setSelectedMonth(e.target.value)}>
                {months.map((month) => (
                  <option key={month.value === '' ? 'all-months' : month.value} value={month.value}>{month.label}</option>
                ))}
              </select>
            </label>
          </div>
        </header>

        <Routes>
          <Route index element={<OverviewPage datasetId={selectedDatasetId || undefined} year={selectedYear} month={monthValue} />} />
          <Route path="projects" element={<ProjectsPage datasetId={selectedDatasetId || undefined} year={selectedYear} month={monthValue} />} />
          <Route path="projects/:refCode" element={<ProjectDetailPage datasetId={selectedDatasetId || undefined} year={selectedYear} month={monthValue} />} />
          <Route path="productivity" element={<ProductivityPage datasetId={selectedDatasetId || undefined} year={selectedYear} month={monthValue} />} />
          <Route path="categories" element={<CategoriesPage datasetId={selectedDatasetId || undefined} year={selectedYear} month={monthValue} />} />
          <Route path="import" element={<ImportPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>

        <footer className="dashboard-footer">
          <span>Copyright © {new Date().getFullYear()} Margin Dashboard. All rights reserved.</span>
        </footer>
      </main>
    </div>
  )
}
