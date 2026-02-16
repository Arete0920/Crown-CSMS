/**
 * Ops API - read-only ops summary and alerts for demo/proof runs
 */

export async function fetchOpsSummary() {
  const res = await fetch("/api/ops/summary/");
  if (!res.ok) throw new Error(`ops summary http ${res.status}`);
  return res.json();
}

export async function fetchOpsAlerts() {
  const res = await fetch("/api/ops/alerts/");
  if (!res.ok) throw new Error(`fetchOpsAlerts failed: ${res.status}`);
  return res.json();
}
