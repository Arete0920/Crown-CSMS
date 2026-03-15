import ActivityFeedCard from '../ActivityFeedCard.jsx';

export default function BoardActivityFeedCard() {
  const items = [
    { title: 'Board packet updated', meta: '1 hour ago' },
    { title: 'Monthly finance summary posted', meta: '2 hours ago' },
    { title: 'Enrollment report refreshed', meta: 'Today' },
    { title: 'Mission engagement summary published', meta: 'Today' },
  ];

  return <ActivityFeedCard title="Recent Leadership Activity" items={items} />;
}
