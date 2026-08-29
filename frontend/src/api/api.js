const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

function buildQuery(params = {}) {
  const query = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      query.set(key, value)
    }
  })

  return query.toString()
}

async function fetchAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error(`API call failed: ${endpoint}`, error)
    throw error
  }
}

export async function getHealth() {
  return fetchAPI('/api/health')
}

export async function getDashboard(params = {}) {
  const query = buildQuery(params)
  return fetchAPI(`/api/dashboard${query ? `?${query}` : ''}`)
}

export async function getDashboardTrend(params = {}) {
  const query = buildQuery(params)
  return fetchAPI(`/api/dashboard/trend${query ? `?${query}` : ''}`)
}

export async function getDepartmentAnalytics(params = {}) {
  const query = buildQuery(params)
  return fetchAPI(`/api/dashboard/departments${query ? `?${query}` : ''}`)
}

export async function getProjects(params = {}) {
  const query = buildQuery(params)
  return fetchAPI(`/api/projects${query ? `?${query}` : ''}`)
}

export async function getProjectDetail(refCode, params = {}) {
  const query = buildQuery(params)
  return fetchAPI(`/api/projects/${refCode}${query ? `?${query}` : ''}`)
}

export async function getProductivity(params = {}) {
  const query = buildQuery(params)
  return fetchAPI(`/api/productivity${query ? `?${query}` : ''}`)
}

export async function getEmployeeDetail(employeeNo, params = {}) {
  const query = buildQuery(params)
  return fetchAPI(`/api/employees/${employeeNo}${query ? `?${query}` : ''}`)
}

export async function getCategories(params = {}) {
  const query = buildQuery(params)
  return fetchAPI(`/api/categories${query ? `?${query}` : ''}`)
}

export async function getCategoryMatrix(params = {}) {
  const query = buildQuery(params)
  return fetchAPI(`/api/categories/matrix${query ? `?${query}` : ''}`)
}

export async function getDataQuality(datasetId) {
  return fetchAPI(`/api/data-quality?dataset_id=${datasetId}`)
}

export async function getDatasets() {
  return fetchAPI('/api/datasets')
}

export async function getSettings(params = {}) {
  const query = buildQuery(params)
  return fetchAPI(`/api/settings${query ? `?${query}` : ''}`)
}

export async function updateSettings(payload) {
  return fetchAPI('/api/settings', {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}
