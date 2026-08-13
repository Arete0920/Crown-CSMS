/**
 * Wizard discovery API — CROWN
 * Thin wrapper around the canonical authenticated JSON transport.
 */
import { authenticatedJson } from "../utils/authClient";

/**
 * Fetches the ordered list of registered wizards from the backend.
 * Returns { wizards: [{ key, slug, title, enabled }] }
 */
export async function fetchWizards() {
  return authenticatedJson("/api/v1/wizards/");
}
