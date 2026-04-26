export default function CrownDashboardMetricGrid({ children, className = '' }) {
  const classes = ['launch-dashboard-grid', 'launch-dashboard-grid-metrics', className].filter(Boolean).join(' ');
  return <section className={classes}>{children}</section>;
}
