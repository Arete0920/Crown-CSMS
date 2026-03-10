import ActivityFeedCard from '../ActivityFeedCard.jsx';

export default function AttendanceActivityFeedCard() {
  const items = [
    { title: 'Grade 7 attendance submitted', meta: '10 minutes ago' },
    { title: 'Absence note received - Emily Carter', meta: '22 minutes ago' },
    { title: 'Tardy report refreshed', meta: 'Today' },
    { title: 'Attendance intervention flag created', meta: 'Today' },
  ];

  return <ActivityFeedCard title="Recent Attendance Activity" items={items} />;
}
