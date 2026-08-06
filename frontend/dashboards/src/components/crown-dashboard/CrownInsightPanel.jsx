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
              <CartesianGrid stroke="var(--crown-compat-color-3b313dfb66)" strokeDasharray="4 6" vertical={false} />
              <XAxis dataKey="month" stroke="var(--crown-compat-color-b5e2bc59ff)" tickLine={false} axisLine={false} />
              <YAxis stroke="var(--crown-compat-color-b5e2bc59ff)" tickLine={false} axisLine={false} width={40} />
              <Tooltip
                cursor={{ stroke: 'var(--crown-compat-color-928ee44540)', strokeWidth: 1, strokeDasharray: '2 4' }}
                contentStyle={{
                  borderRadius: 14,
                  border: '1px solid var(--crown-compat-color-b1925ae209)',
                  boxShadow: '0 14px 28px var(--crown-compat-color-9228ddcf62)',
                }}
              />
              <Line type="monotone" dataKey="value" stroke="var(--crown-compat-color-e7b00c296b)" strokeWidth={3} dot={{ r: 4, fill: 'var(--crown-compat-color-f2074b6cef)', stroke: 'var(--crown-compat-color-d139a66934)', strokeWidth: 2 }} activeDot={{ r: 5, fill: 'var(--crown-compat-color-f8e175950d)' }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </CrownCard>
  );
}
