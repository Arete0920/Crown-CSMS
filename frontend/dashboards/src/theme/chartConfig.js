/**
 * Crown Chart Defaults (Recharts)
 *
 * Usage:
 *   import { chartDefaults } from "@/theme/chartConfig";
 *   <CartesianGrid stroke={chartDefaults.gridStroke} />
 *   <Line stroke={chartDefaults.stroke} dot={false} />
 */
export const chartDefaults = {
  stroke:      "var(--crown-compat-color-cf2d163b11)",
  strokeWidth: 2,
  gridStroke:  "var(--crown-compat-color-bfd4f8ffca)",
  tooltipStyle: {
    backgroundColor: "var(--crown-compat-color-e08de71387)",
    border:          "1px solid var(--crown-compat-color-4f6d03b417)",
    borderRadius:    8,
    fontSize:        13,
  },
  colors: ["var(--crown-compat-color-cf2d163b11)", "var(--crown-compat-color-96f8d201a4)", "var(--crown-compat-color-819c87f4e0)", "var(--crown-compat-color-66341b70b3)", "var(--crown-compat-color-589c0cbec4)"],
};
