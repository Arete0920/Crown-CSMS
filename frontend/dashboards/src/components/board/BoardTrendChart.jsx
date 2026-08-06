import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { chartDefaults } from "../../theme/chartConfig";

function currency(n) {
  if (typeof n !== "number") return n;
  return n.toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}

export default function BoardTrendChart({
  data,
  yKey,
  xKey = "label",
  format = "number",
}) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data}>
        <CartesianGrid stroke={chartDefaults.gridStroke} />
        <XAxis dataKey={xKey} tickLine={false} axisLine={false} />
        <YAxis
          tickLine={false}
          axisLine={false}
          width={80}
          tickFormatter={(v) => (format === "currency" ? currency(v) : v)}
        />
        <Tooltip
          contentStyle={chartDefaults.tooltipStyle}
          formatter={(v) => (format === "currency" ? currency(v) : v)}
        />
        <Line
          type="monotone"
          dataKey={yKey}
          stroke={chartDefaults.stroke}
          strokeWidth={chartDefaults.strokeWidth}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
