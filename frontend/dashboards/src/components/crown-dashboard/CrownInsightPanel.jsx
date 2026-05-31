import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';
import CrownCard from '../launch/CrownCard.jsx';

export default function CrownInsightPanel({ kicker = 'Insight', title, chip, trend = [] }) {
  const isTestRuntime = import.meta.env.MODE === 'test';
  const hasTrendData = Array.isArray(trend) && trend.length > 0;

  return (
    <CrownCard className="launch-chart-card">
      <div className="launch-card-heading-row">
        <div>
          <div className="launch-section-kicker">{kicker}</div>
          <h3>{title}</h3>
        </div>
        {chip ? <div className="launch-chip">{chip}</div> : null}
      </div>
      <div className="launch-chart-wrap">
        {!hasTrendData ? (
          <div className="launch-chart-empty" role="status">Trend data will appear here when records are available.</div>
        ) : isTestRuntime ? (
          <div className="launch-chart-test-fallback" aria-hidden="true" />
        ) : (
          <ResponsiveContainer width="100%" height={240} minWidth={320} minHeight={220}>
            <LineChart data={trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid stroke="#E2E8F0" strokeDasharray="4 6" vertical={false} />
              <XAxis dataKey="month" stroke="#94A3B8" tickLine={false} axisLine={false} />
              <YAxis stroke="#94A3B8" tickLine={false} axisLine={false} width={40} />
              <Tooltip
                cursor={{ stroke: '#93C5FD', strokeWidth: 1, strokeDasharray: '2 4' }}
                contentStyle={{
                  borderRadius: 14,
                  border: '1px solid #DBEAFE',
                  boxShadow: '0 14px 28px rgba(37,99,235,0.12)',
                }}
              />
              <Line type="monotone" dataKey="value" stroke="#2563EB" strokeWidth={3} dot={{ r: 4, fill: '#FFFFFF', stroke: '#1D4ED8', strokeWidth: 2 }} activeDot={{ r: 5, fill: '#FBBF24' }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </CrownCard>
  );
}
