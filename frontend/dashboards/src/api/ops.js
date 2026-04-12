/**
 * Ops API - read-only ops summary and alerts for demo/proof runs
 */
import { apiFetch } from "../lib/api";

async function getJson(path) {
  const response = await apiFetch(path);
  return response.json();
}

export async function fetchOpsSummary() {
  return getJson("/api/ops/summary/");
}

export async function fetchOpsAlerts() {
  return getJson("/api/ops/alerts/");
}
