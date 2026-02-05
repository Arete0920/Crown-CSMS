/**
 * Grade Visualization Helpers
 * Shared utilities for computing and styling grades by percentage.
 */

/**
 * Safely compute percentage from earned/possible points
 * @param {object} cell - grade cell: { points_earned, points_possible }
 * @returns {number | null} - percentage (0–100) or null if invalid
 */
export const pctFromCell = (cell) => {
  const pts = Number(cell?.points_earned);
  const max = Number(cell?.points_possible);
  if (!Number.isFinite(pts) || !Number.isFinite(max) || max <= 0) return null;
  return (pts / max) * 100;
};

/**
 * Compute background color tint based on percentage
 * Follows accessibility best practices: muted, not loud
 * @param {number | null} pct - percentage (0–100) or null
 * @returns {string | undefined} - RGBA color string or undefined (no tint)
 */
export const bgForPct = (pct) => {
  if (pct == null) return undefined;
  if (pct >= 90) return "rgba(34, 197, 94, 0.10)";   // subtle green (passes)
  if (pct >= 70) return "rgba(234, 179, 8, 0.12)";   // subtle amber (monitor)
  return "rgba(239, 68, 68, 0.10)";                  // subtle red (at-risk)
};
