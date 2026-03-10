import ActivityFeedCard from '../ActivityFeedCard.jsx';

export default function MasterControlActivityFeedCard() {
  const items = [
    { title: 'New school activated', meta: 'Today' },
    { title: 'Support dashboard refreshed', meta: 'Today' },
    { title: 'Revenue summary updated', meta: 'Yesterday' },
    { title: 'Implementation checkpoint logged', meta: 'Yesterday' },
  ];

  return <ActivityFeedCard title="Platform Activity" items={items} />;
}
