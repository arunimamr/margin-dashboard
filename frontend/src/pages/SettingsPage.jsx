import { useEffect, useState } from 'react'
import { getSettings, updateSettings } from '../api/api'
import LoadingPanel from '../components/layout/LoadingPanel'

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    dataset_id: null,
    year: new Date().getFullYear(),
    month: 1,
    overhead: 0,
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const response = await getSettings({ year: settings.year, month: settings.month })
        const items = response.items || []

        if (items.length) {
          setSettings((current) => ({
            ...current,
            dataset_id: current.dataset_id ?? items[0].dataset_id ?? null,
            year: items[0].year ?? current.year,
            month: items[0].month ?? current.month,
            overhead: items[0].overhead ?? 0,
          }))
        }
      } catch (err) {
        setError('Unable to load settings.')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')

    try {
      const payload = {
        dataset_id: settings.dataset_id,
        year: Number(settings.year),
        month: Number(settings.month),
        overhead: Number(settings.overhead),
      }

      const updated = await updateSettings(payload)
      setSettings((current) => ({ ...current, ...updated }))
      setSuccess('Settings updated successfully.')
    } catch (err) {
      setError('Unable to update settings.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <LoadingPanel label="Loading settings..." />
  }

  return (
    <div className="page-stack">
      <form className="panel settings-form" onSubmit={handleSave}>
        <div className="panel-header">
          <h2>Monthly overhead settings</h2>
        </div>

        <label className="field">
          <span>Year</span>
          <input
            type="number"
            value={settings.year || new Date().getFullYear()}
            onChange={(e) => setSettings({ ...settings, year: Number(e.target.value) })}
          />
        </label>

        <label className="field">
          <span>Month</span>
          <select value={settings.month || 1} onChange={(e) => setSettings({ ...settings, month: Number(e.target.value) })}>
            <option value={1}>Jan</option>
            <option value={2}>Feb</option>
            <option value={3}>Mar</option>
            <option value={4}>Apr</option>
            <option value={5}>May</option>
            <option value={6}>Jun</option>
            <option value={7}>Jul</option>
            <option value={8}>Aug</option>
            <option value={9}>Sep</option>
            <option value={10}>Oct</option>
            <option value={11}>Nov</option>
            <option value={12}>Dec</option>
          </select>
        </label>

        <label className="field">
          <span>Monthly overhead</span>
          <input
            type="number"
            step="0.01"
            value={settings.overhead || 0}
            onChange={(e) => setSettings({ ...settings, overhead: Number(e.target.value) })}
          />
        </label>

        {error ? <div className="inline-error">{error}</div> : null}
        {success ? <div className="inline-success">{success}</div> : null}

        <div className="form-actions">
          <button type="submit" className="primary-btn" disabled={saving}>
            {saving ? 'Saving...' : 'Save settings'}
          </button>
        </div>
      </form>
    </div>
  )
}
