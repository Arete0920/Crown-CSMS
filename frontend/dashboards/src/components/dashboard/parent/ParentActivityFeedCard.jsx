import ActivityFeedCard from '../ActivityFeedCard.jsx';

export default function ParentActivityFeedCard() {
  const items = [
    { title: 'Assignment posted - Grade 7 Bible', meta: 'Today' },
    { title: 'Attendance recorded - all students present', meta: 'Today' },
    { title: 'Message received from teacher', meta: 'Today' },
    { title: 'Tuition payment posted', meta: 'Yesterday' },
  ];

  return <ActivityFeedCard title="Recent Family Activity" items={items} />;
}
