/**
 * Crown Chart Defaults (Recharts)
 *
 * Usage:
 *   import { chartDefaults } from "@/theme/chartConfig";
 *   <CartesianGrid stroke={chartDefaults.gridStroke} />
 *   <Line stroke={chartDefaults.stroke} dot={false} />
 */
export const chartDefaults = {
  stroke:      "#1B3A6F",
  strokeWidth: 2,
  gridStroke:  "#E5E7EB",
  tooltipStyle: {
    backgroundColor: "#fff",
    border:          "1px solid rgba(0,0,0,0.1)",
    borderRadius:    8,
    fontSize:        13,
  },
  colors: ["#1B3A6F", "#2E7D32", "#ED6C02", "#6B7280", "#D32F2F"],
};
