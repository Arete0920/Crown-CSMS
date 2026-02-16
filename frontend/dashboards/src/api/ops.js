/**
 * Ops API - read-only ops summary for demo/proof runs
 */

export async function fetchOpsSummary() {
  const res = await fetch("/api/ops/summary/");
  if (!res.ok) throw new Error(`ops summary http ${res.status}`);
  return res.json();
}
