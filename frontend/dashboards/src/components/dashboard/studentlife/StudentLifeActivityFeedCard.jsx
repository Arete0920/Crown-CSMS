import ActivityFeedCard from '../ActivityFeedCard.jsx';

export default function StudentLifeActivityFeedCard() {
  const items = [
    { title: 'Care note added for student follow-up', meta: 'Today' },
    { title: 'Service roster updated', meta: 'Today' },
    { title: 'Chapel outline posted', meta: 'Yesterday' },
    { title: 'Mentoring conversation logged', meta: 'Yesterday' },
  ];

  return <ActivityFeedCard title="Recent Care Activity" items={items} />;
}
