import AlertsPanel from '../AlertsPanel.jsx';

export default function StudentLifeAlertsPanel() {
  const alerts = [
    { label: 'Care Follow-Up', detail: '4 students need pastoral check-in', tone: 'red' },
    { label: 'Service Compliance', detail: 'Several students remain behind target', tone: 'amber' },
    { label: 'Chapel Attendance Dip', detail: 'Grade 10 attendance dipped this week', tone: 'amber' },
  ];

  return (
    <AlertsPanel
      title="Student Care Alerts"
      alerts={alerts}
      showButton={false}
    />
  );
}
