import AlertsPanel from '../AlertsPanel.jsx';

export default function AttendanceAlertsPanel() {
  const alerts = [
    { label: 'Repeated Absence Watch', detail: '5 students have 3+ absences this month', tone: 'red' },
    { label: 'Unsubmitted Attendance', detail: '2 class sections still missing', tone: 'amber' },
    { label: 'Tardy Spike', detail: 'Morning tardies rose this week', tone: 'amber' },
  ];

  return (
    <AlertsPanel
      title="Attendance Alerts"
      alerts={alerts}
      rightLabel="3 Active"
      showButton={false}
    />
  );
}
