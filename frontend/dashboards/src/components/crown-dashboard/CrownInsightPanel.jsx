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
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid stroke="#E5E7EB" vertical={false} />
            <XAxis dataKey="month" stroke="#94A3B8" tickLine={false} axisLine={false} />
            <YAxis stroke="#94A3B8" tickLine={false} axisLine={false} width={40} />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#2563EB" strokeWidth={3} dot={{ r: 4, fill: '#FBBF24' }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </CrownCard>
  );
}
