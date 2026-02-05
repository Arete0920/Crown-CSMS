/**
 * CSV Export Utilities
 * Shared helpers for building and downloading CSV files across all grids.
 */

/**
 * Escape a value for CSV: handle quotes and newlines per RFC 4180
 */
export const csvEscape = (v) => {
  if (v == null) return "";
  const s = String(v);
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
};

/**
 * Build a CSV string from rows and columns
 * @param {Array} rows - array of row objects
 * @param {Array} cols - array of column definitions: { key, title }
 * @param {Function} getCellValue - (row, col) => string | number
 * @returns {string} - CSV text with headers
 */
export const buildCsv = (rows, cols, getCellValue) => {
  const header = cols.map((c) => csvEscape(c.title)).join(",");
  const lines = [header];

  for (const row of rows || []) {
    const line = cols.map((col) => {
      const val = getCellValue(row, col);
      return csvEscape(val);
    }).join(",");
    lines.push(line);
  }

  return lines.join("\n");
};

/**
 * Download a text file (CSV, JSON, etc.) via blob + anchor
 * @param {string} filename - e.g. "gradebook_math101.csv"
 * @param {string} text - file contents
 */
export const downloadTextFile = (filename, text) => {
  const blob = new Blob([text], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};
