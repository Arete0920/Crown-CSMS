/**
 * Sticky Table Style Helpers
 * Shared z-index rules and helper functions for sticky table layouts.
 */

/**
 * Z-index layering for sticky table elements
 * Higher numbers are on top; layering prevents overlap bugs.
 */
export const Z = {
  BODY: 1,          // normal table cells
  LEFT: 3,          // sticky left column (body cells)
  HEADER: 10,       // sticky top row (header cells)
  CORNER: 11,       // sticky top-left corner (student column header)
  RIGHT_BODY: 3,    // sticky right column (body cells)
  RIGHT_HEADER: 12, // sticky top-right corner (totals header)
};

/**
 * Sticky top style helper
 * @param {number} top - CSS top value (should be 0 or HEADER_ROW_HEIGHT)
 * @param {number} z - z-index from Z constant
 * @returns {object} - partial style object (merge into existing styles)
 */
export const stickyTop = (top = 0, z = Z.HEADER) => ({
  position: "sticky",
  top,
  zIndex: z,
});

/**
 * Sticky left style helper
 * @param {number} left - CSS left value (should be 0)
 * @param {number} top - CSS top value (should be 0 or HEADER_ROW_HEIGHT)
 * @param {number} z - z-index from Z constant
 * @returns {object} - partial style object (merge into existing styles)
 */
export const stickyLeft = (left = 0, top = 0, z = Z.LEFT) => ({
  position: "sticky",
  left,
  top,
  zIndex: z,
});

/**
 * Sticky right style helper
 * @param {number} right - CSS right value (should be 0)
 * @param {number} top - CSS top value (should be 0 or HEADER_ROW_HEIGHT)
 * @param {number} z - z-index from Z constant
 * @returns {object} - partial style object (merge into existing styles)
 */
export const stickyRight = (right = 0, top = 0, z = Z.RIGHT_HEADER) => ({
  position: "sticky",
  right,
  top,
  zIndex: z,
});
