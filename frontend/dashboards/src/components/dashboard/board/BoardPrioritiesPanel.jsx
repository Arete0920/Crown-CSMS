import PrioritiesPanel from '../PrioritiesPanel.jsx';

export default function BoardPrioritiesPanel() {
  const priorities = [
    'Review latest enrollment trend report',
    'Prepare for next board meeting',
    'Review finance packet and aging summary',
    'Review mission and service participation update',
    'Confirm strategic initiatives for spring term',
  ];

  return (
    <PrioritiesPanel
      title="Board Priorities"
      items={priorities}
      rightLabel="Read Only"
      showButton={false}
    />
  );
}
