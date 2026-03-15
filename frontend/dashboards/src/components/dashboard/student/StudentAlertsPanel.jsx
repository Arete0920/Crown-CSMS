import AlertsPanel from '../AlertsPanel.jsx';

export default function StudentAlertsPanel() {
  const alerts = [
    { label: 'Assignment Alert', detail: '2 assignments are not yet submitted', tone: 'amber' },
    { label: 'Upcoming Quiz', detail: 'History quiz tomorrow', tone: 'amber' },
    { label: 'Unread Message', detail: 'Teacher note needs review', tone: 'red' },
  ];

  return <AlertsPanel alerts={alerts} showButton={false} />;
}
