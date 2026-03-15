import PrioritiesPanel from '../PrioritiesPanel.jsx';

export default function StudentLifePrioritiesPanel() {
  const priorities = [
    'Follow up on 4 mentoring needs',
    'Prepare Friday chapel content',
    'Review 6 care referrals',
    'Confirm service project rosters',
  ];

  return <PrioritiesPanel items={priorities} rightLabel="4 Open" showButton={false} />;
}
