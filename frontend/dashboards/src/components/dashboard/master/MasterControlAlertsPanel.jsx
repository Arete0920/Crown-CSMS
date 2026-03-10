import AlertsPanel from '../AlertsPanel.jsx';

export default function MasterControlAlertsPanel() {
  const alerts = [
    { label: 'Implementation Risk', detail: 'One school is behind onboarding schedule', tone: 'amber' },
    { label: 'Support Queue Spike', detail: 'Billing-related tickets increased this week', tone: 'red' },
    { label: 'Adoption Lag', detail: 'Two schools show low module activity', tone: 'amber' },
  ];

  return (
    <AlertsPanel
      title="Platform Alerts"
      alerts={alerts}
      showButton={false}
    />
  );
}
