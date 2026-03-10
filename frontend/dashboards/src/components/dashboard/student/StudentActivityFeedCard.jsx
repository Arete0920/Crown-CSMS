import ActivityFeedCard from '../ActivityFeedCard.jsx';

export default function StudentActivityFeedCard() {
  const items = [
    { title: 'Assignment submitted - English', meta: '1 hour ago' },
    { title: 'Quiz grade posted - Bible', meta: 'Today' },
    { title: 'Teacher announcement added', meta: 'Today' },
    { title: 'Attendance recorded - Present', meta: 'Today' },
  ];

  return <ActivityFeedCard title="Recent Activity" items={items} />;
}
