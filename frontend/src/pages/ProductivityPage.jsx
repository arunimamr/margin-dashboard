import { useEffect, useMemo, useState } from 'react'
import { getEmployeeDetail, getProductivity } from '../api/api'
import LoadingPanel from '../components/layout/LoadingPanel'
import { exportToCsv } from '../utils/csv'
import { formatCurrency, formatHours, formatPercentage } from '../utils/formatters'

const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const salaryTones = ['mint', 'blue', 'violet', 'rose', 'amber', 'teal']

function salaryTone(month) {
  return salaryTones[(Number(month || 1) - 1) % salaryTones.length]
}

export default function ProductivityPage({ datasetId, year, month }) {
  const [data, setData] = useState({ items: [], departments: [], company_productivity: 0 })
  const [selectedDepartment, setSelectedDepartment] = useState('')
  const [selectedEmployee, setSelectedEmployee] = useState(null)
  const [employeeDetail, setEmployeeDetail] = useState(null)
  const [employeeLoading, setEmployeeLoading] = useState(false)
  const [employeeError, setEmployeeError] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  function openEmployee(item) {
    setEmployeeDetail(null)
    setEmployeeError('')
    setEmployeeLoading(true)
    setSelectedEmployee(item)
  }

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError('')
      try {
        const result = await getProductivity({ dataset_id: datasetId, year, month })
        setData(result)
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

  const departments = useMemo(() => {
    if (data.departments?.length) {
      return data.departments
    }

    const grouped = new Map()

    data.items.forEach((item) => {
      const department = item.department || 'Unassigned'
      const current = grouped.get(department) || {
        name: department,
        people: 0,
        total_hours: 0,
        billable_hours: 0,
        cost: 0,
        employees: [],
      }

      current.people += 1
      current.total_hours += Number(item.total_hours || 0)
      current.billable_hours += Number(item.billable_hours || 0)
      current.cost += Number(item.cost || 0)
      current.employees.push(item)
      grouped.set(department, current)
    })

    return Array.from(grouped.values())
      .map((department) => ({
        ...department,
        employees: department.employees.sort((a, b) => Number(b.total_hours || 0) - Number(a.total_hours || 0)),
        productivity: department.total_hours ? department.billable_hours / department.total_hours * 100 : 0,
      }))
      .sort((a, b) => b.total_hours - a.total_hours)
  }, [data.departments, data.items])

  const activeDepartment = selectedDepartment
  const activeSummary = departments.find((department) => department.name === activeDepartment)
  const departmentEmployees = activeSummary?.employees || []
  const maxMonthlySalary = useMemo(() => employeeDetail?.monthly_salaries?.reduce(
    (max, item) => Math.max(max, Number(item.salary || 0)),
    0,
  ) || 0, [employeeDetail])
  const employeeTotalHours = Number(selectedEmployee?.total_hours || 0)
  const employeeBillableHours = Number(selectedEmployee?.billable_hours || 0)
  const employeeNonBillableHours = Number(selectedEmployee?.non_billable_hours || 0)
  const billablePercent = employeeTotalHours ? employeeBillableHours / employeeTotalHours * 100 : 0

  useEffect(() => {
    if (selectedDepartment && !departments.some((department) => department.name === selectedDepartment)) {
      setSelectedDepartment('')
    }
  }, [departments, selectedDepartment])

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        if (selectedEmployee) {
          setSelectedEmployee(null)
        } else {
          setSelectedDepartment('')
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [selectedEmployee])

  useEffect(() => {
    async function loadEmployee() {
      setEmployeeLoading(true)
      setEmployeeError('')
      setEmployeeDetail(null)
      try {
        const result = await getEmployeeDetail(selectedEmployee.employee_no, { dataset_id: datasetId, year, month })
        setEmployeeDetail(result)
      } catch (err) {
        setEmployeeError('Unable to load employee details.')
      } finally {
        setEmployeeLoading(false)
      }
    }

    if (selectedEmployee && datasetId) {
      loadEmployee()
    }
  }, [selectedEmployee, datasetId, year, month])

  if (!datasetId) {
    return <div className="empty-state"><h3>No dataset selected.</h3></div>
  }

  if (loading) {
    return <LoadingPanel label="Loading productivity..." />
  }

  if (error) {
    return (
      <div className="empty-state error-state">
        <h3>{error}</h3>
        <button onClick={() => window.location.reload()} className="primary-btn">Retry</button>
      </div>
    )
  }

  if (!data.items.length) {
    return <div className="empty-state"><h3>No productivity data for this period.</h3></div>
  }

  return (
    <div className="page-stack">
      <div className="productivity-top-grid">
        <div className="stat-card gray">
          <div className="stat-icon">H</div>
          <div className="stat-copy">
            <span>Total Hours</span>
            <strong>{formatHours(data.items.reduce((sum, item) => sum + Number(item.total_hours), 0))}</strong>
            <small>All logged hours</small>
          </div>
        </div>
        <div className="stat-card blue">
          <div className="stat-icon">B</div>
          <div className="stat-copy">
            <span>Billable Hours</span>
            <strong>{formatHours(data.items.reduce((sum, item) => sum + Number(item.billable_hours), 0))}</strong>
            <small>Chargeable time</small>
          </div>
        </div>
        <div className="stat-card green">
          <div className="stat-icon">P</div>
          <div className="stat-copy">
            <span>Productivity</span>
            <strong>{formatPercentage(data.company_productivity)}</strong>
            <small>Company average</small>
          </div>
        </div>

        <div className="department-drilldown-card">
          <label className="filter-field">
            <span className="department-select-label">
              <span className="department-select-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M4 20V8l8-4 8 4v12" />
                  <path d="M8 20v-6h8v6" />
                  <path d="M8 10h.01M12 10h.01M16 10h.01" />
                </svg>
              </span>
              Choose Department
            </span>
            <select value={selectedDepartment} onChange={(event) => setSelectedDepartment(event.target.value)}>
              <option value="">Department</option>
              {departments.map((department) => (
                <option key={department.name} value={department.name}>{department.name}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="panel table-panel">
        <div className="panel-header">
          <h2>Employee productivity</h2>
          <button
            className="export-btn"
            type="button"
            onClick={() => exportToCsv('employee-productivity.csv', [
              { label: 'Employee', value: (item) => item.employee_name },
              { label: 'Department', value: (item) => item.department || 'Unassigned' },
              { label: 'Total Hours', value: (item) => item.total_hours },
              { label: 'Billable Hours', value: (item) => item.billable_hours },
              { label: 'Non-Billable Hours', value: (item) => item.non_billable_hours },
              { label: 'Productivity', value: (item) => item.productivity },
            ], data.items)}
          >
            Export CSV
          </button>
        </div>

        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>Department</th>
                <th>Total Hours</th>
                <th>Billable Hours</th>
                <th>Non-Billable Hours</th>
                <th>Productivity</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item) => (
                <tr
                  key={item.employee_no}
                  className="clickable-row"
                  onClick={() => openEmployee(item)}
                >
                  <td>{item.employee_name}</td>
                  <td>{item.department || 'Unassigned'}</td>
                  <td>{formatHours(item.total_hours)}</td>
                  <td>{formatHours(item.billable_hours)}</td>
                  <td>{formatHours(item.non_billable_hours)}</td>
                  <td>
                    <div className="productivity-cell">
                      <span>{formatPercentage(item.productivity)}</span>
                      <div className="progress"><i style={{ width: `${Math.min(item.productivity, 100)}%` }} /></div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {activeSummary ? (
        <div className="modal-backdrop" onClick={() => setSelectedDepartment('')}>
          <section className="department-modal" role="dialog" aria-modal="true" aria-labelledby="department-modal-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span>Department drill-down</span>
                <h2 id="department-modal-title">{activeDepartment}</h2>
              </div>
              <div className="modal-actions">
                <button
                  className="export-btn"
                  type="button"
                  onClick={() => exportToCsv(`${activeDepartment.toLowerCase().replaceAll(' ', '-')}-department.csv`, [
                    { label: 'Employee', value: (item) => item.employee_name },
                    { label: 'Employee No', value: (item) => item.employee_no },
                    { label: 'Total Hours', value: (item) => item.total_hours },
                    { label: 'Billable Hours', value: (item) => item.billable_hours },
                    { label: 'Non-Billable Hours', value: (item) => item.non_billable_hours },
                    { label: 'Cost', value: (item) => item.cost },
                    { label: 'Productivity', value: (item) => item.productivity },
                  ], departmentEmployees)}
                >
                  Export CSV
                </button>
                <button className="modal-close" type="button" onClick={() => setSelectedDepartment('')} aria-label="Close department drill-down">
                  Close
                </button>
              </div>
            </div>

            <div className="department-detail-header">
              <div className="people">
                <span>People</span>
                <strong>{activeSummary.people}</strong>
              </div>
              <div className="hours">
                <span>Total hours</span>
                <strong>{formatHours(activeSummary.total_hours)}</strong>
              </div>
              <div className="cost">
                <span>Total cost</span>
                <strong>{formatCurrency(activeSummary.cost)}</strong>
              </div>
              <div className="productivity">
                <span>Productivity</span>
                <strong>{formatPercentage(activeSummary.productivity)}</strong>
              </div>
            </div>

            <div className="department-modal-table">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Employee</th>
                    <th>Employee No</th>
                    <th>Total Hours</th>
                    <th>Billable Hours</th>
                    <th>Non-Billable Hours</th>
                    <th>Cost</th>
                    <th>Productivity</th>
                  </tr>
                </thead>
                <tbody>
                  {departmentEmployees.map((item) => (
                    <tr
                      key={item.employee_no}
                      className="clickable-row department-employee-row"
                      onClick={() => openEmployee({ ...item, department: activeDepartment })}
                    >
                      <td>{item.employee_name}</td>
                      <td>{item.employee_no}</td>
                      <td>{formatHours(item.total_hours)}</td>
                      <td>{formatHours(item.billable_hours)}</td>
                      <td>{formatHours(item.non_billable_hours)}</td>
                      <td>{formatCurrency(item.cost)}</td>
                      <td>
                        <div className="productivity-cell">
                          <span>{formatPercentage(item.productivity)}</span>
                          <div className="progress"><i style={{ width: `${Math.min(item.productivity, 100)}%` }} /></div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      ) : null}

      {selectedEmployee ? (
        <div className="modal-backdrop" onClick={() => setSelectedEmployee(null)}>
          <section className="department-modal employee-detail-modal productivity-employee-modal" role="dialog" aria-modal="true" aria-labelledby="productivity-employee-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span>Employee productivity</span>
                <h2 id="productivity-employee-title">{selectedEmployee.employee_name}</h2>
              </div>
              <button className="modal-close" type="button" onClick={() => setSelectedEmployee(null)} aria-label="Close employee detail">
                Close
              </button>
            </div>

            {employeeLoading ? (
              <div className="employee-detail-state">Loading employee details...</div>
            ) : employeeError ? (
              <div className="employee-detail-state error-state">{employeeError}</div>
            ) : (
              <>
                <div className="employee-profile-grid productivity-profile-grid">
                  <div>
                    <span>Name</span>
                    <strong>{selectedEmployee.employee_name}</strong>
                  </div>
                  <div>
                    <span>Department</span>
                    <strong>{employeeDetail?.department || selectedEmployee.department || 'Unassigned'}</strong>
                  </div>
                  <div className="designation-card">
                    <span>Designation</span>
                    <strong>{employeeDetail?.designation || '-'}</strong>
                  </div>
                  <div>
                    <span>Productivity</span>
                    <strong>{formatPercentage(selectedEmployee.productivity)}</strong>
                  </div>
                </div>

                <div className="productivity-employee-layout">
                  <section className="hours-donut-panel">
                    <div
                      className="hours-donut"
                      style={{ '--billable': `${Math.max(0, Math.min(billablePercent, 100))}%` }}
                    >
                      <div>
                        <strong>{formatPercentage(selectedEmployee.productivity)}</strong>
                        <span>Productivity</span>
                      </div>
                    </div>
                    <div className="hours-breakdown">
                      <div className="hours-total">
                        <span>Total hours</span>
                        <strong>{formatHours(employeeTotalHours)}</strong>
                      </div>
                      <div className="hours-legend billable">
                        <span>Billable hours</span>
                        <strong>{formatHours(employeeBillableHours)}</strong>
                      </div>
                      <div className="hours-legend non-billable">
                        <span>Non billable hours</span>
                        <strong>{formatHours(employeeNonBillableHours)}</strong>
                      </div>
                    </div>
                  </section>

                  <section className="salary-bars-panel">
                    <div className="panel-header">
                      <h3>Monthly salary distribution</h3>
                    </div>
                    {employeeDetail?.monthly_salaries?.length ? (
                      <div className="salary-bar-list">
                        {employeeDetail.monthly_salaries.map((item) => (
                          <div className={`salary-bar-row ${salaryTone(item.month)}`} key={`${item.year}-${item.month}`}>
                            <span>{monthLabels[item.month - 1]} {item.year}</span>
                            <div className="salary-bar-track">
                              <i style={{ width: `${maxMonthlySalary ? (Number(item.salary || 0) / maxMonthlySalary) * 100 : 0}%` }}>
                                <b>{formatCurrency(item.salary)}</b>
                              </i>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="empty-state compact"><h3>No monthly salary data.</h3></div>
                    )}
                  </section>
                </div>
              </>
            )}
          </section>
        </div>
      ) : null}
    </div>
  )
}
