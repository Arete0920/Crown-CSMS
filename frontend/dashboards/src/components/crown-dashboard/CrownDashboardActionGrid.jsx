import CrownActionCard from '../launch/CrownActionCard.jsx';

export default function CrownDashboardActionGrid({ actions = [] }) {
  return (
    <>
      {actions.map((action, idx) => (
        <CrownActionCard
          key={action.title ?? `action-${idx}`}
          title={action.title || action.label}
          description={action.description}
          actionLabel={action.actionLabel || action.label || action.title}
          eyebrow={action.eyebrow || action.kicker || 'Quick Action'}
          href={action.href}
        />
      ))}
    </>
  );
}
