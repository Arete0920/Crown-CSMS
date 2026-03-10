import AlertsPanel from '../AlertsPanel.jsx';

export default function BoardAlertsPanel() {
  const alerts = [
    { label: 'Retention Watch', detail: 'Grade 9 retention is trending lower than target', tone: 'amber' },
    { label: 'Budget Watch', detail: 'Aid allocation nearing annual threshold', tone: 'amber' },
    { label: 'Collections Watch', detail: 'Aging balances remain above preferred range', tone: 'red' },
  ];

  return (
    <AlertsPanel
      title="Board Alerts"
      alerts={alerts}
      rightLabel="3 Active"
      showButton={false}
    />
  );
}
