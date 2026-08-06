/**
 * Round a number to 2 decimal places, accounting for floating-point errors.
 * Uses the Number.EPSILON offset to avoid artifacts like 174.82999999999998.
 */
export function round2(n: number): number {
  return Math.round((n + Number.EPSILON) * 100) / 100;
}

/**
 * Format a number to 2 decimal places as a string.
 */
export function fmt2(n: number): string {
  return round2(n).toFixed(2);
}
