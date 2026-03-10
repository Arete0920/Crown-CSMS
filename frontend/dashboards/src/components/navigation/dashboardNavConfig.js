import { getAccessibleDashboardSections } from '../../config/dashboardRegistry';
import { getCurrentUserRoles } from '../../auth/roleAdapter';

export function getDashboardNavSections() {
  const userRoles = getCurrentUserRoles();

  return getAccessibleDashboardSections(userRoles).map((section) => ({
    label: section.sectionLabel,
    children: section.items.map((item) => ({
      key: item.key,
      label: item.label,
      href: item.path,
      tier: item.tier,
    })),
  }));
}
