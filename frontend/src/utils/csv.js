function csvValue(value) {
  if (value === null || value === undefined) {
    return ''
  }

  const text = String(value)
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text
}

export function exportToCsv(filename, columns, rows) {
  const header = columns.map((column) => csvValue(column.label)).join(',')
  const body = rows.map((row) => columns.map((column) => csvValue(column.value(row))).join(',')).join('\n')
  const csv = [header, body].filter(Boolean).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
