import AlertsPanel from '../AlertsPanel.jsx';

export default function ParentAlertsPanel() {
  const alerts = [
    { label: 'Missing Assignments', detail: 'One child has 3 missing submissions', tone: 'amber' },
    { label: 'Balance Reminder', detail: 'Current balance of $620 remains due', tone: 'amber' },
    { label: 'Event Form Needed', detail: 'Field trip permission form due tomorrow', tone: 'red' },
  ];

  return <AlertsPanel alerts={alerts} showButton={false} />;
}
