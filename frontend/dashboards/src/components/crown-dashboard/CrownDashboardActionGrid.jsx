import CrownActionCard from '../launch/CrownActionCard.jsx';

export default function CrownDashboardActionGrid({ actions = [] }) {
  return actions.map((action) => (
    <CrownActionCard
      key={action.title}
      title={action.title}
      description={action.description}
      actionLabel={action.actionLabel}
    />
  ));
}
