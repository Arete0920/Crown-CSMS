import CrownCard from '../crown/CrownCard.jsx';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

function toChartRows(labels, datasets) {
  return labels.map((label, idx) => {
    const row = { label };
    datasets.forEach((set) => {
      row[set.label] = Array.isArray(set.data) ? set.data[idx] : null;
    });
    return row;
  });
}

export default function TrendChartCard({
  title,
  subtitle,
  labels = [],
  datasets = [],
  type = 'line',
}) {
  const rows = toChartRows(labels, datasets);

  return (
    <CrownCard title={title}>
      {subtitle ? (
        <div style={{ fontSize: 12, color: 'var(--crown-muted)', marginBottom: 12 }}>{subtitle}</div>
      ) : null}

      <div style={{ height: 280 }}>
        <ResponsiveContainer width="100%" height="100%" minHeight={220}>
          {type === 'bar' ? (
            <BarChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.08)" />
              <XAxis dataKey="label" tick={{ fill: 'var(--crown-muted)', fontSize: 11 }} />
              <YAxis tick={{ fill: 'var(--crown-muted)', fontSize: 11 }} />
              <Tooltip />
              <Legend />
              {datasets.map((set) => (
                <Bar
                  key={set.label}
                  dataKey={set.label}
                  fill={set.borderColor || 'var(--crown-brand)'}
                  radius={[6, 6, 0, 0]}
                />
              ))}
            </BarChart>
          ) : (
            <LineChart data={rows}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.08)" />
              <XAxis dataKey="label" tick={{ fill: 'var(--crown-muted)', fontSize: 11 }} />
              <YAxis tick={{ fill: 'var(--crown-muted)', fontSize: 11 }} />
              <Tooltip />
              <Legend />
              {datasets.map((set) => (
                <Line
                  key={set.label}
                  type="monotone"
                  dataKey={set.label}
                  stroke={set.borderColor || 'var(--crown-brand)'}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  activeDot={{ r: 5 }}
                />
              ))}
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </CrownCard>
  );
}
