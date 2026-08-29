import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getEmployeeDetail, getProjectDetail } from '../api/api'
import LoadingPanel from '../components/layout/LoadingPanel'
import { exportToCsv } from '../utils/csv'
import { formatCurrency, formatHours, formatPercentage } from '../utils/formatters'

const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const salaryTones = ['mint', 'blue', 'violet', 'rose', 'amber', 'teal']

function salaryTone(month) {
  return salaryTones[(Number(month || 1) - 1) % salaryTones.length]
}

function statusClass(status) {
  return status === 'profitable' ? 'green' : status === 'loss' || status === 'loss-making' ? 'red' : 'gray'
}

export default function ProjectDetailPage({ datasetId, year, month }) {
  const { refCode } = useParams()
  const [project, setProject] = useState(null)
  const [selectedEmployee, setSelectedEmployee] = useState(null)
  const [employeeDetail, setEmployeeDetail] = useState(null)
  const [employeeLoading, setEmployeeLoading] = useState(false)
  const [employeeError, setEmployeeError] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      setLoading(true)
      setError('')

      try {
        const result = await getProjectDetail(refCode, { dataset_id: datasetId, year, month })
        setProject(result)
      } catch (err) {
        setError('Unable to load this data.')
      } finally {
        setLoading(false)
      }
    }

    if (refCode && datasetId) {
      load()
    } else {
      setLoading(false)
    }
  }, [refCode, datasetId, year, month])

  const employeeHours = useMemo(() => {
    const grouped = new Map()

    project?.employees?.forEach((employee) => {
      const current = grouped.get(employee.employee_no) || {
        employee_no: employee.employee_no,
        employee_name: employee.employee_name,
        hours: 0,
      }

      current.hours += Number(employee.hours || 0)
      grouped.set(employee.employee_no, current)
    })

    return Array.from(grouped.values()).sort((a, b) => b.hours - a.hours)
  }, [project])

  const maxEmployeeHours = employeeHours.reduce((max, employee) => Math.max(max, employee.hours), 0)

  const financialChartData = useMemo(() => {
    if (!project) {
      return []
    }

    const revenue = Number(project.project_price || 0)
    const cost = Number(project.total_project_cost || 0)
    const profit = Number(project.profit || 0)
    const maxValue = Math.max(Math.abs(revenue), Math.abs(cost), Math.abs(profit), 1)

    return [
      { name: 'Revenue', value: revenue, tone: 'revenue', width: Math.max(8, Math.abs(revenue) / maxValue * 100) },
      { name: 'Cost', value: cost, tone: 'cost', width: Math.max(8, Math.abs(cost) / maxValue * 100) },
      { name: 'Profit', value: profit, tone: profit >= 0 ? 'profit' : 'loss', width: Math.max(8, Math.abs(profit) / maxValue * 100) },
    ]
  }, [project])

  const maxMonthlySalary = useMemo(() => employeeDetail?.monthly_salaries?.reduce(
    (max, item) => Math.max(max, Number(item.salary || 0)),
    0,
  ) || 0, [employeeDetail])
  const selectedEmployeeProfitability = Number(selectedEmployee?.profitability || 0)
  const selectedEmployeeProfitabilityPercent = Math.max(0, Math.min(selectedEmployeeProfitability, 100))

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

    if (selectedEmployee?.employee_no && datasetId) {
      loadEmployee()
    }
  }, [selectedEmployee, datasetId, year, month])

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        setSelectedEmployee(null)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  if (!datasetId) {
    return <div className="empty-state"><h3>No dataset selected.</h3></div>
  }

  if (loading) {
    return <LoadingPanel label="Loading project details..." />
  }

  if (error) {
    return (
      <div className="empty-state error-state">
        <h3>{error}</h3>
        <button onClick={() => window.location.reload()} className="primary-btn">Retry</button>
      </div>
    )
  }

  if (!project) {
    return <div className="empty-state"><h3>Project not found.</h3></div>
  }

  return (
    <div className="page-stack">
      <div className="panel project-title-panel">
        <div className="project-header">
          <div>
            <p className="eyebrow">{project.ref_code}</p>
            <h2>{project.project_name || 'Untitled project'}</h2>
          </div>
          <span className={`status-badge ${statusClass(project.status)}`}>
            {project.status || 'Unpriced'}
          </span>
        </div>

        <div className="stats-grid three-col project-kpi-grid">
          <div className="stat-card green">
            <div className="stat-copy">
              <span>Project Price</span>
              <strong>{project.project_price == null ? 'Price unavailable' : formatCurrency(project.project_price)}</strong>
              <small>Sales value</small>
            </div>
          </div>
          <div className="stat-card red">
            <div className="stat-copy">
              <span>Total Cost</span>
              <strong>{formatCurrency(project.total_project_cost)}</strong>
              <small>Direct + indirect</small>
            </div>
          </div>
          <div className="stat-card blue">
            <div className="stat-copy">
              <span>Profit</span>
              <strong>{project.profit == null ? '-' : formatCurrency(project.profit)}</strong>
              <small>Net result</small>
            </div>
          </div>
          <div className="stat-card purple">
            <div className="stat-copy">
              <span>Margin</span>
              <strong>{project.margin == null ? '-' : formatPercentage(project.margin)}</strong>
              <small>Efficiency</small>
            </div>
          </div>
          <div className="stat-card gray">
            <div className="stat-copy">
              <span>Total Hours</span>
              <strong>{formatHours(project.total_project_hours)}</strong>
              <small>Logged time</small>
            </div>
          </div>
        </div>
      </div>

      <div className="card-grid two-up project-detail-grid">
        <div className="panel project-profit-panel">
          <div className="panel-header">
            <h2>Project profitability visual</h2>
          </div>
          <div className="profitability-visual">
            <div className="profit-bridge">
              {financialChartData.map((item) => (
                <div className={`profit-bridge-row ${item.tone}`} key={item.name}>
                  <div className="profit-bridge-label">
                    <span>{item.name}</span>
                    <strong>{formatCurrency(item.value)}</strong>
                  </div>
                  <div className="profit-bridge-track">
                    <i style={{ width: `${item.width}%` }} />
                  </div>
                </div>
              ))}
              <div className={`profit-result ${project.profit >= 0 ? 'profit' : 'loss'}`}>
                <span>{project.profit >= 0 ? 'Net gain' : 'Net loss'}</span>
                <strong>{project.profit == null ? '-' : formatCurrency(project.profit)}</strong>
                <small>{project.margin == null ? 'Margin unavailable' : `${formatPercentage(project.margin)} margin`}</small>
              </div>
            </div>
          </div>
        </div>
        <div className="panel employee-hours-panel">
          <div className="panel-header">
            <h2>Hours by employee</h2>
          </div>
          {employeeHours.length ? (
            <div className="progress-stack">
              {employeeHours.map((employee) => (
                <div key={employee.employee_no}>
                  <span>{employee.employee_name}</span>
                  <div className="progress">
                    <i style={{ width: `${maxEmployeeHours ? (employee.hours / maxEmployeeHours) * 100 : 0}%` }} />
                  </div>
                  <strong>{formatHours(employee.hours)}</strong>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state compact"><h3>No employee hours for this project.</h3></div>
          )}
        </div>
      </div>

      <div className="panel table-panel">
        <div className="panel-header">
          <h2>Employee contribution</h2>
          <button
            className="export-btn"
            type="button"
            onClick={() => exportToCsv(`${project.ref_code}-employee-contribution.csv`, [
              { label: 'Employee', value: (employee) => employee.employee_name },
              { label: 'Hours', value: (employee) => employee.hours },
              { label: 'Direct Rate', value: (employee) => employee.direct_rate ?? '' },
              { label: 'Indirect Rate', value: (employee) => employee.indirect_rate ?? '' },
              { label: 'Cost', value: (employee) => employee.cost },
              { label: 'Revenue Share', value: (employee) => employee.revenue_share ?? '' },
              { label: 'Profitability', value: (employee) => employee.profitability ?? '' },
            ], project.employees || [])}
          >
            Export CSV
          </button>
        </div>

        {project.employees?.length ? (
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Hours</th>
                  <th>Direct Rate</th>
                  <th>Indirect Rate</th>
                  <th>Cost</th>
                  <th>Revenue Share</th>
                  <th>Profitability</th>
                </tr>
              </thead>
              <tbody>
                {project.employees.map((employee, index) => (
                  <tr
                    key={`${employee.employee_no}-${index}`}
                    className="clickable-row"
                    onClick={() => setSelectedEmployee(employee)}
                  >
                    <td>{employee.employee_name}</td>
                    <td>{formatHours(employee.hours)}</td>
                    <td>{employee.direct_rate == null ? '-' : formatCurrency(employee.direct_rate)}</td>
                    <td>{employee.indirect_rate == null ? '-' : formatCurrency(employee.indirect_rate)}</td>
                    <td>{formatCurrency(employee.cost)}</td>
                    <td>{employee.revenue_share == null ? '-' : formatCurrency(employee.revenue_share)}</td>
                    <td className={employee.profitability >= 0 ? 'positive' : 'negative'}>{employee.profitability == null ? '-' : formatPercentage(employee.profitability)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state compact"><h3>No timesheet entries for this project.</h3></div>
        )}
      </div>

      {selectedEmployee ? (
        <div className="modal-backdrop" onClick={() => setSelectedEmployee(null)}>
          <section className="department-modal employee-detail-modal project-employee-modal" role="dialog" aria-modal="true" aria-labelledby="employee-detail-title" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span>Employee profile</span>
                <h2 id="employee-detail-title">{selectedEmployee.employee_name}</h2>
              </div>
              <button className="modal-close" type="button" onClick={() => setSelectedEmployee(null)} aria-label="Close employee detail">
                Close
              </button>
            </div>

            {employeeLoading ? (
              <div className="employee-detail-state">Loading employee details...</div>
            ) : employeeError ? (
              <div className="employee-detail-state error-state">{employeeError}</div>
            ) : employeeDetail ? (
              <>
                <div className="employee-profile-grid">
                  <div>
                    <span>Employee ID</span>
                    <strong>{employeeDetail.employee_no}</strong>
                  </div>
                  <div>
                    <span>Department</span>
                    <strong>{employeeDetail.department || 'Unassigned'}</strong>
                  </div>
                  <div className="designation-card">
                    <span>Designation</span>
                    <strong>{employeeDetail.designation || '-'}</strong>
                  </div>
                  <div>
                    <span>Total working hours</span>
                    <strong>{formatHours(employeeDetail.total_working_hours)}</strong>
                  </div>
                </div>

                <div className="productivity-employee-layout project-employee-layout">
                  <section className={`hours-donut-panel project-employee-summary ${selectedEmployeeProfitability < 0 ? 'loss' : 'profit'}`}>
                    <div
                      className="hours-donut"
                      style={{ '--billable': `${selectedEmployeeProfitabilityPercent}%` }}
                    >
                      <div>
                        <strong>{selectedEmployee.profitability == null ? '-' : formatPercentage(selectedEmployee.profitability)}</strong>
                        <span>Profitability</span>
                      </div>
                    </div>
                    <div className="hours-breakdown">
                      <div className="hours-total">
                        <span>Project hours</span>
                        <strong>{formatHours(selectedEmployee.hours)}</strong>
                      </div>
                      <div className="hours-legend project-cost">
                        <span>Employee cost</span>
                        <strong>{formatCurrency(selectedEmployee.cost)}</strong>
                      </div>
                      <div className="hours-legend project-revenue">
                        <span>Revenue share</span>
                        <strong>{selectedEmployee.revenue_share == null ? '-' : formatCurrency(selectedEmployee.revenue_share)}</strong>
                      </div>
                    </div>
                  </section>

                  <section className="salary-bars-panel">
                    <div className="panel-header">
                      <h3>Monthly salary distribution</h3>
                    </div>
                    {employeeDetail.monthly_salaries.length ? (
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
            ) : null}
          </section>
        </div>
      ) : null}
    </div>
  )
}
