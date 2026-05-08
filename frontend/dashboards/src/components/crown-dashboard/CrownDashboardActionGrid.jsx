import CrownActionCard from '../launch/CrownActionCard.jsx';

export default function CrownDashboardActionGrid({ actions = [] }) {
  return (
    <>
      {actions.map((action, idx) => (
        <CrownActionCard
          key={action.title ?? `action-${idx}`}
          title={action.title}
          description={action.description}
          actionLabel={action.actionLabel}
          eyebrow={action.eyebrow || action.kicker || 'Quick Action'}
          href={action.href}
        />
      ))}
    </>
  );
}
