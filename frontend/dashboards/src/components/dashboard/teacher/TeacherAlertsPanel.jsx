import AlertsPanel from '../AlertsPanel.jsx';

export default function TeacherAlertsPanel() {
  const alerts = [
    { label: 'Missing Assignment Spike', detail: 'Grade 9 section B has 6 missing submissions', tone: 'amber' },
    { label: 'Attendance Missing', detail: 'One class attendance not yet submitted', tone: 'red' },
    { label: 'Parent Response Needed', detail: '3 messages are still unread', tone: 'amber' },
  ];

  return <AlertsPanel alerts={alerts} showButton={false} />;
}
