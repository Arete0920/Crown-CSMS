export function compareValues(a, b, direction = 'asc') {
  const left = a ?? '';
  const right = b ?? '';

  if (typeof left === 'number' && typeof right === 'number') {
    return direction === 'asc' ? left - right : right - left;
  }

  const leftString = String(left).toLowerCase();
  const rightString = String(right).toLowerCase();

  if (leftString < rightString) return direction === 'asc' ? -1 : 1;
  if (leftString > rightString) return direction === 'asc' ? 1 : -1;
  return 0;
}

export function sortRows(rows, sortKey, sortDirection = 'asc') {
  if (!Array.isArray(rows) || !sortKey) return rows ?? [];

  return [...rows].sort((a, b) =>
    compareValues(a?.[sortKey], b?.[sortKey], sortDirection),
  );
}
