/**
 * Pobiera blob jako plik — tworzy tymczasowy link i klika go.
 * Używany wszędzie gdzie pobieramy PDF/inne pliki z API.
 *
 * @param {ArrayBuffer|Blob} data - dane z axios responseType: 'blob'
 * @param {string} filename - nazwa pliku do pobrania
 * @param {string} [mimeType='application/pdf'] - typ MIME
 */
export function downloadBlob(data, filename, mimeType = 'application/pdf') {
  const url = URL.createObjectURL(new Blob([data], { type: mimeType }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

/**
 * Otwiera blob w nowej karcie (np. podgląd PDF).
 *
 * @param {ArrayBuffer|Blob} data
 * @param {string} [mimeType='application/pdf']
 */
export function openBlobInTab(data, mimeType = 'application/pdf') {
  const url = URL.createObjectURL(new Blob([data], { type: mimeType }))
  window.open(url, '_blank')
}
