export function formatCurrency(value) {
  const numeric = Number(value ?? 0)
  return `AED ${numeric.toLocaleString('en-AE', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`
}

export function formatHours(value) {
  const numeric = Number(value ?? 0)
  return numeric.toLocaleString('en-AE', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  })
}

export function formatPercentage(value) {
  const numeric = Number(value ?? 0)
  return `${numeric.toLocaleString('en-AE', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`
}
