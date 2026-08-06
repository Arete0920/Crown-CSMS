/**
 * Wizard discovery API — Crown2026
 * Thin wrapper around the canonical apiFetch.
 */
import { apiFetch } from "../lib/api";

/**
 * Fetches the ordered list of registered wizards from the backend.
 * Returns { wizards: [{ key, slug, title, enabled }] }
 */
export async function fetchWizards() {
  return apiFetch("/api/v1/wizards/");
}
