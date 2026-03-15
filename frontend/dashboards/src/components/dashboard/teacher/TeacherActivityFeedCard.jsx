import ActivityFeedCard from '../ActivityFeedCard.jsx';

export default function TeacherActivityFeedCard() {
  const items = [
    { title: 'Attendance submitted - Period 1', meta: '20 minutes ago' },
    { title: 'Assignment posted - Grade 7 Bible', meta: '1 hour ago' },
    { title: 'Parent message received', meta: 'Today' },
    { title: 'Quiz graded - Grade 9 English', meta: 'Today' },
  ];

  return <ActivityFeedCard title="Recent Class Activity" items={items} />;
}
